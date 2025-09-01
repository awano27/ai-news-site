Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🔧 Fixing 8/31 slide white screen issue..." -ForegroundColor Cyan

git add presentations/day_slides/day_slide_2025_08_31.html

git commit -m "fix(slides): resolve 8/31 slide white screen issue

- Fixed Reveal.js configuration causing white screen display  
- Applied working 8/27 template settings (embedded: true, hash: false)
- Restored proper scrolling functionality and keyboard shortcuts
- Slide now displays AI Master Prompt content correctly

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host ""
Write-Host "📤 Pushing fix to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ 8/31 slide white screen fix deployed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Test the slide:" -ForegroundColor Cyan  
    Write-Host "   https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_31.html" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Wait 2-3 minutes for GitHub Pages deployment, then refresh your browser" -ForegroundColor Magenta
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Check error above." -ForegroundColor Red
}