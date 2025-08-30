Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "Creating deployment trigger..." -ForegroundColor Green

# Create or update a small file to trigger deployment
$deployTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$content = @"
# Deployment Trigger

Last deployment triggered: $deployTime

This file is used to trigger GitHub Pages deployment when needed.
"@

Set-Content -Path ".github/deploy_trigger.md" -Value $content -Encoding UTF8

Write-Host "Adding trigger file..." -ForegroundColor Yellow
git add .github/deploy_trigger.md

Write-Host "Committing deployment trigger..." -ForegroundColor Cyan
git commit -m "deploy: Trigger GitHub Pages deployment

- Re-trigger deployment for 08/28 slide
- Previous deployment was cancelled due to priority conflict
- Ensure all slides are properly deployed to GitHub Pages

Generated with Claude Code"

Write-Host "Pushing deployment trigger..." -ForegroundColor Green
git push origin main

Write-Host "✅ Deployment trigger pushed! Check GitHub Actions." -ForegroundColor Green