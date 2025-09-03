@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Fixing 9/1 slide encoding issue...

copy /Y presentations\day_slides\day_slide_2025_09_01_fixed.html presentations\day_slides\day_slide_2025_09_01.html

if %errorlevel% equ 0 (
    echo File replaced successfully. Committing...
    
    git add presentations/day_slides/day_slide_2025_09_01.html
    git commit -m "fix(9/1): resolve encoding issue and update with detailed content - Generated with Claude Code - Co-Authored-By: Claude <noreply@anthropic.com>"
    
    if %errorlevel% equ 0 (
        echo Pushing to GitHub...
        git push origin main
        
        if %errorlevel% equ 0 (
            echo.
            echo SUCCESS: 9/1 slide encoding fixed and deployed!
            echo.
            echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html
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