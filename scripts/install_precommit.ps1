$ErrorActionPreference = 'Stop'
$hook = @'
#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

# simple mojibake detector
$patterns = @('蟷ｴ','譛・','譌･','朁E','繝','縺','ﾃ宥')

$files = git diff --cached --name-only --diff-filter=ACM | Where-Object { $_ -match '\.(html|css|js|mjs|md)$' }
$bad = @()
foreach($f in $files){
  $c = Get-Content -LiteralPath $f -Raw -Encoding UTF8
  foreach($p in $patterns){ if($c -like "*${p}*") { $bad += $f; break } }
}
if($bad.Count -gt 0){
  Write-Host "Found possible mojibake in:" -ForegroundColor Red
  $bad | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
  Write-Host "Run: python tools/repair_all_html.py and re-stage files." -ForegroundColor Red
  exit 1
}
exit 0
'@

$hookPath = Join-Path (Resolve-Path .git\hooks) 'pre-commit'
Set-Content -LiteralPath $hookPath -Value $hook -Encoding UTF8
& git update-index --chmod=+x .git/hooks/pre-commit | Out-Null
Write-Host "Installed pre-commit hook (UTF-8 check)." -ForegroundColor Green

