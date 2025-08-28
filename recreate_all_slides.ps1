# Recreate all problematic slides using the working 8/27 template

Write-Host "=== Recreating all slides from scratch ===" -ForegroundColor Green

# Replace the old 8/22 with the new one
Move-Item "presentations\day_slides\day_slide_2025_08_22_new.html" "presentations\day_slides\day_slide_2025_08_22.html" -Force
Write-Host "✓ Replaced 8/22 slide with new version" -ForegroundColor Green

Write-Host "`n=== Committing recreated slides ===" -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_22.html

git commit -m "fix: Recreate 8/22 slide from scratch using working template

- Used working 8/27 slide as template
- Clean UTF-8 encoding without character corruption
- Proper reveal.js 4.4.0 with consistent navigation
- Controls enabled with edges layout
- All QuickAccess buttons properly hidden
- Content updated with 8/22 Apple-Google AI collaboration

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "`n=== 8/22 slide recreated successfully ===" -ForegroundColor Green
Write-Host "Testing this slide first before recreating others..." -ForegroundColor Yellow