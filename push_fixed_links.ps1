# PowerShell script to push fixed 9/1 slide links
Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🚀 Pushing fixed source links to GitHub..." -ForegroundColor Green

try {
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ ソースリンク修正版がデプロイ完了！" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 更新されたスライド:" -ForegroundColor Cyan
        Write-Host "   https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html"
        Write-Host ""
        Write-Host "🔗 修正されたソースリンク:" -ForegroundColor Yellow
        Write-Host "   📱 X投稿（510+いいね）"
        Write-Host "   🌐 公式サイト（aicaretoc.io）"  
        Write-Host "   📄 Medium記事（詳細解説）"
        Write-Host "   📰 Naverニュース（韓国報道）"
        Write-Host ""
        Write-Host "✨ 全てのリンクがクリック可能になりました！" -ForegroundColor Green
        Write-Host "💡 ホバーエフェクトも追加済み" -ForegroundColor Magenta
        Write-Host ""
        Write-Host "🕐 数分後にGitHub Pagesで反映されます" -ForegroundColor Blue
    } else {
        Write-Host "❌ プッシュに失敗しました。" -ForegroundColor Red
        Write-Host "GitHub Desktopで手動プッシュしてください。" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ エラーが発生しました: $($_.Exception.Message)" -ForegroundColor Red
}

Read-Host "続行するには何かキーを押してください"