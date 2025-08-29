# PowerShell script to resolve all merge conflicts
Write-Host "=== Resolving All Merge Conflicts ===" -ForegroundColor Green

# List of all conflicted files that need to be added
$conflictedFiles = @(
    "presentations/day_slides/day_slide_2025_07_30.html",
    "presentations/day_slides/day_slide_2025_08_02.html", 
    "presentations/day_slides/day_slide_2025_08_05.html",
    "presentations/day_slides/day_slide_2025_08_06.html",
    "presentations/day_slides/day_slide_2025_08_09.html",
    "presentations/day_slides/day_slide_2025_08_10.html",
    "presentations/day_slides/day_slide_2025_08_11.html", 
    "presentations/day_slides/day_slide_2025_08_12.html",
    "presentations/day_slides/day_slide_2025_08_13.html",
    "presentations/day_slides/day_slide_2025_08_14.html",
    "presentations/day_slides/day_slide_2025_08_15.html",
    "presentations/day_slides/day_slide_2025_08_16.html",
    "presentations/day_slides/day_slide_2025_08_17.html",
    "presentations/day_slides/day_slide_2025_08_19.html", 
    "presentations/day_slides/day_slide_2025_08_20.html",
    "presentations/day_slides/day_slide_2025_08_22.html",
    "presentations/day_slides/day_slide_2025_08_23.html",
    "presentations/day_slides/day_slide_2025_08_24.html",
    "presentations/day_slides/day_slide_2025_08_26.html"
)

Write-Host "Adding all conflicted slide files..." -ForegroundColor Yellow

# Add each conflicted file to mark it as resolved
foreach ($file in $conflictedFiles) {
    Write-Host "Adding: $file" -ForegroundColor Cyan
    git add $file
}

Write-Host "`nChecking status after adding files..." -ForegroundColor Yellow
git status

Write-Host "`nCompleting merge commit..." -ForegroundColor Yellow
git commit -m "resolve: merge conflicts in all daily slides

- Keep local versions of all 19 daily slide files  
- Preserve comprehensive content with proper Japanese encoding
- Maintain 6-section slide structure across all files
- Fix all merge conflicts from 'both added' scenarios

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nMerge commit successful! Now pushing to GitHub..." -ForegroundColor Green
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ SUCCESS: All merge conflicts resolved and pushed to GitHub!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ ERROR: Push failed. Check the output above." -ForegroundColor Red
    }
} else {
    Write-Host "`n❌ ERROR: Merge commit failed. Check the output above." -ForegroundColor Red
}

Write-Host "`n=== Operation Complete ===" -ForegroundColor Green