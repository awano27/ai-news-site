@echo off
REM Weekly Obsidian X-Bookmarks -> tool candidate digest.
REM Designed for Windows Task Scheduler.
REM Runs harvest_obsidian_tools.py and copies the latest dossier into the
REM Obsidian Inbox so the user sees it on next vault open.

setlocal enabledelayedexpansion

set "PROJECT_ROOT=C:\develop\ai-news-site"
set "OBSIDIAN_INBOX=C:\develop\obsidian\2026\00 Inbox"
set "DIGEST_NAME=_weekly_tool_candidates.md"

cd /d "%PROJECT_ROOT%" || (echo Failed to enter %PROJECT_ROOT% & exit /b 1)

python scripts\harvest_obsidian_tools.py --days 14
if errorlevel 1 (
    echo [weekly_tool_harvest] Harvester failed.
    exit /b 1
)

set "LATEST="
for /f "delims=" %%f in ('dir /b /od "tmp\tool_candidates_*.md" 2^>nul') do set "LATEST=%%f"

if defined LATEST (
    if exist "%OBSIDIAN_INBOX%" (
        copy /y "tmp\!LATEST!" "%OBSIDIAN_INBOX%\%DIGEST_NAME%" >nul
        echo [weekly_tool_harvest] Digest copied: %OBSIDIAN_INBOX%\%DIGEST_NAME%
    ) else (
        echo [weekly_tool_harvest] Inbox not found: %OBSIDIAN_INBOX%
        echo Skipped copy. Latest dossier remains at tmp\!LATEST!.
    )
) else (
    echo [weekly_tool_harvest] No dossier produced.
)

endlocal
exit /b 0
