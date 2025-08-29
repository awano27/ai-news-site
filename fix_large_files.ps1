# 大きなファイル問題を修正
Write-Host "大きなファイル問題を修正中..." -ForegroundColor Yellow

# .gitignoreに.serenaキャッシュフォルダを追加
Add-Content -Path ".gitignore" -Value "`n# Serena cache files`n.serena/"

# 大きなファイルをGit履歴から完全削除
Write-Host "大きなファイルをGit履歴から削除中..." -ForegroundColor Red
git rm -r --cached .serena/ 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host ".serenaフォルダはすでにGit管理外です" -ForegroundColor Green
}

# 物理的にもファイルを削除（存在する場合）
if (Test-Path ".serena") {
    Write-Host ".serenaフォルダを物理削除中..." -ForegroundColor Red
    Remove-Item -Recurse -Force ".serena"
}

# その他の大きなファイルも除外に追加
$additionalIgnores = @"

# Large cache and temp files
*.pkl
*.cache
*.tmp
*.temp
cache/
.cache/
temp/
.temp/

# IDE and editor caches
.serena/
.vscode/settings.json
.idea/
*.swp
*.swo

# System files
*.db
*.sqlite
*.sqlite3
"@

Add-Content -Path ".gitignore" -Value $additionalIgnores

# 変更をステージング
git add .gitignore

# 現在の状態確認
Write-Host "`n現在のGit状態:" -ForegroundColor Cyan
git status --porcelain

# コミット作成
$commitMessage = @"
fix: Remove large cache files and improve .gitignore

- Remove .serena cache folder (376MB) from Git tracking
- Add comprehensive .gitignore rules for cache/temp files
- Prevent future large file issues

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
"@

git commit -m $commitMessage

Write-Host "`nプッシュ試行中..." -ForegroundColor Green
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ プッシュ成功！" -ForegroundColor Green
} else {
    Write-Host "❌ プッシュ失敗 - 手動確認が必要です" -ForegroundColor Red
    Write-Host "以下を実行してください:" -ForegroundColor Yellow
    Write-Host "git log --oneline -5" -ForegroundColor Cyan
    Write-Host "git push origin main" -ForegroundColor Cyan
}

Write-Host "`nGitHub Pages URL:" -ForegroundColor Green
Write-Host "https://awano27.github.io/ai-news-site/" -ForegroundColor Cyan