Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "📊 Committing Interactive AI Ranking Dashboard..." -ForegroundColor Cyan
git add presentations/ai_ranking_interactive.html
git add presentations/index.html

git commit -m "feat(ranking): complete interactive AI ranking dashboard redesign

🎯 Major Features Implemented:
- ✅ Evaluation logic transparency with weight adjustment sliders  
- ✅ Advanced filtering (category, purpose) and sorting capabilities
- ✅ Interactive charts with tooltips and click-to-analyze
- ✅ Data export (CSV/JSON) and shareable URL generation
- ✅ Real-time update notifications with auto-refresh
- ✅ Responsive design with accessibility improvements
- ✅ Pagination and performance optimization

📈 Technical Improvements:
- Real-time score recalculation based on user weights
- Chart.js integration with radar and line charts  
- URL parameter persistence for sharing configurations
- Mobile-responsive grid layout with touch support
- WCAG compliant color contrast and keyboard navigation

🔧 UI/UX Enhancements:
- Clean, modern Material Design-inspired interface
- Intuitive control panel with grouped functionality
- Interactive tooltips and hover states
- Loading states and smooth transitions
- Clear navigation with breadcrumb integration

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host ""
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "🎉 Interactive Ranking Dashboard is now LIVE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 Access the new dashboard at:" -ForegroundColor Cyan
    Write-Host "   🏆 Interactive Ranking: https://awano27.github.io/ai-news-site/presentations/ai_ranking_interactive.html" -ForegroundColor Yellow
    Write-Host "   🏠 Main Dashboard: https://awano27.github.io/ai-news-site/presentations/index.html" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "✨ Key Features:" -ForegroundColor Magenta
    Write-Host "   • Real-time weight adjustment sliders" -ForegroundColor White
    Write-Host "   • Interactive charts with tooltips" -ForegroundColor White
    Write-Host "   • CSV/JSON export capabilities" -ForegroundColor White
    Write-Host "   • Shareable configuration URLs" -ForegroundColor White
    Write-Host "   • Mobile-responsive design" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Please check the error message above." -ForegroundColor Red
}