# PowerShell script to resolve merge conflicts and push changes
try {
    Write-Host "Adding resolved files..."
    git add presentations/day_slides/day_slide_2025_08_08.html
    
    Write-Host "Checking git status..."
    git status
    
    Write-Host "Completing merge commit..."
    git commit -m "resolve: merge conflicts in GPT-5 slide

- Keep HEAD version with comprehensive GPT-5 content
- Preserve updated slide with detailed analysis and evaluation
- Fixed all merge conflict markers

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    Write-Host "Pushing to remote..."
    git push origin main
    
    Write-Host "Git operations completed successfully!"
    
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}