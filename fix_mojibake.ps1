param(
  [string]$Root = "presentations"
)

Write-Host "Fixing common mojibake artifacts under '$Root'..." -ForegroundColor Cyan

if (-not (Test-Path $Root)) { Write-Error "Root '$Root' not found"; exit 1 }

$files = Get-ChildItem -Path $Root -Recurse -Filter *.html -File
$fixed = 0

foreach ($f in $files) {
  $text = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
  $orig = $text
  # Broken closing tags like E/h3>
  $text = [regex]::Replace($text, 'E\/(h[1-6]|div|span|p|button|a|li|ul|ol|section|strong|em)>', '</$1>')
  # Dates: 朁E -> 月
  $text = $text -replace '朁E','月'
  # Common UI strings
  $text = $text -replace 'スライチE','スライド'
  $text = $text -replace 'インチE..クス','インデックス'
  $text = $text -replace 'ホ.?Eム','ホーム'
  $text = $text -replace 'レポ.?Eト','レポート'
  $text = $text -replace '採用凍.?E','採用凍結'
  $text = $text -replace '最新牁E','最新情報'
  # Stray symbols
  $text = $text -replace '✁E','✓'

  if ($text -ne $orig) {
    Set-Content -LiteralPath $f.FullName -Value $text -Encoding UTF8
    $fixed++
  }
}

Write-Host "Fixed $fixed file(s)." -ForegroundColor Green

