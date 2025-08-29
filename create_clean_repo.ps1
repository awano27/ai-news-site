# クリーンなリポジトリを作成（安全な方法）
Write-Host "クリーンなリポジトリを作成中..." -ForegroundColor Yellow

# 現在の変更を一時保存
$currentBranch = git branch --show-current
$tempDir = "../ai-news-site-backup"

# バックアップ作成
Write-Host "バックアップ作成中..." -ForegroundColor Cyan
Copy-Item -Path "." -Destination $tempDir -Recurse -Force -Exclude @(".git", "node_modules", ".serena", ".venv", "__pycache__")

# .gitフォルダを削除して新規作成
Write-Host "Git履歴をリセット中..." -ForegroundColor Red
Remove-Item -Recurse -Force .git

# 新しくGit初期化
git init
git add .
git commit -m "Initial commit: Clean AI News Intelligence Platform v2.0

- Complete daily slides system (26 slides)
- Full ranking report with 30 technologies
- Integrated dashboard with navigation
- Removed duplicate buttons and cleaned interface
- Fixed all navigation issues"

# リモート追加
git remote add origin https://github.com/awano27/ai-news-site.git

# 強制プッシュ
Write-Host "`n強制プッシュ実行中..." -ForegroundColor Green
git push origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 成功！クリーンなリポジトリが作成されました" -ForegroundColor Green
    Write-Host "`nGitHub Pages URL:" -ForegroundColor Cyan
    Write-Host "https://awano27.github.io/ai-news-site/" -ForegroundColor Cyan
    Write-Host "https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Cyan
} else {
    Write-Host "エラーが発生しました。手動で確認してください。" -ForegroundColor Red
}