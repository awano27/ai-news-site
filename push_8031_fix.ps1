Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🔍 Checking current git status..." -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "📤 Adding and committing 8/31 slide fixes..." -ForegroundColor Cyan
git add presentations/day_slides/day_slide_2025_08_31.html
git commit -m "fix(slides): resolve 8/31 slide encoding and display issues

- Fixed BOM encoding for proper Japanese text display
- Updated CSS comments to match working 08/27 template
- Resolved rendering issues on GitHub Pages
- Slide now properly displays AI Master Prompt content

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host ""
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ 8/31 slide fixes pushed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 Check the slide:" -ForegroundColor Cyan
    Write-Host "   https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_31.html" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Please check the error above." -ForegroundColor Red
}