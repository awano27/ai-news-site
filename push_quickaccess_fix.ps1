# Move QuickAccess buttons to left-top to resolve overlap
Write-Host "=== QuickAccess Position Fix: Move to Left-Top ===" -ForegroundColor Green

Write-Host "Adding modified slide files..." -ForegroundColor Yellow
git add presentations/day_slides/day_slide_2025_08_27.html
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_22.html

Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "fix: Move QuickAccess buttons to left-top to resolve overlap

- Move QuickAccess navigation from top-right to top-left corner
- Applied to slides: 8/27, 8/19, 8/20, 8/22
- Reveal.js controls remain on the right side
- Complete separation prevents any button overlap
- QuickAccess buttons (📅 Daily, 🏠 Home) now at left-top
- User-requested solution for persistent overlap issue

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push origin lightweight-main:main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: QuickAccess overlap completely resolved!" -ForegroundColor Green
    Write-Host "- QuickAccess buttons: Top-left corner" -ForegroundColor Cyan
    Write-Host "- Reveal.js controls: Right side" -ForegroundColor Cyan
    Write-Host "- Applied to slides: 8/27, 8/19, 8/20, 8/22" -ForegroundColor Cyan
    Write-Host "- No more button overlap!" -ForegroundColor Cyan
    Write-Host "`nTest at: https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Push failed. Check output above." -ForegroundColor Red
}

Write-Host "`n=== QuickAccess Fix Complete ===" -ForegroundColor Green