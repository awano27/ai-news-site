@echo off
echo Committing 8/31 slide encoding fixes...
git add presentations/day_slides/day_slide_2025_08_31.html
git commit -m "fix(slides): resolve 8/31 slide encoding and BOM issues for proper display"
git push origin main
echo.
echo ✅ 8/31 slide bug fixes have been pushed to GitHub!
pause