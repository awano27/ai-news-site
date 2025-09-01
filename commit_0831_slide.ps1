Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🚀 Committing 8/31 AI Master Prompt slide..." -ForegroundColor Cyan

git add presentations/day_slides/day_slide_2025_08_31.html
git add presentations/index.html
git add presentations/day_slides_index.html

git commit -m "feat(slides): add 8/31 AI Master Prompt革命 slide with full integration

🚀 New 8/31 Slide Features:
- AI Master Prompt革命 - 業務効率100倍向上への究極テンプレート
- Impact Score: 92pt with 95% confidence level
- Comprehensive prompt engineering guide with practical examples
- Engineer & business use cases with step-by-step implementation
- Advanced techniques: Chain-of-Thought, Few-Shot, Role-Based prompting
- Risk mitigation strategies and industry trend analysis
- Based on viral X post (133 likes, 1,894 views) by folaoftech
- Immediate applicability with copy-paste templates

📊 Navigation Updates:
- Added 8/31 to presentations/index.html Quick Access menu (top position)
- Updated slideMap with proper chronological ordering
- Added 8/31 to day_slides_index.html with high-impact card design
- Updated statistics: 28 total slides in comprehensive dashboard
- Maintained consistent navigation structure across all channels

🎨 Content Highlights:
- Structured template: Role → Analysis → Output format
- Engineer examples: Code debugging, optimization, design review
- Business examples: Report generation, market analysis, project management
- Implementation steps with customization tips and video reference
- Industry data: 30-50% output accuracy improvement, 20-40% efficiency gains
- Risk analysis: Privacy, hallucination, dependency mitigation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host ""
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ 8/31 AI Master Prompt slide is now LIVE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 Access the new slide:" -ForegroundColor Cyan
    Write-Host "   🚀 8/31 Slide: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_31.html" -ForegroundColor Yellow
    Write-Host "   🏠 Main Dashboard: https://awano27.github.io/ai-news-site/presentations/index.html" -ForegroundColor Yellow
    Write-Host "   📅 Slides Index: https://awano27.github.io/ai-news-site/presentations/day_slides_index.html" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🎯 Key Features:" -ForegroundColor Magenta
    Write-Host "   • 100倍業務効率向上のマスタープロンプトテンプレート" -ForegroundColor White
    Write-Host "   • エンジニア・ビジネス両対応の実践例" -ForegroundColor White
    Write-Host "   • 即日適用可能な構造化テンプレート" -ForegroundColor White
    Write-Host "   • Chain-of-Thought等の高度なテクニック解説" -ForegroundColor White
    Write-Host "   • リスク対策と業界トレンド分析" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Total slides: 28 (Impact Score: 92pt)" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Please check the error message above." -ForegroundColor Red
}