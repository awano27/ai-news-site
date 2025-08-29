# Update all slides to use reveal.js 4.4.0 for consistency

Write-Host "=== Updating reveal.js version to 4.4.0 ===" -ForegroundColor Green

$files = @(
    "presentations\day_slides\day_slide_2025_08_19.html",
    "presentations\day_slides\day_slide_2025_08_20.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Updating $file..." -ForegroundColor Yellow
        
        $content = Get-Content $file -Raw -Encoding UTF8
        
        # Update reveal.js CDN URLs to version 4.4.0
        $content = $content -replace 'reveal\.js@4\.3\.1', 'reveal.js@4.4.0'
        
        # Write back
        Set-Content -Path $file -Value $content -Encoding UTF8
        
        Write-Host "✓ Updated $file to reveal.js 4.4.0" -ForegroundColor Green
    }
}

Write-Host "`n=== Committing version updates ===" -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html

git commit -m "fix: Update reveal.js to 4.4.0 for consistent navigation

- Updated 8/19 and 8/20 slides from 4.3.1 to 4.4.0
- Ensures consistent behavior across all slides
- Should fix navigation controls on older slides

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "`n=== All slides now use reveal.js 4.4.0 ===" -ForegroundColor Green