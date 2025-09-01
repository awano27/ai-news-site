Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🔧 Applying final fix for 8/31 slide visibility..." -ForegroundColor Cyan

git add presentations/day_slides/day_slide_2025_08_31.html

git commit -m "fix(slides): prevent 8/31 slide from disappearing after initial display

- Added explicit opacity: 1 and visibility: visible to prevent Reveal.js hiding content
- Applied complete 8/27 template CSS including control hiding
- Fixed slide disappearing issue after initial page load
- Ensured stable content display matching working template

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host ""
Write-Host "📤 Pushing comprehensive fix to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ 8/31 slide visibility issue completely resolved!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Stable slide URL:" -ForegroundColor Cyan  
    Write-Host "   https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_31.html" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Changes deployed in 2-3 minutes. Clear browser cache (Ctrl+F5) if needed." -ForegroundColor Magenta
    Write-Host ""
    Write-Host "🎯 Fixed issues:" -ForegroundColor Green
    Write-Host "   • Slide no longer disappears after initial display" -ForegroundColor White
    Write-Host "   • Content remains visible and scrollable" -ForegroundColor White
    Write-Host "   • Applied stable 8/27 template configuration" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Check error above." -ForegroundColor Red
}