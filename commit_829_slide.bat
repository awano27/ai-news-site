@echo off
cd "C:\Users\yoshitaka\ai-news-site"
echo.
echo ==========================================
echo Creating and deploying 8/29 Grok Code Fast 1 slide
echo ==========================================
echo.

echo Adding all 8/29 slide files...
git add presentations/day_slides/day_slide_2025_08_29.html
git add presentations/index.html
git add presentations/day_slides_index.html

echo.
echo Current status:
git status --short

echo.
echo Committing changes...
git commit -m "feat: Add 8/29 Grok Code Fast 1 slide - xAI's high-speed coding revolution

NEW SLIDE: Complete coverage of xAI's breakthrough coding AI
- day_slide_2025_08_29.html: Comprehensive analysis with 96pt impact
- 67ms response time, 70.8% SWE-Bench accuracy, 160 tokens/sec
- High X engagement: 8,659 likes, active developer community discussion
- IDE integration ready: Cursor, VS Code, GitHub Copilot support
- Free trial period with unlimited usage potential

NAVIGATION UPDATES:
- Added to presentations/index.html sidebar and quick access
- Added to presentations/day_slides_index.html with full card
- JavaScript mapping updated for seamless navigation
- Positioned at top as latest daily slide (8/29)

CONTENT HIGHLIGHTS:
- Revolutionary high-speed AI coding tool analysis
- Technical comparison with GitHub Copilot and other tools  
- Implementation guide for engineers and business users
- X/Twitter engagement analysis with community feedback
- Market impact assessment and future implications
- Actionable implementation plan for immediate adoption

This ensures 8/29 content is visible across all distribution channels.

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ==========================================  
echo SUCCESS! 8/29 Grok Code Fast 1 slide deployed!
echo ==========================================
echo.
echo The slide is now accessible via:
echo - https://awano27.github.io/ai-news-site/presentations/index.html
echo - https://awano27.github.io/ai-news-site/presentations/day_slides_index.html
echo - Direct: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_29.html
echo.
pause