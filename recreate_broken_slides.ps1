# Recreate all broken slides with proper UTF-8 encoding

Write-Host "=== Recreating broken slides ===" -ForegroundColor Green

# Reset broken files from git first
Write-Host "Resetting broken files from git..." -ForegroundColor Yellow
git checkout HEAD~3 -- presentations/day_slides/day_slide_2025_08_19.html
git checkout HEAD~3 -- presentations/day_slides/day_slide_2025_08_20.html
git checkout HEAD~3 -- presentations/day_slides/day_slide_2025_08_23.html
git checkout HEAD~3 -- presentations/day_slides/day_slide_2025_08_24.html

Write-Host "Files reset from earlier version" -ForegroundColor Green

# Commit the reset files
git add presentations/day_slides/day_slide_2025_08_*.html
git commit -m "fix: Reset broken slides to earlier clean version

- Reset 8/19, 8/20, 8/23, 8/24 from earlier git version
- Should restore proper UTF-8 encoding
- Will need to update content and navigation separately

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "`n=== Broken slides reset to clean versions ===" -ForegroundColor Green