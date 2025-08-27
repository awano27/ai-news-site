# GitHub Pages直接デプロイ設定
Write-Host "GitHub Pages設定を修正中..." -ForegroundColor Yellow

# GitHub Actionsワークフローを追加
git add .github/workflows/pages.yml

# presentations/index.htmlをルートにコピー（フォールバック）
Copy-Item "presentations/index.html" "index.html" -Force
git add index.html

# コミット
$commitMessage = @"
fix: Add GitHub Actions workflow for Pages deployment

- Add .github/workflows/pages.yml for reliable deployment
- Copy main index.html to root for direct access
- Ensure all presentation files are accessible

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
"@

git commit -m $commitMessage

Write-Host "プッシュ中..." -ForegroundColor Green
git push origin main

Write-Host "完了！以下を確認してください:" -ForegroundColor Green
Write-Host "1. https://github.com/awano27/ai-news-site/settings/pages" -ForegroundColor Cyan  
Write-Host "2. Source を 'GitHub Actions' に変更" -ForegroundColor Cyan
Write-Host "3. https://awano27.github.io/ai-news-site/" -ForegroundColor Cyan