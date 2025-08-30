Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "Adding 08/28 slide..." -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_28.html

Write-Host "Committing new slide..." -ForegroundColor Cyan
git commit -m "feat: Add 08/28 slide - OpenAI Codex revolutionary update

- Created comprehensive slide about OpenAI Codex major update
- Features GPT-5 foundation with IDE integration and cloud connectivity  
- Impact score: 95pt (highest level for developer tools)
- Applied perfect 08/27 template with scrolling CSS and responsive design
- Includes installation guide, comparison table, and KPI analysis

Content highlights:
- GPT-5 outperforms Claude 4 Sonnet in benchmarks
- IDE extensions for VS Code, Cursor, Windsurf
- GitHub code review with @codex mention
- Cost efficiency: 1/7 of Claude Code
- Immediate productivity boost for engineers and business users

Template features:
- Perfect scrolling behavior (no slide transitions)
- Mobile-optimized responsive design
- iOS touch scrolling optimization
- Consistent styling with all other slides

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing to origin main..." -ForegroundColor Yellow
git push origin main

Write-Host "✅ 08/28 slide successfully added!" -ForegroundColor Green