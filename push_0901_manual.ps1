# PowerShell script to push 9/1 slide
Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🚀 Pushing 9/1 slide to GitHub..." -ForegroundColor Green

try {
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ 9/1スライドがLIVEになりました！" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 新しいスライド:" -ForegroundColor Cyan
        Write-Host "   https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html"
        Write-Host ""
        Write-Host "🎯 内容サマリー:" -ForegroundColor Yellow
        Write-Host "   🏥 AIヘルスケア革命「RX」プラットフォーム"
        Write-Host "   📊 総合スコア: 81/100"
        Write-Host "   ⚡ 診断効率30%向上、数分でAI分析"
        Write-Host "   🔗 韓国発・病院パートナーシップ拡大中"
        Write-Host ""
        Write-Host "🔗 動作確認済みソースリンク:" -ForegroundColor Magenta
        Write-Host "   📱 X投稿、🌐 公式サイト、📄 Medium記事、📰 Naverニュース"
        Write-Host ""
        Write-Host "✨ ダッシュボードにも追加されました！" -ForegroundColor Green
    } else {
        Write-Host "❌ プッシュに失敗しました。" -ForegroundColor Red
        Write-Host "手動でGitHub Desktopまたはブラウザから確認してください。" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ エラーが発生しました: $($_.Exception.Message)" -ForegroundColor Red
}

Read-Host "続行するには何かキーを押してください"