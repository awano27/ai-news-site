@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Checking git status...
git status

echo.
echo Checking remote status...
git remote -v

echo.
echo Recent commits...
git log --oneline -5

pause