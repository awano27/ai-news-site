@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Checking current git status...
git status --short

echo.
echo Adding and committing 9/2 slide directly...
git add presentations/day_slides/day_slide_2025_09_02.html
git commit -m "fix(9/2): replace with working HTML slide"

echo.
echo Force pushing to GitHub...
git push --force origin main

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Force pushed to GitHub!
    echo.
    echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
    echo.
    echo Give it 2-3 minutes to update on GitHub Pages.
) else (
    echo Force push failed
)

pause