Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "Pulling latest changes..." -ForegroundColor Cyan
git pull origin main

Write-Host "Adding slide files..." -ForegroundColor Yellow
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_21.html  
git add presentations/day_slides/day_slide_2025_08_22.html
git add presentations/day_slides/day_slide_2025_08_23.html

Write-Host "Current status:" -ForegroundColor Green
git status --short

Write-Host "Committing changes..." -ForegroundColor Cyan
git commit -m "fix: Complete repair of problematic slides 08/20-08/23

- Fixed all scrolling and display issues
- Applied 08/27 template to all slides  
- Added responsive design
- Standardized reveal.js configurations

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing changes..." -ForegroundColor Green
git push origin main

Write-Host "Done!" -ForegroundColor Green