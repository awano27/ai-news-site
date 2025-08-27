# Fix GitHub Pages build by removing node_modules from git history
Write-Host "Removing node_modules from git tracking..." -ForegroundColor Yellow

# Remove node_modules from git cache
git rm -r --cached frontend/node_modules/ 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "node_modules not in git cache (already clean)" -ForegroundColor Green
}

# Stage the .gitignore and _config.yml files
git add .gitignore
git add _config.yml

# Check status
Write-Host "Current git status:" -ForegroundColor Cyan
git status --porcelain

# Create commit
$commitMessage = @"
fix: Configure Jekyll for GitHub Pages deployment

- Add .gitignore to exclude node_modules and build files  
- Add _config.yml with proper Jekyll configuration
- Remove node_modules from git tracking
- Configure GitHub Pages to serve presentations/ directory

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
"@

git commit -m $commitMessage

Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push origin main

Write-Host "GitHub Pages configuration complete!" -ForegroundColor Green
Write-Host "Site should be available at: https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Cyan