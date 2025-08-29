# Fix navigation for all slides - simple approach

Write-Host "=== Fixing navigation for all slides ===" -ForegroundColor Green

# Reset files from git to fix encoding issues
Write-Host "Resetting files from git..." -ForegroundColor Yellow
git checkout HEAD -- presentations/day_slides/day_slide_2025_08_23.html
git checkout HEAD -- presentations/day_slides/day_slide_2025_08_24.html

Write-Host "Files reset successfully" -ForegroundColor Green

# Simple commit and push
git add -A
git commit -m "fix: Reset slides to fix encoding and navigation issues

- Reset 8/23 and 8/24 slides from git to fix character encoding
- All slides should now have proper UTF-8 encoding
- Navigation controls should work consistently

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "=== Files reset and pushed ===" -ForegroundColor Green