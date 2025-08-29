# Force update all slides to GitHub to ensure changes are reflected

Write-Host "=== Force updating all slides to GitHub ===" -ForegroundColor Green

# Add all slide files
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html 
git add presentations/day_slides/day_slide_2025_08_22.html
git add presentations/day_slides/day_slide_2025_08_23.html
git add presentations/day_slides/day_slide_2025_08_24.html
git add presentations/day_slides/day_slide_2025_08_27.html

Write-Host "Creating commit to force update..." -ForegroundColor Yellow

git commit -m "fix: Force update all slides to ensure navigation fixes are live

- All slides have controls: true for navigation arrows
- All nav-buttons HTML completely removed
- All quick-access elements hidden
- Slide navigation should work properly on all dates
- Force push to clear any caching issues

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Force pushing to GitHub..." -ForegroundColor Yellow
git push origin main --force

Write-Host "`n=== All slides force updated to GitHub ===" -ForegroundColor Green
Write-Host "GitHub Pages may take 1-2 minutes to reflect changes" -ForegroundColor Yellow