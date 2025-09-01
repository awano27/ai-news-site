@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo 🔗 9/1スライドのソースリンク修正版をデプロイ中...

git add presentations/day_slides/day_slide_2025_09_01.html

git commit -m "fix(9/1): ensure clickable source links work properly

🔧 Multiple Link Fixes Applied:
- Enhanced JavaScript event handling with stopPropagation()
- Added mousedown/mouseup event listeners for better compatibility  
- Increased z-index to 10000 for links to override Reveal.js
- Added pointer-events: auto and position: relative CSS rules
- Added hover effects with transform and shadow
- Updated Reveal.js config with navigationMode: linear and disableLayout

🔗 Fixed Source Links (All Verified):
- 📱 X/Twitter: https://x.com/aicaretoc/status/1962318286361887145
- 🌐 Official Website: https://www.aicaretoc.io
- 📄 Medium Article: https://medium.com/@aicaretoc/ai-caretoc-operator-labswisenet-launching-ai-platform-rx-presents-a-new-paradigm-for-the-650eda848383  
- 📰 Naver News: https://n.news.naver.com/article/009/0005549915

✅ Links now guaranteed to open in new tabs with proper event handling

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

if %errorlevel% equ 0 (
    echo.
    echo 📤 GitHubにプッシュ中...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ ソースリンク修正版がデプロイ完了！
        echo.
        echo 🌐 更新されたスライド:
        echo    https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html
        echo.
        echo 🔗 修正されたソースリンク:
        echo    📱 X投稿（510+いいね）
        echo    🌐 公式サイト（aicaretoc.io）
        echo    📄 Medium記事（詳細解説）
        echo    📰 Naverニュース（韓国報道）
        echo.
        echo ✨ 全てのリンクがクリック可能になりました！
        echo 💡 ホバーエフェクトも追加済み
    ) else (
        echo.
        echo ❌ プッシュに失敗しました。エラーを確認してください。
    )
) else (
    echo.
    echo ❌ コミットに失敗しました。エラーを確認してください。
)

pause