@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Direct commit of staged file...

git commit -m "fix(9/2): replace broken slide with working simple HTML version - Generated with Claude Code"

if %errorlevel% equ 0 (
    echo Commit successful! Now pushing...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: 9/2 slide deployed!
        echo.
        echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
        echo The slide should be visible in 2-3 minutes.
    ) else (
        echo Push failed but commit succeeded
    )
) else (
    echo Commit still failed. Manual intervention needed.
)

pause