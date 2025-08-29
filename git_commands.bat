@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Adding resolved files...
git add presentations/day_slides/day_slide_2025_08_08.html

echo Checking git status...
git status

echo Completing merge commit...
git commit -m "resolve: merge conflicts in GPT-5 slide - Keep HEAD version with comprehensive GPT-5 content - Preserve updated slide with detailed analysis and evaluation - Fixed all merge conflict markers"

echo Pushing to remote...
git push origin main

echo Git operations completed successfully!
pause