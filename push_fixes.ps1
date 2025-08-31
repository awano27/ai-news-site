Set-Location "C:\Users\yoshitaka\ai-news-site"

# Add all changes
git add -A

# Commit with message
git commit -m "fix: correct 8/26 slide title and add 8/30 Claude Chrome extension slide

- Fix 8/26 title from 'Claude Sonnet' to 'Gemini 2.5 Flash Image' in navigation
- Add complete 8/30 slide for Claude AI Chrome Extension (94pt impact)
- Update all navigation entries and statistics (27 slides total)

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin main

Write-Host ""
Write-Host "✅ Push completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📌 View the slides at:" -ForegroundColor Cyan
Write-Host "   Main Dashboard: https://awano27.github.io/ai-news-site/presentations/index.html" -ForegroundColor Yellow
Write-Host "   8/30 Slide: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_30.html" -ForegroundColor Yellow
Write-Host "   8/26 Slide: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_26.html" -ForegroundColor Yellow