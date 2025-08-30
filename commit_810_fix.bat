@echo off
cd "C:\Users\yoshitaka\ai-news-site"
git add presentations/day_slides/day_slide_2025_08_10.html
git commit -m "fix: Repair 8/10 slide encoding corruption - complete reconstruction"
git push origin main
echo 8/10 slide encoding fix committed successfully!