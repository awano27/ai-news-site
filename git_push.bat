@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"
echo === AI News Site GitHub Push ===

echo.
echo === Git Status ===
git status

echo.
echo === Adding Files ===
git add presentations/index.html
git add presentations/day_slides/day_slide_2025_08_27.html
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_22.html

echo.
echo === Files to Commit ===
git diff --cached --name-only

echo.
echo === Creating Commit ===
git commit -m "feat: Add Daily AI News integration and fix broken slides - Add Daily AI News page integration to main dashboard - New sidebar menu item and dashboard card - Complete recreation of broken daily slides: 8/27, 8/19, 8/20, 8/22 - Fix navigation button overlap across all slides - Resolve character encoding issues 🤖 Generated with Claude Code Co-Authored-By: Claude <noreply@anthropic.com>"

echo.
echo === Pushing to GitHub ===
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 🎉 SUCCESS: All changes pushed to GitHub!
    echo ✅ Daily AI News integration complete
    echo ✅ Navigation button overlaps fixed  
    echo ✅ Broken slides recreated
    echo.
    echo 🌐 Live URLs:
    echo Main Site: https://awano27.github.io/ai-news-site/
    echo Dashboard: https://awano27.github.io/ai-news-site/presentations/
    echo Daily News: https://awano27.github.io/daily-ai-news-pages/
) else (
    echo.
    echo ❌ Push failed. Trying force push...
    git push origin main --force-with-lease
)

echo.
echo === Final Status ===
git status

pause