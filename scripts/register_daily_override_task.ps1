[CmdletBinding()]
param(
    [string]$CheckoutPath = "C:\develop\ai-news-site-automation",
    [string]$RepositoryUrl = "https://github.com/awano27/ai-news-site.git",
    [string]$TaskName = "VisionHub Daily News Override",
    [string]$At = "08:00",
    [switch]$PlanOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Normalize-GitUrl {
    param([Parameter(Mandatory = $true)][string]$Url)
    $normalized = $Url.Trim().TrimEnd("/")
    if ($normalized.EndsWith(".git", [System.StringComparison]::OrdinalIgnoreCase)) {
        $normalized = $normalized.Substring(0, $normalized.Length - 4)
    }
    return $normalized.ToLowerInvariant()
}

$checkout = [System.IO.Path]::GetFullPath($CheckoutPath)
$launcher = Join-Path $checkout "scripts\run_daily_override.bat"
$runtimeMarkerName = "visionhub-daily-news-override-runtime.json"
$actionArguments = "/d /s /c `"`"$launcher`"`""
$plan = [ordered]@{
    checkoutPath = $checkout
    repositoryUrl = $RepositoryUrl
    taskName = $TaskName
    action = [ordered]@{
        execute = "cmd.exe"
        arguments = $actionArguments
        workingDirectory = $checkout
    }
    trigger = [ordered]@{ dailyAt = $At }
    principal = [ordered]@{ logonType = "InteractiveToken" }
    settings = [ordered]@{
        startWhenAvailable = $true
        multipleInstances = "IgnoreNew"
        executionTimeLimit = "PT1H"
        disallowStartIfOnBatteries = $false
        stopIfGoingOnBatteries = $false
    }
}

if ($PlanOnly) {
    $plan | ConvertTo-Json -Compress -Depth 5
    exit 0
}

if (-not (Test-Path -LiteralPath $checkout)) {
    $parent = Split-Path -Parent $checkout
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    & git clone $RepositoryUrl $checkout
    if ($LASTEXITCODE -ne 0) {
        throw "git clone failed for $RepositoryUrl"
    }
}
else {
    if (-not (Test-Path -LiteralPath (Join-Path $checkout ".git") -PathType Container)) {
        throw "Existing checkout is not an independent Git clone: $checkout"
    }
    $origin = (& git -C $checkout config --get remote.origin.url).Trim()
    if ($LASTEXITCODE -ne 0 -or (Normalize-GitUrl $origin) -ne (Normalize-GitUrl $RepositoryUrl)) {
        throw "Existing checkout origin does not match RepositoryUrl; it was not changed."
    }
}

$gitDirectory = Join-Path $checkout ".git"
if (-not (Test-Path -LiteralPath $gitDirectory -PathType Container)) {
    throw "Checkout is not an independent Git clone: $checkout"
}
@{ checkoutPath = $checkout } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $gitDirectory $runtimeMarkerName) -Encoding utf8

$action = New-ScheduledTaskAction -Execute $env:ComSpec -Argument $actionArguments -WorkingDirectory $checkout
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType InteractiveToken
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
