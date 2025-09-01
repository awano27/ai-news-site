@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo 🔄 8/31スライド（ローテーション機能なし）をデプロイ中...

git add presentations/day_slides/day_slide_2025_08_31.html

git commit -m "feat(8/31): remove auto-rotation functionality, keep clickable source links

🎯 Master Prompt Practical Guide - Final Version:
- Removed smart rotation panel and controls as requested
- Maintained clickable source links for academic credibility
- Preserved keyboard navigation shortcuts (H/R/M/ESC)

🔗 Clickable Sources Maintained:
- Lakera AI: Prompt Engineering Ultimate Guide 2025
- OpenAI: Official Best Practices Documentation  
- Tiago Forte: Master Prompt Method Framework
- Georgios Xenakis: Meta-prompt Methodology

⌨️ Keyboard Navigation:
- H: Navigate to day_slides_index.html
- R: Navigate to ai_ranking_interactive.html  
- M: Navigate to integrated_report.html
- Escape: Go back in browser history

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

if %errorlevel% equ 0 (
    echo.
    echo 📤 GitHubにプッシュ中...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ 8/31スライド（最終版）がLIVEになりました！
        echo.
        echo 🌐 更新されたスライド:
        echo    https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_31.html
        echo.
        echo 🔗 ソースリンク機能:
        echo    📄 Lakera AI, OpenAI, Tiago Forte, Georgios Xenakis
        echo.
        echo ⌨️ キーボードナビゲーション:
        echo    H = ホーム ^| R = ランキング ^| M = メインレポート ^| ESC = 戻る
        echo.
        echo ✨ 自動ローテーション機能は削除されました！
    ) else (
        echo.
        echo ❌ プッシュに失敗しました。エラーを確認してください。
    )
) else (
    echo.
    echo ❌ コミットに失敗しました。エラーを確認してください。
)

pause