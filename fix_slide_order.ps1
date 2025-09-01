Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🔧 Fixing slide display order..." -ForegroundColor Cyan

git add presentations/index.html

git commit -m "fix(navigation): correct slide order for 8/28, 8/29, 8/30 display consistency

- Fix slideMap order in presentations/index.html JavaScript
- Ensure chronological order: 8/29 before 8/30 in slideMap
- Resolve display inconsistency between sidebar and navigation
- Maintain proper date-based sorting throughout the platform

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host ""
Write-Host "✅ Slide order fix completed!" -ForegroundColor Green
Write-Host "Now all slides display in consistent chronological order." -ForegroundColor Yellow