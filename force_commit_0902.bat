@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Checking git status...
git status

echo.
echo Adding file with forced commit...
git add presentations/day_slides/day_slide_2025_09_02.html

echo.
echo Committing with message...
git commit -m "fix(9/2): replace broken slide with working simple HTML version"

if %errorlevel% equ 0 (
    echo.
    echo Commit successful. Now pushing...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: 9/2 slide fixed and deployed!
        echo.
        echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
    ) else (
        echo Push failed
    )
) else (
    echo Commit failed - checking what's wrong
    git diff presentations/day_slides/day_slide_2025_09_02.html
)

pause