[CmdletBinding()]
param(
    [string]$RepoPath = (Join-Path $PSScriptRoot ".."),
    [string]$PythonPath,
    [string]$LogPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repo = (Resolve-Path -LiteralPath $RepoPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $repo ".git"))) {
    throw "RepoPath is not a Git checkout: $repo"
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
        $stashCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "stash", "push", "--include-untracked", "-m", "daily override preflight") -Label "git stash"
        if ($stashCode -ne 0) {
            throw "Could not preserve dirty runtime state in a stash."
        }
        Write-RunnerLog "Preserved dirty runtime state in a named stash."
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
    if ($ahead -eq 0 -and $behind -gt 0) {
        $syncCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "merge", "--ff-only", "origin/main") -Label "git fast-forward"
        if ($syncCode -ne 0) {
            throw "Fast-forward sync failed."
        }
    }
    elseif ($ahead -gt 0 -and $behind -gt 0) {
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
