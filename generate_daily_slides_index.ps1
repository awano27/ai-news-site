param(
  [string]$SlidesDir = "presentations/day_slides",
  [string]$OutFile = "presentations/day_slides_index.html"
)

function Get-TitleFromFile([string]$path){
  $html = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  $title = ([regex]::Match($html, '<title>(.*?)</title>', 'Singleline')).Groups[1].Value
  if([string]::IsNullOrWhiteSpace($title)){
    $title = ([regex]::Match($html, '<h1[^>]*>(.*?)</h1>', 'Singleline')).Groups[1].Value
  }
  # strip tags
  $title = [regex]::Replace($title, '<[^>]+>', '')
  # fix common artifacts
  $title = $title -replace '朁E','月'
  $title = [regex]::Replace($title, '\s+', ' ')
  $title = $title.Trim()
  # remove leading date like: 2025年09月03日 - 
  $title = [regex]::Replace($title, '^[0-9]{4}年[0-9]{2}月[0-9]{2}日\s*-\s*', '')
  return $title
}

function HtmlEnc([string]$s){
  if([string]::IsNullOrEmpty($s)){ return '' }
  $o = $s -replace '&','&amp;'
  $o = $o -replace '<','&lt;'
  $o = $o -replace '>','&gt;'
  return $o
}

if(!(Test-Path $SlidesDir)){ throw "Slides directory not found: $SlidesDir" }

$files = Get-ChildItem -Path $SlidesDir -Filter 'day_slide_*.html' -File | Sort-Object Name -Descending

$byDate = @{}
foreach($f in $files){
  if($f.Name -match '^day_slide_(\d{4})_(\d{2})_(\d{2})(?:_detailed)?\.html$'){
    $dateKey = "$($Matches[1])-$($Matches[2])-$($Matches[3])"
    $disp = "$($Matches[1])/$($Matches[2])/$($Matches[3])"
    $title = Get-TitleFromFile $f.FullName
    $entry = [pscustomobject]@{ dateKey=$dateKey; dateDisp=$disp; file=$f.Name; title=$title; detailed=($f.Name -like '*_detailed.html') }
    if($byDate.ContainsKey($dateKey)){
      # prefer detailed
      if($entry.detailed){ $byDate[$dateKey] = $entry }
    } else {
      $byDate[$dateKey] = $entry
    }
  }
}

$ordered = $byDate.Values | Sort-Object dateKey -Descending

$head = @"
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Daily Slides Index</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
  <script src="assets/xai-init.js" defer></script>
  <style>
    :root{--bg:#f8fafc;--fg:#0f172a;--accent:#3b82f6;--border:#e2e8f0}
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--fg);font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif}
    .wrap{display:grid;grid-template-columns:260px 1fr;min-height:100vh}
    aside{background:#0f172a;color:#e5e7eb;padding:18px}
    .brand{font-weight:800;margin:4px 0 14px}
    .nav a{display:block;color:#cbd5e1;text-decoration:none;padding:8px 10px;border-radius:8px}
    .nav a:hover{background:#1e293b;color:#fff}
    main{padding:20px}
    h1{margin:4px 0 16px;font-size:24px}
    .note{background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin:0 0 16px}
    ul.slides{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}
    ul.slides li a{display:block;background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--fg)}
    ul.slides li a:hover{border-color:#c7d2fe;box-shadow:0 4px 16px rgba(2,6,23,.06)}
    .date{display:inline-block;font-size:12px;font-weight:800;color:#fff;background:var(--accent);padding:2px 8px;border-radius:999px;margin-right:8px}
  </style>
</head>
<body>
  <div class="wrap">
    <aside>
      <div class="brand">AI Intelligence</div>
      <nav class="nav">
        <a href="index.html">Home</a>
        <a href="ai_ranking_interactive.html">Ranking</a>
        <a href="integrated_report.html">Report</a>
        <a href="advanced_intelligence_report_20250826.html">Advanced</a>
      </nav>
    </aside>
    <main>
      <h1>Daily Slides</h1>
      <div class="note">日別スライドのトピック名を表示しています。</div>
      <ul class="slides">
"@

$itemsHtml = foreach($it in $ordered){
  $t = if([string]::IsNullOrWhiteSpace($it.title)) { 'Daily Slide' } else { $it.title }
  "        <li><a href=\"day_slides/$($it.file)\"><span class=\"date\">$($it.dateDisp)</span> $(HtmlEnc $t)</a></li>"
}

$tail = @"
      </ul>
    </main>
  </div>
</body>
</html>
"@

Set-Content -LiteralPath $OutFile -Value ($head + ($itemsHtml -join "`n") + $tail) -Encoding UTF8
Write-Host "Generated $OutFile with $($ordered.Count) entries." -ForegroundColor Green
