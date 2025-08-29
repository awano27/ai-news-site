# PowerShell script to completely remove large file from Git history
Write-Host "=== Removing Large File from Git History ===" -ForegroundColor Green

# Step 1: Use git filter-branch to remove the problematic file from ALL commits
Write-Host "Removing large cache file from entire Git history..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Cyan

git filter-branch --force --index-filter "git rm --cached --ignore-unmatch '.serena/cache/typescript/document_symbols_cache_v23-06-25.pkl'" --prune-empty --tag-name-filter cat -- --all

# Step 2: Remove the original refs (backup references)
Write-Host "Cleaning up backup references..." -ForegroundColor Yellow
git for-each-ref --format="%(refname)" refs/original/ | ForEach-Object { git update-ref -d $_ }

# Step 3: Expire all reflogs
Write-Host "Expiring reflogs..." -ForegroundColor Yellow
git reflog expire --expire=now --all

# Step 4: Aggressive garbage collection
Write-Host "Running garbage collection..." -ForegroundColor Yellow
git gc --prune=now --aggressive

# Step 5: Check repository size
Write-Host "`nRepository size after cleanup:" -ForegroundColor Green
$repoSize = (Get-ChildItem -Recurse .git | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "$([math]::Round($repoSize, 2)) MB" -ForegroundColor Cyan

# Step 6: Verify the file is gone
Write-Host "`nVerifying large file removal..." -ForegroundColor Yellow
$largeFiles = git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | Where-Object { $_ -match "blob" -and ([int]($_.Split(' ')[2]) -gt 100000000) }

if ($largeFiles) {
    Write-Host "❌ Large files still found:" -ForegroundColor Red
    $largeFiles | ForEach-Object { Write-Host $_ -ForegroundColor Red }
} else {
    Write-Host "✅ No large files found in repository!" -ForegroundColor Green
}

# Step 7: Try to push
Write-Host "`nAttempting to push to GitHub..." -ForegroundColor Green
git push origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ SUCCESS: Repository pushed to GitHub successfully!" -ForegroundColor Green
    Write-Host "🎉 All slide files including the updated GPT-5 slide are now on GitHub!" -ForegroundColor Green
    Write-Host "`nGitHub Pages URL: https://awano27.github.io/ai-news-site/" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Push failed. Additional steps needed." -ForegroundColor Red
    Write-Host "Repository size may still be too large or other issues exist." -ForegroundColor Yellow
    Write-Host "`nTry checking:" -ForegroundColor Yellow
    Write-Host "git log --oneline -5" -ForegroundColor Cyan
    Write-Host "git ls-files | xargs ls -la | sort -k5 -nr | head -20" -ForegroundColor Cyan
}

Write-Host "`n=== Operation Complete ===" -ForegroundColor Green