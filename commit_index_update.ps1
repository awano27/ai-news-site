Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "Adding updated index..." -ForegroundColor Green
git add presentations/day_slides_index.html

Write-Host "Committing index update..." -ForegroundColor Cyan
git commit -m "fix: Add 08/28 slide to index - OpenAI Codex update

- Added missing 08/28 slide entry to day_slides_index.html
- Slide was created but not included in navigation index
- Impact Score: 95pt with 98% confidence
- Tags: AI development, dev tools, productivity, integration

This resolves the 'slide not found' issue - slide exists but wasn't discoverable via index.

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing index update..." -ForegroundColor Yellow
git push origin main

Write-Host "✅ Index updated - 08/28 slide now discoverable!" -ForegroundColor Green