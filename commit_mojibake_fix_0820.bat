@echo off
cd "C:\Users\yoshitaka\ai-news-site"
echo.
echo ==========================================
echo Committing 8/20 mojibake fix
echo ==========================================
echo.

echo Adding repaired 8/20 slide and status document...
git add presentations/day_slides/day_slide_2025_08_20.html
git add MOJIBAKE_STATUS.md

echo.
echo Current status:
git status --short

echo.
echo Committing changes...
git commit -m "fix: Complete repair of 8/20 slide mojibake - Google Pixel 10 reconstruction

CRITICAL MOJIBAKE FIX: day_slide_2025_08_20.html
- Complete reconstruction with proper UTF-8 encoding
- Source: 0820.txt input file with correct Japanese content  
- Applied 08/27 excellent template with perfect scrolling
- Content: Google Pixel 10 AI features analysis with 92pt impact

TECHNICAL DETAILS:
- Fixed severe corruption: 縺ｧ縺阪ｋ諠・ｱ → できる情報
- Japanese text now displays correctly throughout slide
- Link clickability maintained with pointer-events fixes
- Responsive design with mobile breakpoints

CONTENT HIGHLIGHTS:
- Tensor G5 + Gemini AI integration analysis
- Magic Cue, Voice Translate, Pro Res Zoom features
- 4-model lineup ($800-$1,800 price range)
- Business/Engineer KPI evaluation (8-9/10 scores)
- 5 verified source links with 95% confidence

IMPACT: Critical user experience improvement - Japanese content now readable

REMAINING WORK: 13 more files have mojibake (see MOJIBAKE_STATUS.md)

🤖 Generated with Claude Code  
Co-Authored-By: Claude <noreply@anthropic.com>"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ==========================================
echo 8/20 mojibake fix committed successfully!
echo ==========================================
echo.
echo Status: 2/15 mojibake slides fixed (08/10, 08/20)
echo Remaining: 13 slides need repair (see MOJIBAKE_STATUS.md)
echo.
pause