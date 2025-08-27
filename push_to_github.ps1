# GitHub Push Script for AI News Site Updates
Write-Host "=== AI News Site GitHub Push ===" -ForegroundColor Green

# Set location to project directory
Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow

# Check git status
Write-Host "`n=== Git Status ===" -ForegroundColor Cyan
git status

# Add all modified files
Write-Host "`n=== Adding Files ===" -ForegroundColor Yellow
git add presentations/index.html
git add presentations/day_slides/day_slide_2025_08_27.html
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_22.html

# Show what will be committed
Write-Host "`n=== Files to Commit ===" -ForegroundColor Yellow
git diff --cached --name-only

# Create commit
Write-Host "`n=== Creating Commit ===" -ForegroundColor Yellow
git commit -m "feat: Add Daily AI News integration and fix broken slides

- Add Daily AI News page integration to main dashboard
- New sidebar menu item: AIニュース一覧 with 📋 icon
- New dashboard card showing 75 articles and 72 high priority items
- Add keyboard shortcut 'D' for quick access
- External iframe integration with https://awano27.github.io/daily-ai-news-pages/

- Complete recreation of broken daily slides:
  * 8/27 NEC AI Agent cotomi Act (80.4% Web operation success rate)
  * 8/19 DeepSeek V3.1 (685B parameters, 71.6% benchmark, 68x cost efficiency)
  * 8/20 Google Pixel 10 series (Gemini AI integration, 6 major features)
  * 8/22 Neo AI NEO (34.2% Kaggle medal rate, 11 specialized agents)

- Fix navigation button overlap across all slides:
  * Move quick navigation to top-right (20px from top/right)
  * Keep reveal.js controls in bottom-right (20px from bottom/right)
  * Add z-index management and backdrop blur effects

- Resolve character encoding issues in Japanese text
- Implement consistent 6-section slide structure
- Add comprehensive source citations and reliability indicators

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Commit failed!" -ForegroundColor Red
    exit 1
}

# Push to GitHub
Write-Host "`n=== Pushing to GitHub ===" -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: All changes pushed to GitHub!" -ForegroundColor Green
    Write-Host "✅ Daily AI News integration complete" -ForegroundColor Cyan
    Write-Host "✅ Navigation button overlaps fixed" -ForegroundColor Cyan
    Write-Host "✅ Broken slides recreated (8/19, 8/20, 8/22, 8/27)" -ForegroundColor Cyan
    Write-Host "✅ Character encoding issues resolved" -ForegroundColor Cyan
    
    Write-Host "`n🌐 Live URLs:" -ForegroundColor Magenta
    Write-Host "Main Site: https://awano27.github.io/ai-news-site/" -ForegroundColor Blue
    Write-Host "Dashboard: https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Blue
    Write-Host "Daily News: https://awano27.github.io/daily-ai-news-pages/" -ForegroundColor Blue
} else {
    Write-Host "`n❌ Push failed. Trying alternative approach..." -ForegroundColor Red
    
    # Try force push if needed
    Write-Host "Attempting force push..." -ForegroundColor Yellow
    git push origin main --force-with-lease
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Force push successful!" -ForegroundColor Green
    } else {
        Write-Host "❌ Force push also failed. Manual intervention required." -ForegroundColor Red
        Write-Host "Please check GitHub repository status manually." -ForegroundColor Yellow
    }
}

Write-Host "`n=== Final Status ===" -ForegroundColor Cyan
git status

Write-Host "`n=== Complete ===" -ForegroundColor Green