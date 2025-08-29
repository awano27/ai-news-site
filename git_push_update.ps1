# Updated Git push script for 8/8 GPT-5 slide
Write-Host "8/8 GPT-5スライド更新をGitHubにプッシュします..." -ForegroundColor Green

# 1. リモートの変更を取得
Write-Host "`nリモートの変更を取得中..." -ForegroundColor Yellow
git pull origin main

# 2. 現在の状態を確認
Write-Host "`n現在の変更を確認中..." -ForegroundColor Yellow
git status

# 3. すべての変更をステージング
Write-Host "`nすべての変更をステージング..." -ForegroundColor Yellow
git add -A

# 4. コミット作成
Write-Host "`nコミットを作成..." -ForegroundColor Yellow
git commit -m "update: GPT-5 slide with comprehensive content from 0808.txt

- Updated day_slide_2025_08_08.html with detailed GPT-5 release information
- Fixed all character encoding issues in Japanese text
- Added comprehensive analysis with X engagement data
- Included proper evaluation scores (Engineer 9/10, Business 8/10)
- Added official OpenAI links and social media references
- Enhanced technical details and future roadmap
- Improved reliability indicators with 95% confidence

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# 5. GitHubへプッシュ
Write-Host "`nGitHubへプッシュ中..." -ForegroundColor Green
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 成功！GPT-5スライド更新がGitHubにプッシュされました" -ForegroundColor Green
    Write-Host "`nGitHub Pages URL:" -ForegroundColor Cyan
    Write-Host "https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_08.html" -ForegroundColor Green
    Write-Host "https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Green
    Write-Host "`n更新内容:" -ForegroundColor Cyan
    Write-Host "- 文字化け完全修正" -ForegroundColor White
    Write-Host "- 詳細なGPT-5分析 (X数万エンゲージメント含む)" -ForegroundColor White
    Write-Host "- エンジニア向け9/10点、ビジネス向け8/10点の評価" -ForegroundColor White
    Write-Host "- 公式ソース + SNS参照リンク追加" -ForegroundColor White
    Write-Host "- 将来計画 (GPT-5-mini、128kコンテキスト等)" -ForegroundColor White
} else {
    Write-Host "`n❌ エラーが発生しました" -ForegroundColor Red
    Write-Host "手動で以下を実行してください:" -ForegroundColor Yellow
    Write-Host "git pull origin main" -ForegroundColor Cyan
    Write-Host "git add -A" -ForegroundColor Cyan
    Write-Host "git commit -m `"update: GPT-5 slide improvements`"" -ForegroundColor Cyan
    Write-Host "git push origin main" -ForegroundColor Cyan
}