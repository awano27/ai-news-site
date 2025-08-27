# Push Updated Slides for 8/22, 8/23, 8/24 to GitHub
Write-Host "=== Updated Daily Slides: Push to GitHub ===" -ForegroundColor Green

Write-Host "Adding updated slide files..." -ForegroundColor Yellow
git add presentations/day_slides/day_slide_2025_08_22.html
git add presentations/day_slides/day_slide_2025_08_23.html
git add presentations/day_slides/day_slide_2025_08_24.html

Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "feat: Update daily slides with latest AI news content

- 8/22: Apple×Google AI partnership - Siri renewal with Gemini
- 8/23: DeepSeek V3.1 - 671B parameter open-source AI revolution
- 8/24: xAI Grok 2.5 - Musk's open-source AI democratization

Content updates:
- Comprehensive 6-section structure for each slide
- Latest AI news analysis with KPI evaluation
- Technical specifications and industry impact
- Real-time social media reaction analysis
- Enhanced navigation with left-top QuickAccess buttons
- Hidden reveal.js controls to prevent overlap

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push origin lightweight-main:main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: Updated slides pushed to GitHub!" -ForegroundColor Green
    Write-Host "- 8/22 slide: Apple×Google AI partnership" -ForegroundColor Cyan
    Write-Host "- 8/23 slide: DeepSeek V3.1 open-source revolution" -ForegroundColor Cyan
    Write-Host "- 8/24 slide: xAI Grok 2.5 democratization" -ForegroundColor Cyan
    Write-Host "- Navigation overlap completely resolved" -ForegroundColor Cyan
    Write-Host "`nView at: https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Push failed. Check output above." -ForegroundColor Red
}

Write-Host "`n=== Daily Slides Update Complete ===" -ForegroundColor Green