Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🚀 Deploying improved 8/31 AI Prompt Engineering slide..." -ForegroundColor Cyan

git add presentations/day_slides/day_slide_2025_08_31.html

git commit -m "feat(slides): completely redesign 8/31 slide with enhanced content structure

🎯 Content Improvements:
- Professional title: 'AIプロンプトエンジニアリング最前線2025'
- Structured sections with clear visual hierarchy
- Comprehensive technique comparison table
- Practical implementation examples for engineers and business
- Risk management and security best practices
- Step-by-step implementation guide
- Industry trends and future outlook
- Detailed references and source validation

💎 Design Enhancements:
- Modern card-based layout with glassmorphism effects
- Color-coded information hierarchy (success/warning/info)
- Interactive progress bar and smooth scrolling
- Responsive grid layouts for different screen sizes
- Professional typography and spacing
- Animated gradient backgrounds

📊 Content Structure:
- 9 comprehensive sections vs previous basic layout
- 89pt impact score with detailed methodology
- 5+ advanced techniques with practical examples
- Risk mitigation strategies with probabilities
- Implementation timeline with specific actions
- Multiple data sources and validation

🔧 Technical Fixes:
- Stable Reveal.js configuration
- Proper BOM encoding for Japanese text
- Optimized CSS for performance and accessibility
- Cross-browser compatibility improvements

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host ""
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ Enhanced 8/31 slide is now LIVE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Updated slide:" -ForegroundColor Cyan
    Write-Host "   https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_31.html" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🎨 Key Improvements:" -ForegroundColor Magenta
    Write-Host "   • Professional content structure with 9 comprehensive sections" -ForegroundColor White
    Write-Host "   • Practical implementation guide and real-world examples" -ForegroundColor White
    Write-Host "   • Risk management strategies and security best practices" -ForegroundColor White
    Write-Host "   • Modern glassmorphism design with responsive layout" -ForegroundColor White
    Write-Host "   • Interactive progress bar and smooth user experience" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Content Quality: 89pt impact score | Professional-grade presentation" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Check error above." -ForegroundColor Red
}