# Complete removal of all navigation buttons from day slides

Write-Host "=== Completely removing all navigation buttons ===" -ForegroundColor Green

$files = @(
    "presentations\day_slides\day_slide_2025_08_19.html",
    "presentations\day_slides\day_slide_2025_08_20.html", 
    "presentations\day_slides\day_slide_2025_08_22.html",
    "presentations\day_slides\day_slide_2025_08_23.html",
    "presentations\day_slides\day_slide_2025_08_24.html",
    "presentations\day_slides\day_slide_2025_08_27.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Processing $file..." -ForegroundColor Yellow
        
        $content = Get-Content $file -Raw -Encoding UTF8
        
        # Remove navigation slide section completely
        $content = $content -replace '(?s)\s*<!-- Navigation Slide -->.*?</section>', ''
        
        # Remove any remaining nav-buttons div
        $content = $content -replace '(?s)<div class="nav-buttons">.*?</div>', ''
        
        # Remove nav-buttons CSS
        $content = $content -replace '(?s)\.nav-buttons \{[^}]+\}', ''
        $content = $content -replace '(?s)\.nav-btn \{[^}]+\}', ''
        $content = $content -replace '(?s)\.nav-btn:hover \{[^}]+\}', ''
        
        # Remove navigation-card CSS
        $content = $content -replace '(?s)\.navigation-card \{[^}]+\}', ''
        
        # Write back
        Set-Content -Path $file -Value $content -Encoding UTF8
        
        Write-Host "✓ Completely cleaned $file" -ForegroundColor Green
    }
}

Write-Host "`n=== Committing final cleanup ===" -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_*.html
git commit -m "fix: Complete removal of all navigation buttons from slides

- Removed all nav-buttons HTML elements completely
- Removed all nav-buttons CSS styling
- Removed navigation slide sections entirely
- Only reveal.js slide navigation controls remain
- Bottom-right button overlap completely eliminated

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "`n=== All navigation buttons completely removed ===" -ForegroundColor Green