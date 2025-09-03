@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Fixing 9/2 slide encoding and display issues...

copy /Y presentations\day_slides\day_slide_2025_09_02_fixed.html presentations\day_slides\day_slide_2025_09_02.html

if %errorlevel% equ 0 (
    echo File replaced successfully. Committing...
    
    git add presentations/day_slides/day_slide_2025_09_02.html
    git commit -m "fix(9/2): resolve display issues and update with complete content - Generated with Claude Code - Co-Authored-By: Claude <noreply@anthropic.com>"
    
    if %errorlevel% equ 0 (
        echo Pushing to GitHub...
        git push origin main
        
        if %errorlevel% equ 0 (
            echo.
            echo SUCCESS: 9/2 slide fixed and deployed!
            echo.
            echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
            echo.
            echo The fixed slide should be available in 2-3 minutes.
        ) else (
            echo Push failed
        )
    ) else (
        echo Commit failed
    )
) else (
    echo Copy failed
)

pause