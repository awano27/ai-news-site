@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Deploying 9/2 slide...

git add presentations/day_slides/day_slide_2025_09_02.html presentations/day_slides_index.html

git commit -m "feat(9/2): add MiniCPM-V 4.5 mobile AI revolution slide - Generated with Claude Code - Co-Authored-By: Claude <noreply@anthropic.com>"

if %errorlevel% equ 0 (
    echo.
    echo Pushing to GitHub...
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
) else (
    echo Commit failed
)

pause