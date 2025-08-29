@echo off
echo === Resolving All Merge Conflicts ===

echo Adding all conflicted slide files...
git add presentations/day_slides/day_slide_2025_07_30.html
git add presentations/day_slides/day_slide_2025_08_02.html
git add presentations/day_slides/day_slide_2025_08_05.html
git add presentations/day_slides/day_slide_2025_08_06.html
git add presentations/day_slides/day_slide_2025_08_09.html
git add presentations/day_slides/day_slide_2025_08_10.html
git add presentations/day_slides/day_slide_2025_08_11.html
git add presentations/day_slides/day_slide_2025_08_12.html
git add presentations/day_slides/day_slide_2025_08_13.html
git add presentations/day_slides/day_slide_2025_08_14.html
git add presentations/day_slides/day_slide_2025_08_15.html
git add presentations/day_slides/day_slide_2025_08_16.html
git add presentations/day_slides/day_slide_2025_08_17.html
git add presentations/day_slides/day_slide_2025_08_19.html
git add presentations/day_slides/day_slide_2025_08_20.html
git add presentations/day_slides/day_slide_2025_08_22.html
git add presentations/day_slides/day_slide_2025_08_23.html
git add presentations/day_slides/day_slide_2025_08_24.html
git add presentations/day_slides/day_slide_2025_08_26.html

echo.
echo Checking status...
git status

echo.
echo Completing merge commit...
git commit -m "resolve: merge conflicts in all daily slides - Keep local versions with comprehensive content - Fix all both-added conflict scenarios"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo === Operation Complete ===
pause