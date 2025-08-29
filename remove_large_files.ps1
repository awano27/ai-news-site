# Git履歴から大きなファイルを完全に削除
Write-Host "Git履歴から大きなファイルを完全削除中..." -ForegroundColor Yellow

# まず現在のブランチ状態を保存
git stash

# .serenaフォルダをGit履歴から完全削除（BFG代替手法）
Write-Host "Git filter-branchで履歴クリーニング中..." -ForegroundColor Red
git filter-branch --force --index-filter `
  "git rm -r --cached --ignore-unmatch .serena/" `
  --prune-empty --tag-name-filter cat -- --all

# リモートの参照を更新
Write-Host "リモート参照を更新中..." -ForegroundColor Cyan
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin

# ガベージコレクション実行
Write-Host "ガベージコレクション実行中..." -ForegroundColor Cyan
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# stashを復元
git stash pop 2>$null

# 強制プッシュ
Write-Host "`n強制プッシュ実行中..." -ForegroundColor Green
git push origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ プッシュ成功！" -ForegroundColor Green
    Write-Host "`nGitHub Pages URL:" -ForegroundColor Cyan
    Write-Host "https://awano27.github.io/ai-news-site/" -ForegroundColor Cyan
    Write-Host "https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Cyan
} else {
    Write-Host "❌ まだエラーがあります" -ForegroundColor Red
    Write-Host "以下を手動実行してください:" -ForegroundColor Yellow
    Write-Host "git push origin main --force-with-lease" -ForegroundColor Cyan
}