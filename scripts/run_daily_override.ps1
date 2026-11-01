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

function Get-RescuePaths {
    # Only files that day's run alone produced: added by the commit, named with its
    # date, and still absent from origin/main (an operator may have restored some by hand).
    param(
        [Parameter(Mandatory = $true)][string]$Sha,
        [Parameter(Mandatory = $true)][string]$IsoDate
    )
    $dayInput = "input/day/{0}.txt" -f $IsoDate.Substring(5).Replace("-", "")
    $underscored = $IsoDate.Replace("-", "_")
    $added = @(& git -C $repo diff-tree --no-commit-id --name-only -r --diff-filter=A $Sha)
    if ($LASTEXITCODE -ne 0) {
        throw "Could not list files added by $Sha."
    }
    $dated = @($added | Where-Object { $_ -eq $dayInput -or $_.Contains($IsoDate) -or $_.Contains($underscored) })
    if ($dated.Count -eq 0) {
        return @()
    }
    $existing = @(& git -C $repo ls-tree -r --name-only origin/main -- @dated)
    if ($LASTEXITCODE -ne 0) {
        throw "Could not check origin/main for the dated files of $Sha."
    }
    return @($dated | Where-Object { $existing -notcontains $_ })
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
        # A publish that failed to push leaves its validated override commit behind.
        # Rebasing it onto the cloud run conflicts on generated artifacts every time,
        # which used to deadlock the runner before it ever collected X bookmarks.
        # Today's leftover is disposable because the pipeline below regenerates every
        # file in it. A past day's is not: only that day's run produced its dated
        # files (2026-10-29 had to be restored by hand), so those are re-committed on
        # top of origin/main and ride on the publisher's push. Pushing them alone
        # would trigger generate-daily-news-json.yml (input/day/*.txt), whose bot
        # commit lands within a minute and rejects the strict publish hours later as
        # non-fast-forward, every day (2026-10-31: b52b3cf5 -> 6ed4228c in 43s).
        # A backfill left behind by a failed publish is handled the same way.
        $today = "{0:yyyy-MM-dd}" -f (Get-Date)
        $entries = @(& git -C $repo log "--format=%H%x09%s" --reverse "origin/main..HEAD")
        if ($LASTEXITCODE -ne 0) {
            throw "Could not list local commits ahead of origin/main."
        }
        $leftovers = @()
        $disposable = $entries.Count -gt 0
        foreach ($entry in $entries) {
            $sha, $subject = $entry -split "`t", 2
            if ($subject -match '^chore\(report\): (?:local override|backfill daily-news) (\d{4}-\d{2}-\d{2})$') {
                $leftovers += [pscustomobject]@{ Sha = $sha; Date = $Matches[1]; Subject = $subject }
            }
            else {
                $disposable = $false
            }
        }
        if ($disposable) {
            foreach ($commit in $leftovers) {
                $backupRef = "refs/override-backup/$($commit.Date)-$($commit.Sha.Substring(0, 10))"
                $refCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "update-ref", $backupRef, $commit.Sha) -Label "git update-ref"
                if ($refCode -ne 0) {
                    throw "Could not back up leftover commit $($commit.Sha) as $backupRef."
                }
                Write-RunnerLog "Backed up leftover commit $($commit.Sha) '$($commit.Subject)' as $backupRef"
            }
            Write-RunnerLog "Discarding leftover override commit(s): $(@($leftovers | ForEach-Object { $_.Subject }) -join '; ')"
            $resetCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "reset", "--hard", "origin/main") -Label "git reset"
            if ($resetCode -ne 0) {
                throw "Could not discard leftover override commits."
            }
            foreach ($commit in $leftovers) {
                if ($commit.Date -eq $today) {
                    continue
                }
                $rescue = @(Get-RescuePaths -Sha $commit.Sha -IsoDate $commit.Date)
                if ($rescue.Count -eq 0) {
                    Write-RunnerLog "Nothing to rescue from $($commit.Sha): origin/main already has its dated files."
                    continue
                }
                $checkoutCode = Invoke-LoggedCommand -FilePath "git" -Arguments (@("-C", $repo, "checkout", $commit.Sha, "--") + $rescue) -Label "git checkout"
                $commitCode = 1
                if ($checkoutCode -eq 0) {
                    $commitCode = Invoke-LoggedCommand -FilePath "git" -Arguments @("-C", $repo, "commit", "-m", "chore(report): backfill daily-news $($commit.Date)") -Label "git commit"
                }
                if ($commitCode -ne 0) {
                    throw "Could not build the backfill commit for $($commit.Date) from $($commit.Sha)."
                }
                Write-RunnerLog "Rescued $($rescue.Count) dated file(s) of $($commit.Date) from $($commit.Sha) onto HEAD for today's publish: $($rescue -join ', ')"
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
    $selectionOutput = $null
    $selectionCode = 0
    try {
        $selectionOutput = & $PythonPath -m src.auto_collect.provider_selection
        $selectionCode = $LASTEXITCODE
    }
    catch {
        $selectionCode = 1
    }
    if ($selectionCode -ne 0) {
        Write-RunnerLog "LLM provider selection failed; using ollama."
    }
    else {
        $note = ""
        foreach ($line in @($selectionOutput)) {
            $text = ([string]$line).Trim()
            if ($text.StartsWith("provider=")) {
                $chosen = $text.Substring(9).Trim()
                if ($chosen -eq "ollama" -or $chosen -eq "nvidia") {
                    $provider = $chosen
                }
            }
            elseif ($text.StartsWith("note=")) {
                $note = $text.Substring(5)
            }
        }
        if ($note) {
            Write-RunnerLog $note
        }
    }
    $preflightPath = Join-Path $repo "logs\auto_collect\provider_preflight.json"
    $preflightCode = Invoke-LoggedCommand -FilePath $PythonPath -Arguments @("-m", "src.auto_collect.provider_preflight", "--provider", $provider, "--probe", "--output", $preflightPath) -Label "provider preflight"
    if ($preflightCode -ne 0) {
        throw "Provider preflight failed; inspect provider_preflight.json. Publication is held."
    }
    Write-RunnerLog "Running pipeline with provider=$provider."
    $pipelineCode = Invoke-LoggedCommand -FilePath $PythonPath -Arguments @("-m", "src.auto_collect.main", "--provider", $provider, "--force") -Label "pipeline"
    if ($pipelineCode -ne 0) {
        throw "Daily report pipeline failed."
    }

    $reportDate = (Get-Date).ToString("yyyy-MM-dd")
    $message = "chore(report): local override $reportDate"
    $publisher = Join-Path $repo "scripts\publish_daily_report.py"
    $publishCode = Invoke-LoggedCommand -FilePath $PythonPath -Arguments @($publisher, "--repo", $repo, "--date", $reportDate, "--message", $message, "--push", "--require-quality") -Label "publisher"
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
