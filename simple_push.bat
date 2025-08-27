@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo === Simple GitHub Push (Clean Approach) ===

echo.
echo === Adding .gitignore for large files ===
echo # Claude cache files >> .gitignore
echo .serena/ >> .gitignore
echo *.pkl >> .gitignore

echo.
echo === Adding essential files only ===
git add .gitignore
git add presentations/index.html
git add presentations/day_slides/day_slide_2025_08_27.html
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_22.html

echo.
echo === Creating clean commit ===
git commit -m "feat: Daily AI News integration and slide recreation - Add Daily AI News page to dashboard with 75 articles - Fix navigation button overlap across all slides - Recreate broken slides: 8/27 NEC AI, 8/19 DeepSeek V3.1, 8/20 Google Pixel 10, 8/22 Neo AI - Add keyboard shortcut D for Daily News - Fix character encoding issues"

echo.
echo === Pushing to GitHub (clean) ===
git push origin lightweight-main:main --force

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 🎉 SUCCESS! All changes deployed to GitHub!
    echo ✅ Daily AI News integration live
    echo ✅ Navigation button overlaps fixed
    echo ✅ All broken slides recreated
    echo.
    echo 🌐 Access your site at:
    echo https://awano27.github.io/ai-news-site/presentations/
) else (
    echo.
    echo ❌ Push failed. Repository may need manual cleanup.
    echo Please check GitHub repository status.
)

pause