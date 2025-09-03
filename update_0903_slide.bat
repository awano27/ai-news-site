@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Updating 9/3 slide with detailed content...

copy /Y presentations\day_slides\day_slide_2025_09_03_detailed.html presentations\day_slides\day_slide_2025_09_03.html

if %errorlevel% equ 0 (
    echo File updated successfully. Committing...
    
    git add presentations/day_slides/day_slide_2025_09_03.html
    git commit -m "feat(9/3): update slide with detailed LongCat-Flash content - Generated with Claude Code - Co-Authored-By: Claude <noreply@anthropic.com>"
    
    if %errorlevel% equ 0 (
        echo Pushing to GitHub...
        git push origin main
        
        if %errorlevel% equ 0 (
            echo.
            echo SUCCESS: 9/3 detailed slide deployed!
            echo.
            echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_03.html
            echo.
            echo The detailed slide should be available in 2-3 minutes.
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