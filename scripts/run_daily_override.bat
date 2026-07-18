@echo off
setlocal
for %%I in ("%~dp0..") do set "REPO=%%~fI"
if exist "%LOCALAPPDATA%\visionhub-daily-news-override\secrets.local.bat" call "%LOCALAPPDATA%\visionhub-daily-news-override\secrets.local.bat"
if not defined NVIDIA_API_KEY if exist "C:\develop\ai-news-site\scripts\secrets.local.bat" call "C:\develop\ai-news-site\scripts\secrets.local.bat"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%REPO%\scripts\run_daily_override.ps1" -RepoPath "%REPO%"
exit /b %ERRORLEVEL%
