# Remove QuickAccess buttons from all day slides

Write-Host "=== Removing QuickAccess buttons from all slides ===" -ForegroundColor Green

$files = @(
    "presentations\day_slides\day_slide_2025_08_19.html",
    "presentations\day_slides\day_slide_2025_08_20.html", 
    "presentations\day_slides\day_slide_2025_08_22.html",
    "presentations\day_slides\day_slide_2025_08_23.html",
    "presentations\day_slides\day_slide_2025_08_24.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Processing $file..." -ForegroundColor Yellow
        
        $content = Get-Content $file -Raw
        
        # Remove nav-buttons CSS
        $content = $content -replace '(?s)\.reveal \.nav-buttons \{[^}]+\}.*?\.reveal \.nav-btn:hover \{[^}]+\}', ''
        
        # Remove nav-buttons HTML
        $content = $content -replace '(?s)<p[^>]*>他のレポート[^<]*</p>.*?<div class="nav-buttons">.*?</div>', ''
        
        # Write back
        Set-Content -Path $file -Value $content -Encoding UTF8
        
        Write-Host "✓ Removed QuickAccess from $file" -ForegroundColor Green
    }
}

Write-Host "`n=== Committing changes ===" -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_*.html
git commit -m "fix: Completely remove QuickAccess navigation buttons

- Removed nav-buttons CSS styling completely
- Removed nav-buttons HTML elements 
- No more overlap issues as buttons are fully eliminated
- Slide navigation controls remain functional

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "`n=== QuickAccess buttons completely removed ===" -ForegroundColor Green