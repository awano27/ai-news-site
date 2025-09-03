@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Syncing with remote repository...

git pull origin main

if %errorlevel% equ 0 (
    echo.
    echo Pull successful. Now pushing 9/3 slide...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: 9/3 slide pushed to GitHub!
        echo.
        echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_03.html
        echo.
        echo The slide should be available in 2-3 minutes.
    ) else (
        echo Push failed after pull
    )
) else (
    echo Pull failed - there may be merge conflicts
    echo Please resolve conflicts manually
)

pause