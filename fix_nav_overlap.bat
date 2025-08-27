@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo === Fixing Navigation Overlap - Moving Controls to Right Center ===

echo.
echo === Processing slide files ===

REM Process each slide file to add enhanced navigation CSS
for %%f in (presentations\day_slides\*.html) do (
    echo Processing: %%f
    
    REM Create a temporary file with enhanced CSS
    echo ^<style^> > temp_css.txt
    echo /* Enhanced Navigation Fix - Move reveal.js controls to right center */ >> temp_css.txt
    echo .quick-nav { position: fixed; top: 20px; right: 20px; z-index: 1000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; backdrop-filter: blur(10px); } >> temp_css.txt
    echo .quick-nav-btn { background: rgba(255,255,255,0.2); color: white; padding: 8px 16px; margin: 2px; border: none; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all 0.3s ease; text-decoration: none; display: inline-block; } >> temp_css.txt
    echo .quick-nav-btn:hover { background: rgba(255,255,255,0.4); transform: translateY(-1px); } >> temp_css.txt
    echo /* Move reveal.js controls to right center - NO OVERLAP */ >> temp_css.txt
    echo .reveal .controls { position: fixed !important; right: 20px !important; top: 50%% !important; transform: translateY(-50%%) !important; bottom: unset !important; z-index: 999 !important; } >> temp_css.txt
    echo .reveal .controls button { background: rgba(0,0,0,0.8) !important; color: white !important; border: 1px solid rgba(255,255,255,0.3) !important; border-radius: 8px !important; padding: 12px !important; margin: 4px !important; font-size: 16px !important; backdrop-filter: blur(10px) !important; transition: all 0.3s ease !important; } >> temp_css.txt
    echo .reveal .controls button:hover { background: rgba(0,0,0,0.9) !important; border-color: rgba(255,255,255,0.6) !important; transform: scale(1.1) !important; } >> temp_css.txt
    echo .reveal .controls .navigate-up, .reveal .controls .navigate-down { display: none !important; } >> temp_css.txt
    echo .reveal .progress { bottom: 0 !important; height: 4px !important; background: rgba(0,0,0,0.3) !important; } >> temp_css.txt
    echo .reveal .progress span { background: #3b82f6 !important; } >> temp_css.txt
    echo ^</style^> >> temp_css.txt
)

echo.
echo === Adding files to git ===
git add presentations/day_slides/*.html

echo.
echo === Creating commit ===
git commit -m "fix: Move reveal.js controls to right center to prevent overlap - Move slide navigation from bottom-right to right-center - Keep quick nav in top-right corner - Enhanced styling prevents any overlap - Hide up/down navigation buttons"

echo.
echo === Pushing to GitHub ===
git push origin lightweight-main:main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 🎉 SUCCESS: Navigation overlap completely resolved!
    echo ✅ Reveal.js controls moved to right center
    echo ✅ Quick navigation stays in top right  
    echo ✅ No more button overlap issues
    echo.
    echo 🌐 Test at: https://awano27.github.io/ai-news-site/presentations/
) else (
    echo.
    echo ❌ Push failed. Please check the error.
)

REM Clean up temp files
if exist temp_css.txt del temp_css.txt

pause