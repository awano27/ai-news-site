@echo off
REM Local override for visionhub daily-news. Triggered by Windows Task Scheduler.
REM Runs after the cloud primary (06:00 JST) so X bookmarks from the Obsidian
REM vault fill the X tab. Pulls cloud's commit, regenerates (NVIDIA NIM when a
REM key is configured, otherwise local Ollama), commits and pushes report paths.

setlocal
set REPO=C:\develop\ai-news-site
set LOG=%REPO%\logs\run_daily_override.log
set TODAY_MMDD=%date:~5,2%%date:~8,2%
set TODAY_YMD=%date:~0,4%-%date:~5,2%-%date:~8,2%

cd /d "%REPO%" || exit /b 1

REM Pin the interpreter. The hermes-agent venv hijacked the PATH "python"
REM (no pipeline deps), which broke the X sync the same way on 2026-06-07.
REM This alias is the Microsoft Store Python that has feedparser/trafilatura
REM etc. and is version-independent, so PATH pollution cannot break us again.
set "PY=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"

REM Load gitignored local secrets (provides NVIDIA_API_KEY for cloud-grade
REM scoring). Template: scripts\secrets.local.bat.example -> copy to
REM scripts\secrets.local.bat and paste your key.
if exist "%REPO%\scripts\secrets.local.bat" call "%REPO%\scripts\secrets.local.bat"

REM Provider: prefer NVIDIA NIM when a real key (nvapi-...) is present - stable,
REM no local GPU. Otherwise fall back to local Ollama so we never regress.
set "PROVIDER=ollama"
if defined NVIDIA_API_KEY (
  echo %NVIDIA_API_KEY%| findstr /b /c:"nvapi-" >nul && set "PROVIDER=nvidia"
)

echo. >> "%LOG%"
echo === %DATE% %TIME% START daily override (provider=%PROVIDER%) === >> "%LOG%"

REM Ollama health check only matters when using the local provider.
if /I "%PROVIDER%"=="ollama" (
  curl -s -m 3 http://localhost:11434/api/tags >nul 2>&1
  if errorlevel 1 (
    echo %DATE% %TIME%: Ollama not responding on :11434 - aborting >> "%LOG%"
    exit /b 1
  )
)

REM Pull cloud primary commit before regenerating (upstream-independent)
git fetch origin main >> "%LOG%" 2>&1
if errorlevel 1 (
  echo %DATE% %TIME%: git fetch failed - aborting >> "%LOG%"
  exit /b 1
)
git rebase --autostash origin/main >> "%LOG%" 2>&1
if errorlevel 1 (
  echo %DATE% %TIME%: git rebase onto origin/main failed - aborting >> "%LOG%"
  git rebase --abort >> "%LOG%" 2>&1
  exit /b 1
)

REM Regenerate (reads X bookmarks from vault). NVIDIA when key present, else Ollama.
"%PY%" -m src.auto_collect.main --provider %PROVIDER% --force >> "%LOG%" 2>&1
if errorlevel 1 (
  echo %DATE% %TIME%: pipeline failed >> "%LOG%"
  exit /b 1
)

REM Stage only known output paths (avoid sweeping unrelated untracked files)
git add -u >> "%LOG%" 2>&1
git add "input/day/%TODAY_MMDD%.txt" 2>nul
git add "daily-news/data.json" "daily-news/index.html" 2>nul
git add "presentations/auto_daily_report.html" "presentations/auto_daily_report.json" 2>nul
git add "presentations/daily_reports/%TODAY_YMD%.html" 2>nul
git add "public-pages/api/auto_daily_report/latest.json" 2>nul
git add "public-pages/api/auto_daily_report/%TODAY_YMD%.json" 2>nul
git add "public-pages/news/%TODAY_YMD%.json" 2>nul
git add "public-pages/news/archive_index.json" "public-pages/news/version.json" "public-pages/news/latest.json" 2>nul
git add "news/latest.json" 2>nul

git diff --cached --quiet
if errorlevel 1 (
  git commit -m "chore(report): local override %TODAY_YMD%" >> "%LOG%" 2>&1
  git push origin main >> "%LOG%" 2>&1
  if errorlevel 1 (
    echo %DATE% %TIME%: git push failed - manual resolution needed >> "%LOG%"
    exit /b 1
  )
  echo %DATE% %TIME%: pushed local override >> "%LOG%"
) else (
  echo %DATE% %TIME%: no changes to commit >> "%LOG%"
)

echo === %DATE% %TIME% END === >> "%LOG%"
endlocal
exit /b 0
