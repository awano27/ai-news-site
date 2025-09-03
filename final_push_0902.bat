@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Final push for 9/2 slide...

git add presentations/day_slides/day_slide_2025_09_02.html

git commit -m "fix(9/2): final clean HTML version with working layout"

git push origin main

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: 9/2 slide pushed to GitHub!
    echo.
    echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
    echo.
    echo Please wait 3-5 minutes for GitHub Pages to update, then refresh the page.
    echo The slide contains:
    echo - MiniCPM-V 4.5 mobile AI revolution
    echo - Working source links
    echo - Implementation guide
    echo - Business use cases
) else (
    echo Push failed
)

pause