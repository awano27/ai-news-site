# Git push script
Write-Host "GitHubへのプッシュを開始..." -ForegroundColor Green

# 1. 現在の状態を確認
Write-Host "`n現在の変更を確認中..." -ForegroundColor Yellow
git status

# 2. すべての変更をステージング
Write-Host "`nすべての変更をステージング..." -ForegroundColor Yellow
git add -A

# 3. コミット作成
Write-Host "`nコミットを作成..." -ForegroundColor Yellow
git commit -m "fix: Daily Slides improvements and character encoding fixes

- Added missing Sources and Navigation sections to all 26 daily slides
- Fixed character encoding issues in multiple slide files
- Each slide now has proper 6-section structure
- Added keyboard shortcuts for navigation
- Fixed GPT-5 slide text corruption issue

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# 4. GitHubへプッシュ
Write-Host "`nGitHubへプッシュ中..." -ForegroundColor Green
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 成功！GitHubへのプッシュが完了しました" -ForegroundColor Green
    Write-Host "`nGitHub Pages URL:" -ForegroundColor Cyan
    Write-Host "https://awano27.github.io/ai-news-site/" -ForegroundColor Green
    Write-Host "https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Green
} else {
    Write-Host "`n❌ エラーが発生しました" -ForegroundColor Red
}