@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Applying final link fixes for both 9/1 and 9/2 slides...

git add presentations/day_slides/day_slide_2025_09_01.html presentations/day_slides/day_slide_2025_09_02.html presentations/link_test.html

git commit -m "fix(links): force external links to work with CSS overrides - removed cursor pointer from inline styles - added pointer-events auto and z-index overrides - Generated with Claude Code - Co-Authored-By: Claude <noreply@anthropic.com>"

if %errorlevel% equ 0 (
    echo.
    echo Pushing to GitHub...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: All link fixes deployed!
        echo.
        echo Test URLs:
        echo 9/1 slide: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html
        echo 9/2 slide: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
        echo Test page: https://awano27.github.io/ai-news-site/presentations/link_test.html
        echo.
        echo Wait 2-3 minutes then test all source links.
    ) else (
        echo Push failed
    )
) else (
    echo Commit failed
)

pause