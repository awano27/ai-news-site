@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Adding 9/2 slide improvements...
git add presentations/day_slides/day_slide_2025_09_02.html

echo Committing changes...
git commit -m "feat(9/2): add comprehensive evaluation section and match slide structure

- Added 6-item stats grid with detailed scoring breakdown
- Added market response and community analysis section  
- Added 'why this matters' highlight box
- Restructured sections to match 9/1 and 9/3 format:
  1. Title Slide -> Overview -> Technical Details -> Business Impact -> Evaluation and Links
- All source links verified and working
- Comprehensive evaluation covers technical innovation, implementation, performance, business value, and market impact"

echo Pushing to GitHub...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: 9/2 slide improvements deployed!
    echo.
    echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
    echo.
    echo New features:
    echo - Comprehensive evaluation with 6 scoring dimensions
    echo - Market analysis and community metrics
    echo - Structured format matching other daily slides
    echo - Enhanced business impact section
) else (
    echo Push failed
)

pause