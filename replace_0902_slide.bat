@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Replacing 9/2 slide with clean version...

copy /Y presentations\day_slides\day_slide_2025_09_02_clean.html presentations\day_slides\day_slide_2025_09_02.html

if %errorlevel% equ 0 (
    echo File replaced successfully.
    echo.
    echo Adding to git...
    git add presentations/day_slides/day_slide_2025_09_02.html
    
    echo Committing...
    git commit -m "fix(9/2): replace with completely clean HTML slide"
    
    echo Pushing to GitHub...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: Clean 9/2 slide deployed!
        echo.
        echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
        echo.
        echo Wait 2-3 minutes for GitHub Pages to update.
    ) else (
        echo Push failed
    )
) else (
    echo File copy failed
)

pause