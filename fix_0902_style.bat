@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Replacing 9/2 slide with correct Reveal.js format...

copy /Y presentations\day_slides\day_slide_2025_09_02_reveal.html presentations\day_slides\day_slide_2025_09_02.html

if %errorlevel% equ 0 (
    echo File replaced successfully.
    echo.
    echo Adding to git...
    git add presentations/day_slides/day_slide_2025_09_02.html
    
    echo Committing...
    git commit -m "fix(9/2): match other slides format with Reveal.js sections"
    
    echo Pushing to GitHub...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: 9/2 slide now matches other slides format!
        echo.
        echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
        echo.
        echo Features:
        echo - Same Reveal.js layout as 9/1 and 9/3 slides
        echo - Multiple sections with scrolling
        echo - Working external links
        echo - Purple mobile theme
    ) else (
        echo Push failed
    )
) else (
    echo File copy failed
)

pause