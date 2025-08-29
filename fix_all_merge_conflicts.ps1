# PowerShell script to fix all merge conflict markers in slide files
Write-Host "=== Fixing All Merge Conflict Markers ===" -ForegroundColor Green

# List of all files with merge conflicts
$conflictFiles = @(
    "presentations/day_slides/day_slide_2025_08_24.html",
    "presentations/day_slides/day_slide_2025_08_23.html", 
    "presentations/day_slides/day_slide_2025_08_08.html",
    "presentations/day_slides/day_slide_2025_08_26.html",
    "presentations/day_slides/day_slide_2025_08_22.html",
    "presentations/day_slides/day_slide_2025_08_20.html",
    "presentations/day_slides/day_slide_2025_08_19.html",
    "presentations/day_slides/day_slide_2025_08_17.html",
    "presentations/day_slides/day_slide_2025_08_16.html",
    "presentations/day_slides/day_slide_2025_08_15.html",
    "presentations/day_slides/day_slide_2025_08_14.html",
    "presentations/day_slides/day_slide_2025_08_13.html",
    "presentations/day_slides/day_slide_2025_08_12.html",
    "presentations/day_slides/day_slide_2025_08_11.html",
    "presentations/day_slides/day_slide_2025_08_10.html",
    "presentations/day_slides/day_slide_2025_08_09.html",
    "presentations/day_slides/day_slide_2025_08_06.html",
    "presentations/day_slides/day_slide_2025_08_05.html",
    "presentations/day_slides/day_slide_2025_08_02.html",
    "presentations/day_slides/day_slide_2025_07_30.html"
)

$totalFiles = $conflictFiles.Count
$processedFiles = 0

foreach ($file in $conflictFiles) {
    $processedFiles++
    Write-Host "[$processedFiles/$totalFiles] Processing: $file" -ForegroundColor Yellow
    
    if (Test-Path $file) {
        # Read file content
        $content = Get-Content $file -Raw -Encoding UTF8
        
        # Remove merge conflict markers
        $cleanContent = $content -replace '<<<<<<< HEAD\r?\n', ''
        $cleanContent = $cleanContent -replace '=======\r?\n', ''
        $cleanContent = $cleanContent -replace '>>>>>>> aa72465003db996b6b1bfc174b8a0b6870dd638a\r?\n', ''
        
        # Fix common character encoding issues in Japanese text
        $cleanContent = $cleanContent -replace 'Estrong>', '<strong>'
        $cleanContent = $cleanContent -replace 'E/strong>', '</strong>'
        $cleanContent = $cleanContent -replace 'E/p>', '</p>'
        $cleanContent = $cleanContent -replace 'E/h4>', '</h4>'
        $cleanContent = $cleanContent -replace '絁E��', '組み'
        $cleanContent = $cleanContent -replace '�E析', '分析'
        $cleanContent = $cleanContent -replace '唁E��', 'します'
        $cleanContent = $cleanContent -replace 'E��', ''
        $cleanContent = $cleanContent -replace '劁E', ''
        $cleanContent = $cleanContent -replace 'ぁE', ''
        
        # Write cleaned content back
        Set-Content -Path $file -Value $cleanContent -Encoding UTF8
        Write-Host "  ✅ Fixed: $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ File not found: $file" -ForegroundColor Red
    }
}

Write-Host "`n=== Verification ===" -ForegroundColor Cyan
Write-Host "Checking for remaining conflict markers..." -ForegroundColor Yellow

$remainingConflicts = 0
foreach ($file in $conflictFiles) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        if ($content -match '=======|>>>>>>>|<<<<<<<') {
            $remainingConflicts++
            Write-Host "❌ Still has conflicts: $file" -ForegroundColor Red
        }
    }
}

if ($remainingConflicts -eq 0) {
    Write-Host "✅ All conflict markers removed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ $remainingConflicts files still have conflict markers" -ForegroundColor Red
}

Write-Host "`n=== Git Operations ===" -ForegroundColor Cyan
Write-Host "Adding all fixed files..." -ForegroundColor Yellow

# Add all fixed files to git
foreach ($file in $conflictFiles) {
    git add $file
}

Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "fix: Remove merge conflict markers from all daily slides

- Clean up merge conflict markers from 20 slide files
- Fix character encoding issues in Japanese text
- Restore proper slide content structure  
- Ensure all slides display correctly on GitHub Pages

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push origin lightweight-main

Write-Host "Updating main branch..." -ForegroundColor Yellow  
git push origin lightweight-main:main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: All slides fixed and pushed to GitHub!" -ForegroundColor Green
    Write-Host "GitHub Pages URL: https://awano27.github.io/ai-news-site/" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Push failed. Check the output above." -ForegroundColor Red
}

Write-Host "`n=== Operation Complete ===" -ForegroundColor Green