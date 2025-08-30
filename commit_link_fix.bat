@echo off
cd "C:\Users\yoshitaka\ai-news-site"
git add presentations/day_slides/day_slide_2025_08_10.html presentations/day_slides/day_slide_2025_08_28.html
git commit -m "fix: Ensure source links are clickable in slides - reveal.js interaction fix"
git push origin main
echo Link clickability fix committed!