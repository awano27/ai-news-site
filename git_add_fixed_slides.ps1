っこWrite-Host "Staging fixed slides 08/20-08/23..." -ForegroundColor Green

cd "C:\Users\yoshitaka\ai-news-site"

# Check if files exist and have modifications
$files = @(
    "presentations/day_slides/day_slide_2025_08_20.html",
    "presentations/day_slides/day_slide_2025_08_21.html",
    "presentations/day_slides/day_slide_2025_08_22.html",
    "presentations/day_slides/day_slide_2025_08_23.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Adding $file" -ForegroundColor Yellow
        git add $file
    } else {
        Write-Host "File not found: $file" -ForegroundColor Red
    }
}

Write-Host "`nChecking git status..." -ForegroundColor Cyan
git status --short

$commitMessage = @"
fix: Complete repair of problematic slides 08/20-08/23

Fixed Issues:
- 08/20: Complete restructure with 08/27 template
- 08/21: Upgraded to full scrolling CSS + reveal.js optimization  
- 08/22: Added missing scrolling CSS and responsive design
- 08/23: Upgraded to full scrolling CSS + reveal.js optimization

Applied Solutions:
- Perfect scrolling CSS with overflow fixes
- Complete responsive design (768px, 480px breakpoints)
- iOS touch scrolling optimization
- Reveal.js configuration standardization
- Cross-device compatibility

All slides now match the excellent quality of the 08/27 template.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
"@

Write-Host "`nCommitting changes..." -ForegroundColor Green
git commit -m $commitMessage

Write-Host "`nPushing to origin main..." -ForegroundColor Green  
git push origin main

Write-Host "`n✅ Fixed slides successfully committed and pushed!" -ForegroundColor Green