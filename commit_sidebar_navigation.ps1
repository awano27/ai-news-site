Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "Adding updated navigation..." -ForegroundColor Green
git add presentations/day_slides_index.html

Write-Host "Committing sidebar navigation update..." -ForegroundColor Cyan
git commit -m "feat: Add complete slide navigation to sidebar

- Added all 28 daily slides to left navigation menu
- 08/28 OpenAI Codex slide now prominently displayed at top
- Created 'Daily Slides' section with visual separator
- Organized slides chronologically (newest first)
- Enhanced discoverability for all slides including recent ones

Navigation improvements:
- Direct access to all slides from sidebar
- Clear visual categorization
- Consistent naming convention
- User-friendly chronological ordering

This resolves the issue where 08/28 and other slides were not discoverable via left menu navigation.

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing navigation update..." -ForegroundColor Yellow
git push origin main

Write-Host "✅ Complete slide navigation now available in sidebar!" -ForegroundColor Green