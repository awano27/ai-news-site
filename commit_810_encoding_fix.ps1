Write-Host "=== Committing 8/10 slide encoding fix ===" -ForegroundColor Cyan

Set-Location "C:\Users\yoshitaka\ai-news-site"

# Add the repaired slide
Write-Host "Adding repaired 8/10 slide..." -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_10.html

# Check status
Write-Host "Current status:" -ForegroundColor Yellow
git status --short

# Commit the fix
Write-Host "Committing encoding repair..." -ForegroundColor Green
git commit -m "fix: Repair 8/10 slide encoding corruption - complete reconstruction

URGENT FIX: Resolve severe mojibake in Japanese text
- Completely reconstructed day_slide_2025_08_10.html with proper UTF-8
- Applied 08/27 excellent template with perfect scrolling CSS
- GPT-5 content: production deployment, API examples, reasoning_effort
- Impact Score: 92pt with comprehensive analysis
- Fixed corrupted text like 'AI業界�E' and '皁E��値' 

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push origin main

Write-Host "`n✅ 8/10 slide encoding fix committed and pushed!" -ForegroundColor Green