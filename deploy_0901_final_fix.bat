@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Deploying 9/1 slide with fixed Reveal.js settings...

git add presentations/day_slides/day_slide_2025_09_01.html

git commit -m "fix(9/1): simplify Reveal.js config to match working 8/27 template

Based on successful test page verification, the issue was Reveal.js interference:

- Removed navigationMode: linear and disableLayout: true (problematic settings)
- Simplified JavaScript by removing complex event handlers
- Removed forced z-index CSS that was conflicting
- Applied exact same Reveal.js config as working 8/27 slide
- Kept only simple hover effects for external links

This matches the proven working pattern from 8/27 slide where links work perfectly.
External links should now open naturally with target='_blank' attribute.

Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

if %errorlevel% equ 0 (
    echo.
    echo Pushing to GitHub...
    git push origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo SUCCESS: 9/1 slide links should now work!
        echo.
        echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html
        echo.
        echo Wait 2-3 minutes then test the source links at bottom of page.
        echo All 4 links should now open in new tabs correctly.
    ) else (
        echo Push failed
    )
) else (
    echo Commit failed
)

pause