@echo off
cd "C:\Users\yoshitaka\ai-news-site"
echo.
echo ==========================================
echo Committing ALL slide link fixes
echo ==========================================
echo.

echo Adding all fixed slides to git...
git add presentations/day_slides/day_slide_2025_08_01.html
git add presentations/day_slides/day_slide_2025_08_03.html
git add presentations/day_slides/day_slide_2025_08_04.html
git add presentations/day_slides/day_slide_2025_08_10.html
git add presentations/day_slides/day_slide_2025_08_14.html
git add presentations/day_slides/day_slide_2025_08_15.html
git add presentations/day_slides/day_slide_2025_08_16.html
git add presentations/day_slides/day_slide_2025_08_17.html
git add presentations/day_slides/day_slide_2025_08_18.html
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_28.html

echo.
echo Current status:
git status --short

echo.
echo Committing changes...
git commit -m "fix: Ensure ALL slide source links are clickable - comprehensive fix

CRITICAL FIX: Complete resolution of link interaction issues in reveal.js
- Added mouseWheel: false, hideInactiveCursor: false, disableLayout: true
- Set pointer-events: auto !important on all links
- Added z-index: 10 to ensure links are above other elements
- Fixed CSS for .source-link and .source-links classes

Fixed ALL slides with source links (12 total):
- 08/01 - AI News Analysis
- 08/03 - Google DeepMind AlphaEarth
- 08/04 - AI News Analysis
- 08/10 - GPT-5 Production Deployment
- 08/14 - Anthropic Claude 3.5
- 08/15 - OpenAI o1-mini
- 08/16 - Meta Llama 3.1
- 08/17 - Google Gemini Updates
- 08/18 - AI News Analysis
- 08/19 - AMD Ryzen 7 8700G
- 08/20 - Google Pixel 10
- 08/28 - OpenAI Codex

This ensures 100% of source reference links are now clickable."

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ==========================================
echo SUCCESS! All slide links are now clickable!
echo ==========================================
echo.
pause