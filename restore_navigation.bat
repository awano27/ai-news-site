@echo off
echo === Restore Slide Navigation Controls ===

echo Adding modified slide files...
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_22.html
git add presentations/day_slides/day_slide_2025_08_23.html
git add presentations/day_slides/day_slide_2025_08_24.html
git add presentations/day_slides/day_slide_2025_08_27.html

echo Creating commit...
git commit -m "fix: Restore slide navigation while hiding QuickAccess buttons

- Enabled reveal.js controls with controls: true
- Added controlsLayout: edges and controlsBackArrows: faded
- Hide only QuickAccess buttons with specific CSS selectors
- Slide navigation (arrows) now visible and functional
- No overlap issues as QuickAccess buttons are hidden

Applied to slides: 8/19, 8/20, 8/22, 8/23, 8/24, 8/27

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo Pushing to GitHub...
git push origin main

echo.
echo === Navigation Restored Successfully ===