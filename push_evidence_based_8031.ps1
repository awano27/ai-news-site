Set-Location "C:\Users\yoshitaka\ai-news-site"

Write-Host "🔬 Deploying evidence-based 8/31 slide with research backing..." -ForegroundColor Cyan

git add presentations/day_slides/day_slide_2025_08_31.html

git commit -m "feat(slides): create evidence-based 8/31 prompt engineering slide

🎯 Content Quality Transformation:
- Title: 'エビデンス重視のプロンプトエンジニアリング'
- Research-backed approach with peer-reviewed citations
- Balanced perspective addressing limitations and risks
- Evidence-first methodology with statistical significance

📊 Research Foundation:
- Chain-of-Thought: +10-30pt improvement (arXiv verified)
- Self-Consistency: 51.7%→68% on GSM8K (AWS data)  
- Cost optimization: ~76% reduction with structured approach
- Statistical validation: n≥30, p<0.05 significance threshold

🏗️ Practical Implementation:
- 5-block master prompt template (Role-Task-Output-Verify-Constraints)
- Incremental booster application (CoT → Self-Consistency → Few-Shot)
- A/B testing framework with 2-week measurement cycle
- Security best practices with input validation

⚠️ Balanced Analysis:
- Explicit acknowledgment of task dependency and limitations
- Hallucination risk mitigation strategies
- Cost/latency considerations for long prompts
- Security vulnerability awareness (prompt injection)

🔬 Methodology Transparency:
- Primary source verification (OpenAI, IBM, Lakera official guides)
- Academic research validation (arXiv, AWS experiments)
- X post existence confirmation with caveat on metrics accuracy
- Industry trend analysis (McKinsey, PwC, Bessemer reports)

💎 Design Excellence:
- Evidence-focused color scheme (purple accent for research)
- Performance badges for technique classification
- Citation integration throughout content
- Responsive design with accessibility considerations

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host ""
Write-Host "📤 Pushing evidence-based version to GitHub..." -ForegroundColor Cyan
git push origin main

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ Evidence-based 8/31 slide is now LIVE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Research-backed slide:" -ForegroundColor Cyan
    Write-Host "   https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_08_31.html" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔬 Key Improvements:" -ForegroundColor Magenta
    Write-Host "   • Evidence-first approach with peer-reviewed citations" -ForegroundColor White
    Write-Host "   • Balanced perspective addressing real limitations" -ForegroundColor White
    Write-Host "   • Statistical validation framework (n≥30, p<0.05)" -ForegroundColor White
    Write-Host "   • Practical 5-block template with security considerations" -ForegroundColor White
    Write-Host "   • Transparent methodology and source verification" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Research Quality:" -ForegroundColor Cyan
    Write-Host "   • Primary sources: OpenAI, IBM, Lakera official guides" -ForegroundColor White
    Write-Host "   • Academic backing: arXiv, AWS experimental data" -ForegroundColor White
    Write-Host "   • Industry trends: McKinsey, PwC, Bessemer reports" -ForegroundColor White
    Write-Host "   • Honest assessment of X metrics limitations" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Professional Standard: Research-grade presentation ready for enterprise use" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Check error above." -ForegroundColor Red
}