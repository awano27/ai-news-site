[CmdletBinding()]
param(
    [string]$RepoPath = (Join-Path $PSScriptRoot ".."),
    [string]$PythonPath,
    [string]$LogPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repo = (Resolve-Path -LiteralPath $RepoPath).Path
$runtimeMarkerName = "visionhub-daily-news-override-runtime.json"
$gitDirectory = Join-Path $repo ".git"
if (-not (Test-Path -LiteralPath $gitDirectory -PathType Container)) {
    throw "RepoPath must be an installer-provisioned independent Git clone: $repo"
}
$runtimeMarker = Join-Path $gitDirectory $runtimeMarkerName
if (-not (Test-Path -LiteralPath $runtimeMarker -PathType Leaf)) {
    throw "Runtime marker is missing; run the installer for this checkout."
}
$markerData = Get-Content -LiteralPath $runtimeMarker -Raw | ConvertFrom-Json
$markerPath = [System.IO.Path]::GetFullPath([string]$markerData.checkoutPath)
if (-not [string]::Equals($markerPath, $repo, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Runtime marker checkout path does not match RepoPath."
}

if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    $repoPython = Join-Path $repo ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $repoPython -PathType Leaf) {
        $PythonPath = $repoPython
    }
    else {
        $PythonPath = (Get-Command python -ErrorAction Stop).Source
    }
}
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "PythonPath does not exist: $PythonPath"
}

if ([string]::IsNullOrWhiteSpace($LogPath)) {
    $LogPath = Join-Path $repo "logs\run_daily_override.log"
}
$logDirectory = Split-Path -Parent $LogPath
if ($logDirectory) {
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
}

function Write-RunnerLog {
    param([Parameter(Mandatory = $true)][string]$Message)
    $line = "{0:yyyy-MM-ddTHH:mm:ssK} {1}" -f (Get-Date), $Message
    Add-Content -LiteralPath $LogPath -Value $line -Encoding utf8
}

function Invoke-LoggedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $FilePath @Arguments 2>&1
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    foreach ($line in $output) {
        Write-RunnerLog "${Label}: $line"
    }
    return [int]$LASTEXITCODE
}

$mutex = $null
$mutexHeld = $false
$exitCode = 1
try {
    $mutex = [System.Threading.Mutex]::new($false, "Global\VisionHubDailyOverride")
    try {
        $mutexHeld = $mutex.WaitOne(0)
    }
    catch [System.Threading.AbandonedMutexException] {
        $mutexHeld = $true
        Write-RunnerLog "Recovered an abandoned daily override mutex."
    }
    if (-not $mutexHeld) {
        throw "Another daily override is already running."
    }

    Write-RunnerLog "START repo=$repo"
    $dirty = & git -C $repo status --porcelain=v1 --untracked-files=all
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed."
    }
    if ($dirty) {
        $stashMessage = "daily-override recovery {0:yyyyMMddTHHmmss}" -f (Get-Date)
        $previousStashId = "$(& git -C $repo for-each-ref "--format=%(objectname)" refs/stash)"
        $previousStashId = $previousStashId.Trim()
        $stashCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "stash", "push", "--include-untracked", "-m", $stashMessage) -Label "git stash"
        if ($stashCode -ne 0) {
            throw "Could not preserve dirty runtime state in a stash."
        }
        $stashId = "$(& git -C $repo for-each-ref "--format=%(objectname)" refs/stash)"
        $stashId = $stashId.Trim()
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($stashId) -or $stashId -eq $previousStashId) {
            throw "Dirty runtime state did not create a recoverable stash."
        }
        Write-RunnerLog "Preserved dirty runtime state: stash=$stashId message='$stashMessage'."
    }

    $fetchCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "fetch", "origin", "main") -Label "git fetch"
    if ($fetchCode -ne 0) {
        throw "git fetch origin main failed."
    }
    $counts = (& git -C $repo rev-list --left-right --count "HEAD...origin/main").Trim()
    if ($LASTEXITCODE -ne 0 -or $counts -notmatch "^(\d+)\s+(\d+)$") {
        throw "Could not determine ahead/behind state."
    }
    $ahead = [int]$Matches[1]
    $behind = [int]$Matches[2]
    Write-RunnerLog "Git state ahead=$ahead behind=$behind"
    if ($ahead -gt 0) {
        # A publish that failed to push leaves its override commit behind. Rebasing it
        # onto the cloud run conflicts on generated artifacts every morning, which used
        # to deadlock the runner before it ever collected X bookmarks. The pipeline
        # regenerates every one of those files below, so a stale override is disposable.
        $todaySubject = "chore(report): local override {0:yyyy-MM-dd}" -f (Get-Date)
        $localSubjects = @(& git -C $repo log "--format=%s" "origin/main..HEAD")
        if ($LASTEXITCODE -ne 0) {
            throw "Could not list local commits ahead of origin/main."
        }
        $stale = $localSubjects.Count -gt 0
        foreach ($subject in $localSubjects) {
            if ($subject -notmatch '^chore\(report\): local override \d{4}-\d{2}-\d{2}$' -or $subject -eq $todaySubject) {
                $stale = $false
            }
        }
        if ($stale) {
            Write-RunnerLog "Discarding stale override commit(s) the pipeline will regenerate: $($localSubjects -join '; ')"
            $resetCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "reset", "--hard", "origin/main") -Label "git reset"
            if ($resetCode -ne 0) {
                throw "Could not discard stale override commits."
            }
            $ahead = 0
            $behind = 0
        }
    }
    if ($ahead -eq 0 -and $behind -gt 0) {
        $syncCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "merge", "--ff-only", "origin/main") -Label "git fast-forward"
        if ($syncCode -ne 0) {
            throw "Fast-forward sync failed."
        }
    }
    elseif ($ahead -gt 0 -and $behind -gt 0) {
        # Deliberately no -X theirs here: anything still ahead at this point is not a
        # stale override (those were discarded above), so a conflict is a real one and
        # must stop the run rather than silently overwrite origin/main.
        $rebaseCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "rebase", "origin/main") -Label "git rebase"
        if ($rebaseCode -ne 0) {
            [void](Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "rebase", "--abort") -Label "git rebase abort")
            throw "Rebase conflict or failure; local commit and stash were retained."
        }
    }

    Set-Location -LiteralPath $repo
    $provider = "ollama"
    if ($env:NVIDIA_API_KEY -and $env:NVIDIA_API_KEY.StartsWith("nvapi-", [System.StringComparison]::OrdinalIgnoreCase)) {
        $provider = "nvidia"
    }
    Write-RunnerLog "Running pipeline with provider=$provider."
    $pipelineCode = Invoke-LoggedCommand -FilePath $PythonPath -Arguments @("-m", "src.auto_collect.main", "--provider", $provider, "--force") -Label "pipeline"
    if ($pipelineCode -ne 0) {
        throw "Daily report pipeline failed."
    }

    $reportDate = (Get-Date).ToString("yyyy-MM-dd")
    $message = "chore(report): local override $reportDate"
    $publisher = Join-Path $repo "scripts\publish_daily_report.py"
    $publishCode = Invoke-LoggedCommand -FilePath $PythonPath -Arguments @($publisher, "--repo", $repo, "--date", $reportDate, "--message", $message, "--push") -Label "publisher"
    if ($publishCode -ne 0) {
        throw "Reviewed publication CLI failed."
    }
    Write-RunnerLog "END success"
    $exitCode = 0
}
catch {
    Write-RunnerLog "FAILED: $($_.Exception.Message)"
}
finally {
    if ($mutexHeld -and $mutex) {
        $mutex.ReleaseMutex()
    }
    if ($mutex) {
        $mutex.Dispose()
    }
}
exit $exitCode
