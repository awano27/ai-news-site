Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "📥 Pulling latest changes from GitHub..." -ForegroundColor Cyan
git pull origin main

Write-Host ""
Write-Host "📤 Pushing local changes to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ Sync and push completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 View the slides at:" -ForegroundColor Cyan
    Write-Host "   Main Dashboard: https://awano27.github.io/ai-news-site/presentations/index.html" -ForegroundColor Yellow
    Write-Host "   8/30 Slide: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_30.html" -ForegroundColor Yellow
    Write-Host "   8/26 Slide (Fixed): https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_26.html" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "⚠️ There might be conflicts to resolve. Please check git status." -ForegroundColor Red
    git status
}