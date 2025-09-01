@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo 🏥 9/1スライド「AIヘルスケア革命RX」をデプロイ中...

git add presentations/day_slides/day_slide_2025_09_01.html presentations/index.html

git commit -m "feat(9/1): launch AIヘルスケア革命「RX」プラットフォーム slide

🏥 AI CareToc Operator LabsWisenet - RX Platform Analysis:
- Revolutionary AI-powered precision nutrition healthcare platform
- Comprehensive slide covering technical implementation and business impact
- Real-world use cases for PDM, CS, and healthcare consultants
- Market impact analysis with 81/100 total score
- Working clickable source links to all official sources

🎯 Content Highlights:
- 30% diagnostic efficiency improvement
- Minutes-fast AI analysis vs hours of manual work  
- Immediate platform availability with hospital partnerships
- API integration examples with Python SDK
- Complete risk assessment and security considerations

🔗 Verified Sources:
- X/Twitter official post with 510+ likes
- Official website: aicaretoc.io
- Medium technical article
- Naver News Korean coverage

📱 Dashboard Updates:
- Added 9/1 slide to Quick Access panel with 🏥 icon
- Positioned as latest slide at top of chronological list
- Maintains keyboard navigation (H/R/M/ESC shortcuts)

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

if %errorlevel% equ 0 (
    echo.
    echo 📤 GitHubにプッシュ中...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ 9/1スライドがLIVEになりました！
        echo.
        echo 🌐 新しいスライド:
        echo    https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html
        echo.
        echo 🎯 内容サマリー:
        echo    🏥 AIヘルスケア革命「RX」プラットフォーム
        echo    📊 総合スコア: 81/100
        echo    ⚡ 診断効率30%向上、数分でAI分析
        echo    🔗 韓国発・病院パートナーシップ拡大中
        echo.
        echo 🔗 動作確認済みソースリンク:
        echo    📱 X投稿、🌐 公式サイト、📄 Medium記事、📰 Naverニュース
        echo.
        echo ✨ ダッシュボードにも追加されました！
    ) else (
        echo.
        echo ❌ プッシュに失敗しました。エラーを確認してください。
    )
) else (
    echo.
    echo ❌ コミットに失敗しました。エラーを確認してください。
)

pause