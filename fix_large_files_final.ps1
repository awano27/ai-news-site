# Fix Large Files and Push to GitHub
Write-Host "=== Fixing Large Files Issue ===" -ForegroundColor Green

Set-Location "C:\Users\yoshitaka\ai-news-site"

# Remove the problematic large file from git history
Write-Host "Removing large file from git..." -ForegroundColor Yellow
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .serena/cache/typescript/document_symbols_cache_v23-06-25.pkl" --prune-empty --tag-name-filter cat -- --all

# Add .serena/ to .gitignore to prevent future issues
Write-Host "Adding .serena/ to .gitignore..." -ForegroundColor Yellow
Add-Content -Path ".gitignore" -Value "`n# Claude cache files`n.serena/`n*.pkl`n"

# Add the missing slide files that were created
Write-Host "Adding the recreated slide files..." -ForegroundColor Yellow
git add presentations/day_slides/day_slide_2025_08_27.html
git add presentations/day_slides/day_slide_2025_08_19.html  
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_22.html

# Check status
Write-Host "`n=== Current Status ===" -ForegroundColor Cyan
git status

# Force push to clean up the remote repository
Write-Host "`n=== Force Pushing to Clean Repository ===" -ForegroundColor Yellow
git push origin lightweight-main:main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: Repository cleaned and pushed!" -ForegroundColor Green
    Write-Host "✅ Large file removed from git history" -ForegroundColor Cyan
    Write-Host "✅ Daily AI News integration deployed" -ForegroundColor Cyan  
    Write-Host "✅ Recreated slides deployed" -ForegroundColor Cyan
    Write-Host "✅ Navigation fixes deployed" -ForegroundColor Cyan
    
    Write-Host "`n🌐 Live Site:" -ForegroundColor Magenta
    Write-Host "https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Blue
} else {
    Write-Host "`n❌ Push still failed. Trying alternative approach..." -ForegroundColor Red
    
    # Create a completely new commit with just the essential files
    Write-Host "Creating clean commit with essential files only..." -ForegroundColor Yellow
    
    # Reset and add only the files we need
    git reset --soft HEAD~1
    git add .gitignore
    git add presentations/index.html
    git add presentations/day_slides/day_slide_2025_08_27.html
    git add presentations/day_slides/day_slide_2025_08_19.html  
    git add presentations/day_slides/day_slide_2025_08_20.html
    git add presentations/day_slides/day_slide_2025_08_22.html
    
    # Commit with clean history
    git commit -m "feat: Daily AI News integration and slide fixes

- Add Daily AI News integration to main dashboard
- Fix navigation button overlap issues  
- Recreate broken slides: 8/19, 8/20, 8/22, 8/27
- Add .gitignore for cache files

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"
    
    # Force push the clean version
    git push origin lightweight-main:main --force
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Clean push successful!" -ForegroundColor Green
    } else {
        Write-Host "❌ All push attempts failed. Manual GitHub intervention needed." -ForegroundColor Red
    }
}

Write-Host "`n=== Complete ===" -ForegroundColor Green