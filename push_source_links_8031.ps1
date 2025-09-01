Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🔗 Adding clickable source links to 8/31 slide..." -ForegroundColor Cyan

git add presentations/day_slides/day_slide_2025_08_31.html

git commit -m "feat(8/31): add clickable source links and navigation shortcuts

🔗 Clickable Source Links Added:
- Lakera AI: Prompt Engineering Ultimate Guide 2025
- OpenAI: Official Best Practices Documentation  
- Tiago Forte: Master Prompt Method Framework
- Georgios Xenakis: Meta-prompt Methodology (Medium)

🎨 Link Styling (matching 8/27 template):
- Purple button design with practical-color theme
- Hover effects and responsive layout
- Clear labeling with 📄 icons for external resources
- target='_blank' for new tab opening

⌨️ Keyboard Navigation (matching 8/27 functionality):
- H: Navigate to day_slides_index.html
- R: Navigate to ai_ranking_interactive.html  
- M: Navigate to integrated_report.html
- Escape: Go back in browser history
- Home/End/PageUp/PageDown: Scroll navigation

🎯 User Experience Improvements:
- Direct access to source materials for verification
- Consistent navigation pattern across all daily slides  
- Professional presentation with academic-level sourcing
- Enhanced credibility with clickable references

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host ""
Write-Host "📤 Pushing source link enhancements to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ 8/31 slide with clickable source links is now LIVE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Enhanced slide:" -ForegroundColor Cyan
    Write-Host "   https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_31.html" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔗 Clickable Sources:" -ForegroundColor Magenta
    Write-Host "   📄 Lakera AI - https://www.lakera.ai/blog/prompt-engineering-guide" -ForegroundColor White
    Write-Host "   📄 OpenAI - https://help.openai.com/en/articles/6654000-best-practices..." -ForegroundColor White
    Write-Host "   📄 Tiago Forte - https://www.geeky-gadgets.com/the-master-prompt-method..." -ForegroundColor White
    Write-Host "   📄 Georgios Xenakis - https://medium.com/@xenakis_disconnected/..." -ForegroundColor White
    Write-Host ""
    Write-Host "⌨️ Keyboard Navigation:" -ForegroundColor Magenta
    Write-Host "   H = Home (Slides Index) | R = Ranking | M = Main Report | ESC = Back" -ForegroundColor White
    Write-Host ""
    Write-Host "✨ Now matches 8/27 template with full source accessibility!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Check error above." -ForegroundColor Red
}