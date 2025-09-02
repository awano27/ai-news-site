param(
  [string]$Root = "presentations"
)

Write-Host "Reverting xai-theme injection under '$Root'..." -ForegroundColor Yellow

if (-not (Test-Path $Root)) { Write-Error "Root path '$Root' not found."; exit 1 }

$files = Get-ChildItem -Path $Root -Filter *.html -Recurse -File
$updated = 0; $skipped = 0

foreach ($f in $files) {
  $content = Get-Content -LiteralPath $f.FullName -Raw
  if ($content -notmatch 'xai-init\.js') { $skipped++; continue }
  $new = $content -replace "\r?\n?\s*<script\s+src=\"\.?\.?/?.*xai-init\.js\"\s+defer></script>\s*", ""
  Set-Content -LiteralPath $f.FullName -Value $new -Encoding UTF8
  $updated++
}

Write-Host ("Updated: {0} files, Skipped: {1}" -f $updated, $skipped) -ForegroundColor Green
Write-Host "Note: assets remain at presentations/assets/. Remove manually if desired." -ForegroundColor DarkGray

