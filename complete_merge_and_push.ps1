Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "📝 Completing the merge..." -ForegroundColor Cyan
git commit -m "Merge remote changes and add 8/30 slide with 8/26 title fix"

Write-Host ""
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 All changes are now live!" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "📌 View your slides at:" -ForegroundColor Cyan
    Write-Host "   Main Dashboard: https://awano27.github.io/ai-news-site/presentations/index.html" -ForegroundColor Yellow
    Write-Host "   8/30 Slide (NEW): https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_30.html" -ForegroundColor Green
    Write-Host "   8/26 Slide (FIXED): https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_26.html" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Total slides: 27" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Please check the error message above." -ForegroundColor Red
}