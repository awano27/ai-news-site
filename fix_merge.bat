@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo 🔧 Completing merge...

git commit -m "Merge remote changes with 9/1 slide"

if %errorlevel% equ 0 (
    echo ✅ Merge completed
    echo 📤 Pushing to GitHub...
    
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ 9/1スライドがLIVEになりました！
        echo.
        echo 🌐 https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html
        echo.
    ) else (
        echo ❌ Push failed
    )
) else (
    echo ❌ Merge failed
)

pause