@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Pushing 9/2 slide to GitHub...

git push origin main

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: 9/2 slide deployed!
    echo.
    echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
    echo.
    echo The slide should be available in 2-3 minutes.
) else (
    echo Push failed
)

pause