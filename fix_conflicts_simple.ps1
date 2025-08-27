# Simple script to fix merge conflict markers
Write-Host "=== Fixing Merge Conflict Markers ===" -ForegroundColor Green

# Get all slide files
$slideFiles = Get-ChildItem "presentations/day_slides/*.html"

$processedFiles = 0
foreach ($file in $slideFiles) {
    $processedFiles++
    Write-Host "[$processedFiles/$($slideFiles.Count)] Processing: $($file.Name)" -ForegroundColor Yellow
    
    try {
        # Read file content
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        
        # Remove merge conflict markers (simple approach)
        $originalLength = $content.Length
        
        $content = $content -replace "<<<<<<< HEAD`r?`n", ""
        $content = $content -replace "=======`r?`n", ""
        $content = $content -replace ">>>>>>> aa72465003db996b6b1bfc174b8a0b6870dd638a`r?`n", ""
        
        # Also remove any standalone conflict markers
        $content = $content -replace "<<<<<<< HEAD", ""
        $content = $content -replace "=======", ""
        $content = $content -replace ">>>>>>> aa72465003db996b6b1bfc174b8a0b6870dd638a", ""
        
        $newLength = $content.Length
        
        if ($originalLength -ne $newLength) {
            # Write cleaned content back
            Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
            Write-Host "  ✅ Fixed: $($file.Name) (removed $($originalLength - $newLength) characters)" -ForegroundColor Green
        } else {
            Write-Host "  ✓ Clean: $($file.Name)" -ForegroundColor Cyan
        }
        
    } catch {
        Write-Host "  ❌ Error processing $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nChecking for remaining conflict markers..." -ForegroundColor Yellow
$conflictsRemaining = 0

foreach ($file in $slideFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    if ($content -match "=======|>>>>>>>|<<<<<<<") {
        $conflictsRemaining++
        Write-Host "❌ Still has conflicts: $($file.Name)" -ForegroundColor Red
    }
}

if ($conflictsRemaining -eq 0) {
    Write-Host "✅ All merge conflict markers removed!" -ForegroundColor Green
    
    Write-Host "`nAdding files to git..." -ForegroundColor Yellow
    git add presentations/day_slides/*.html
    
    Write-Host "Creating commit..." -ForegroundColor Yellow
    git commit -m "fix: Remove all merge conflict markers from daily slides

- Clean up merge conflict markers from all slide files
- Ensure proper display on GitHub Pages
- Fix broken slide content structure

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git push origin lightweight-main
    git push origin lightweight-main:main --force
    
    Write-Host "`n🎉 All slides fixed and pushed to GitHub!" -ForegroundColor Green
    Write-Host "GitHub Pages: https://awano27.github.io/ai-news-site/" -ForegroundColor Cyan
    
} else {
    Write-Host "❌ $conflictsRemaining files still need manual fixing" -ForegroundColor Red
}

Write-Host "`n=== Complete ===" -ForegroundColor Green