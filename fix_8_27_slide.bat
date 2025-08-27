@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo === Adding 8/27 Slide to Navigation ===

echo.
echo === Adding modified files ===
git add presentations/index.html

echo.
echo === Creating commit ===
git commit -m "fix: Add missing 8/27 NEC AI Agent slide to navigation

- Add 8/27 slide to sidebar DAILY SLIDES section
- Add 8/27 entry to slideMap for proper routing
- Add 8/27 to Quick Access panel
- Update All Slides count from 26 to 27
- 8/27 slide: NEC AI Agent cotomi Act (80.4%% Web operation success rate)

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"

echo.
echo === Pushing to GitHub ===
git push origin lightweight-main:main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 🎉 SUCCESS: 8/27 slide navigation fixed!
    echo ✅ 8/27 NEC AI Agent slide now accessible
    echo ✅ Sidebar menu updated
    echo ✅ Quick Access panel updated
    echo.
    echo 🌐 Test the 8/27 slide at:
    echo https://awano27.github.io/ai-news-site/presentations/
    echo Click "🤖 8/27 - NEC AI Agent" in the sidebar
) else (
    echo.
    echo ❌ Push failed. Please check the error above.
)

pause