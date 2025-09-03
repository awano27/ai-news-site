@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Checking merge status...
git status

echo.
echo Completing merge without editor...
git commit --no-edit -m "Merge remote changes and add 9/3 slide"

if %errorlevel% equ 0 (
    echo.
    echo Merge completed. Now pushing...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: All changes pushed to GitHub!
        echo.
        echo 9/3 slide URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_03.html
        echo.
        echo The slide should be available in 2-3 minutes.
    ) else (
        echo Push failed
    )
) else (
    echo Merge commit failed
    echo Run: git status
    echo to see if there are conflicts to resolve
)

pause