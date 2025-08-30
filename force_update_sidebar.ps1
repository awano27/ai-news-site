Write-Host "=== Forcing sidebar navigation update ===" -ForegroundColor Cyan

Set-Location "C:\Users\yoshitaka\ai-news-site"

# Check git status first
Write-Host "Current git status:" -ForegroundColor Yellow
git status --short

Write-Host "`nAdding index file..." -ForegroundColor Green
git add presentations/day_slides_index.html

Write-Host "Current status after add:" -ForegroundColor Yellow  
git status --short

Write-Host "`nCommitting changes..." -ForegroundColor Green
git commit -m "fix: Force update sidebar navigation with all daily slides

URGENT: Add complete daily slide navigation to sidebar
- All 28 slides now accessible via left menu
- 8/28 OpenAI Codex prominently displayed at top
- Daily Slides section with proper organization
- Chronological ordering (newest to oldest)

This ensures 8/28 and all other slides are discoverable.

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "`nPushing to GitHub..." -ForegroundColor Green
git push origin main --force-with-lease

Write-Host "`n✅ Sidebar navigation forcefully updated!" -ForegroundColor Green
Write-Host "Wait 2-3 minutes for GitHub Pages deployment." -ForegroundColor Yellow