# Simple final fix for all slides

Write-Host "=== Simple final fix ===" -ForegroundColor Green

$files = @(
    "presentations\day_slides\day_slide_2025_08_19.html",
    "presentations\day_slides\day_slide_2025_08_20.html", 
    "presentations\day_slides\day_slide_2025_08_23.html",
    "presentations\day_slides\day_slide_2025_08_24.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Processing $file..." -ForegroundColor Yellow
        
        # Read with UTF-8 encoding
        $content = Get-Content $file -Raw -Encoding UTF8
        
        # Update reveal.js to 4.4.0
        $content = $content -replace 'reveal\.js@4\.3\.1', 'reveal.js@4.4.0'
        
        # Remove navigation slide section
        $content = $content -replace '(?s)<!-- Navigation Slide -->.*?</section>', ''
        
        # Remove nav-buttons CSS styles
        $content = $content -replace '(?s)\.navigation-card[^}]*}', ''
        $content = $content -replace '(?s)\.nav-buttons[^}]*}', ''
        $content = $content -replace '(?s)\.nav-btn[^}]*}', ''
        
        # Write back with UTF-8 encoding
        $content | Set-Content -Path $file -Encoding UTF8
        
        Write-Host "✓ Fixed $file" -ForegroundColor Green
    }
}

Write-Host "`n=== Committing fixes ===" -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_23.html
git add presentations/day_slides/day_slide_2025_08_24.html

git commit -m "fix: Remove navigation buttons and update reveal.js

- Updated reveal.js from 4.3.1 to 4.4.0 for consistency
- Removed navigation buttons causing overlap
- Fixed UTF-8 encoding issues

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "`n=== Fixes applied and pushed ===" -ForegroundColor Green