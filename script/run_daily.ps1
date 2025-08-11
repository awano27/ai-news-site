Param(
  [switch]$Push
)

$ErrorActionPreference = 'Stop'

# Resolve project root (ai-news-site)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

# Ensure venv
$Venv = Join-Path $Root '.venv'
$PythonExe = Join-Path $Venv 'Scripts/python.exe'

if (-not (Test-Path $PythonExe)) {
  Write-Host '[setup] creating venv'
  try {
    python -m venv $Venv
  } catch {
    py -3 -m venv $Venv
  }
}

Write-Host '[setup] installing requirements'
& $PythonExe -m pip install --upgrade pip | Out-Host
& $PythonExe -m pip install -r (Join-Path $Root 'requirements.txt') | Out-Host

# Run builder
Write-Host '[run] build news'
& $PythonExe (Join-Path $Root 'script/build_news.py') | Out-Host

# Optional: commit & push if in git repo
if (Test-Path (Join-Path $Root '.git')) {
  $newsChanges = git -C $Root status --porcelain -- news | Out-String
  if ($newsChanges.Trim().Length -gt 0) {
    git -C $Root add news
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm K'
    git -C $Root commit -m "chore(news): auto-update $ts" | Out-Host
    if ($Push -or $env:GIT_AUTO_PUSH -eq '1') {
      git -C $Root push | Out-Host
    }
  }
}

Write-Host '[done]'


