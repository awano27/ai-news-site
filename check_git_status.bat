@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo === Git Status ===
git status

echo.
echo === Recent Commits ===
git log --oneline -5

echo.
echo === Remote Status ===
git ls-remote --heads origin main

echo.
echo 9/3 slide is already updated on remote. Check the URL:
echo https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_03.html

pause