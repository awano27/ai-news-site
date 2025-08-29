@echo off
cd "C:\Users\yoshitaka\ai-news-site"
git add presentations/day_slides/day_slide_2025_08_03.html
git add presentations/day_slides/day_slide_2025_08_25.html  
git add presentations/day_slides/day_slide_2025_08_26.html
git add presentations/day_slides/day_slide_2025_08_01.html
git commit -m "fix: Standardize all slides with 08/27 excellent scrolling style

- Applied perfect scrolling CSS from 08/27 to slides 08/01, 08/03, 08/25, 08/26
- Fixed viewport settings to enable user scaling
- Added comprehensive responsive design for mobile devices
- Disabled reveal.js controls for consistent scrolling experience
- All slides now have the same excellent readability as 08/27

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
echo "All standardized slides committed and pushed successfully!"