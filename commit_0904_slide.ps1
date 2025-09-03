# PowerShell script to commit 9/4 slide
cd "C:\Users\yoshitaka\ai-news-site"

# Add the slide file
git add presentations/day_slides/day_slide_2025_09_04.html

# Check status
Write-Host "=== Git Status ==="
git status

# Commit with message
git commit -m @"
feat(9/4): add Gaia AI Phone slide - world's first on-device AI smartphone

- Complete slide with privacy-focused features and Web3 integration
- Comprehensive technical specs and implementation guide
- Business use cases for PDM/CS workflows
- Total score: 90.5/100 with breakdown
- Links to official resources and documentation

🤖 Generated with Claude Code
"@

Write-Host "=== Commit completed ==="

# Push to GitHub
git push origin main

Write-Host "=== Push completed ==="