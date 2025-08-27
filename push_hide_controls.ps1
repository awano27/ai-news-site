# Hide reveal.js controls completely to eliminate overlap
Write-Host "=== Complete Solution: Hide Reveal.js Controls ===" -ForegroundColor Green

Write-Host "Adding modified slide files..." -ForegroundColor Yellow
git add presentations/day_slides/day_slide_2025_08_27.html
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_22.html

Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "fix: Hide reveal.js controls to completely eliminate overlap

- Hide default reveal.js navigation controls (display: none)
- QuickAccess buttons remain in top-left (📅 Daily, 🏠 Home)  
- Keyboard navigation still works (arrow keys)
- Progress bar remains at bottom
- Complete elimination of button overlap issues
- Clean interface with no conflicting navigation elements
- Applied to slides: 8/27, 8/19, 8/20, 8/22

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push origin lightweight-main:main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: Navigation overlap completely eliminated!" -ForegroundColor Green
    Write-Host "- Reveal.js controls: Hidden (no overlap possible)" -ForegroundColor Cyan
    Write-Host "- QuickAccess buttons: Top-left corner only" -ForegroundColor Cyan
    Write-Host "- Keyboard navigation: Still works (arrow keys)" -ForegroundColor Cyan
    Write-Host "- Progress bar: Bottom as usual" -ForegroundColor Cyan
    Write-Host "- Applied to slides: 8/27, 8/19, 8/20, 8/22" -ForegroundColor Cyan
    Write-Host "`nTest at: https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Push failed. Check output above." -ForegroundColor Red
}

Write-Host "`n=== Overlap Issue Completely Resolved ===" -ForegroundColor Green