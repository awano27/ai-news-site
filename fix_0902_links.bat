@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Fixing 9/2 slide links by simplifying JavaScript...

git add presentations/day_slides/day_slide_2025_09_02.html

git commit -m "fix(9/2): remove complex JavaScript to fix source links - simplified Reveal.js config to match working 8/27 template - Generated with Claude Code - Co-Authored-By: Claude <noreply@anthropic.com>"

if %errorlevel% equ 0 (
    echo.
    echo Pushing to GitHub...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: 9/2 slide link fix deployed!
        echo.
        echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
        echo.
        echo Wait 2-3 minutes then test the source links.
    ) else (
        echo Push failed
    )
) else (
    echo Commit failed
)

pause