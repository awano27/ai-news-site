# Fix sidebar navigation in day_slides_index.html
Write-Host "=== Fixing sidebar navigation in day slides index ===" -ForegroundColor Green

Write-Host "Adding modified files..." -ForegroundColor Yellow
git add presentations/day_slides_index.html

Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "fix: Remove circular navigation in day slides index sidebar

- Remove self-referencing 毎日スライド link from sidebar
- Add ホーム link to main index page instead
- Fix navigation flow to prevent circular references
- Maintain proper navigation hierarchy

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push origin lightweight-main:main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: Navigation fixed!" -ForegroundColor Green
    Write-Host "- Removed circular reference (毎日スライド → 毎日スライド)" -ForegroundColor Cyan
    Write-Host "- Added proper ホーム link to main page" -ForegroundColor Cyan
    Write-Host "- Navigation flow now correct" -ForegroundColor Cyan
    Write-Host "`nView at: https://awano27.github.io/ai-news-site/presentations/day_slides_index.html" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Push failed. Check output above." -ForegroundColor Red
}

Write-Host "`n=== Navigation Fix Complete ===" -ForegroundColor Green