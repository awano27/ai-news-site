@echo off
setlocal enableextensions
set REPO=%~dp0..
if not exist "%REPO%\.git\hooks" (
  echo .git\hooks not found. Run from a git repo.
  exit /b 1
)
(
  echo @echo off
  echo rem Pre-commit mojibake check (Windows)
  echo set PYTHONPATH=%REPO%
  echo python "%REPO%\tools\check_mojibake.py"
  echo if not %%errorlevel%%==0 exit /b 1
) > "%REPO%\.git\hooks\pre-commit.bat"
echo Installed .git\hooks\pre-commit.bat
exit /b 0

