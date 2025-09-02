param(
  [string]$Root = "presentations"
)

Write-Host "Applying x.ai-inspired theme to HTML files under '$Root'..." -ForegroundColor Cyan

if (-not (Test-Path $Root)) {
  Write-Error "Root path '$Root' not found."; exit 1
}

$files = Get-ChildItem -Path $Root -Filter *.html -Recurse -File
$updated = 0; $skipped = 0

foreach ($f in $files) {
  $content = Get-Content -LiteralPath $f.FullName -Raw
  if ($content -match 'xai-init\.js') { $skipped++; continue }

  # decide relative path to assets
  $relative = if ($f.DirectoryName -like "*\presentations\day_slides*") { "../assets/xai-init.js" } else { "assets/xai-init.js" }

  $inject = '<script src="' + $relative + '" defer></script>'

  if ($content -match "</head>") {
    $new = $content -replace "</head>", ($inject + "`n</head>")
  } elseif ($content -match "<body[\s>]") {
    $new = $content -replace "(<body[\s>])", ("`$1`n" + $inject + "`n")
  } else {
    $new = $content + "`n" + $inject + "`n"
  }

  Set-Content -LiteralPath $f.FullName -Value $new -Encoding UTF8
  $updated++
}

Write-Host ("Updated: {0} files, Skipped: {1}" -f $updated, $skipped) -ForegroundColor Green
