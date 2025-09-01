@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Forcing GitHub Pages update...

echo Step 1: Check if changes are pushed
git status
git log --oneline -3

echo.
echo Step 2: Force push (if needed)
git push origin main --force

echo.
echo Step 3: Clear GitHub Pages cache
echo Visit: https://github.com/awano27/ai-news-site/settings/pages
echo And click "Save" to force rebuild

echo.
echo Step 4: Wait 2-3 minutes then check:
echo https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_01.html

echo.
echo If still not working, try:
echo 1. Hard refresh (Ctrl+F5)
echo 2. Incognito/Private mode
echo 3. Clear browser cache

pause