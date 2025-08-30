@echo off
cd "C:\Users\yoshitaka\ai-news-site"
echo === Committing link clickability fixes for all slides ===
git add presentations/day_slides/day_slide_2025_08_10.html
git add presentations/day_slides/day_slide_2025_08_28.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_19.html
git status --short
git commit -m "fix: Ensure all slide source links are clickable - comprehensive fix

CRITICAL FIX: Resolve link interaction issues in reveal.js slides
- Added mouseWheel: false, disableLayout: true to Reveal.initialize
- Set pointer-events: auto !important on all links
- Added z-index: 10 to ensure links are above other elements
- Fixed CSS for .source-link and .source-links classes

Fixed slides:
- day_slide_2025_08_10.html (GPT-5)
- day_slide_2025_08_28.html (OpenAI Codex)
- day_slide_2025_08_20.html (Google Pixel 10)
- day_slide_2025_08_19.html (AMD Ryzen 7 8700G)

This ensures all source reference links are clickable and interactive."
git push origin main
echo.
echo ===================================
echo Link fixes committed successfully!
echo ===================================
pause