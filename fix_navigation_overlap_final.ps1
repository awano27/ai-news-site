# Fix Navigation Button Overlap - Move reveal.js controls to right center
Write-Host "=== Final Navigation Fix: Move Controls to Right Center ===" -ForegroundColor Green

# Get all slide files
$slideFiles = Get-ChildItem "presentations/day_slides/*.html"

$processedFiles = 0
foreach ($file in $slideFiles) {
    $processedFiles++
    Write-Host "[$processedFiles/$($slideFiles.Count)] Processing: $($file.Name)" -ForegroundColor Yellow
    
    try {
        # Read file content
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        
        # Enhanced CSS for better button positioning
        $improvedCSS = @"

        /* Enhanced Navigation Fix - Move reveal.js controls to right center */
        .quick-nav {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(0, 0, 0, 0.8);
            padding: 10px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
        
        .quick-nav-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 8px 16px;
            margin: 2px;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .quick-nav-btn:hover {
            background: rgba(255, 255, 255, 0.4);
            transform: translateY(-1px);
        }
        
        /* Move reveal.js controls to right center - NO OVERLAP */
        .reveal .controls {
            position: fixed !important;
            right: 20px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            bottom: unset !important;
            z-index: 999 !important;
        }
        
        .reveal .controls button {
            background: rgba(0, 0, 0, 0.8) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 8px !important;
            padding: 12px !important;
            margin: 4px !important;
            font-size: 16px !important;
            backdrop-filter: blur(10px) !important;
            transition: all 0.3s ease !important;
        }
        
        .reveal .controls button:hover {
            background: rgba(0, 0, 0, 0.9) !important;
            border-color: rgba(255, 255, 255, 0.6) !important;
            transform: scale(1.1) !important;
        }
        
        .reveal .controls .navigate-left,
        .reveal .controls .navigate-right {
            display: block !important;
        }
        
        .reveal .controls .navigate-up,
        .reveal .controls .navigate-down {
            display: none !important;
        }
        
        /* Progress bar stays at bottom */
        .reveal .progress {
            bottom: 0 !important;
            height: 4px !important;
            background: rgba(0, 0, 0, 0.3) !important;
        }
        
        .reveal .progress span {
            background: #3b82f6 !important;
        }
"@

        # Look for the closing </style> tag and add our enhanced CSS before it
        if ($content -match "</style>") {
            $content = $content -replace "</style>", "$improvedCSS`n    </style>"
        }
        
        # Write the updated content
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        Write-Host "  ✅ Enhanced: $($file.Name)" -ForegroundColor Green
        
    } catch {
        Write-Host "  ❌ Error processing $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== Git Operations ===`n" -ForegroundColor Cyan
Write-Host "Adding enhanced files..." -ForegroundColor Yellow
git add presentations/day_slides/*.html

Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "fix: Move reveal.js controls to right center to prevent overlap

- Move slide navigation controls from bottom-right to right-center
- Keep quick navigation buttons in top-right corner  
- Enhanced styling with backdrop blur and hover effects
- Hide up/down navigation buttons (only show left/right)
- Progress bar remains at bottom
- Complete separation prevents any overlap issues

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push origin lightweight-main:main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: Navigation overlap completely fixed!" -ForegroundColor Green
    Write-Host "- Reveal.js controls: Right center (50% height)" -ForegroundColor Cyan  
    Write-Host "- Quick navigation: Top right corner" -ForegroundColor Cyan
    Write-Host "- No more overlap issues!" -ForegroundColor Cyan
    Write-Host "`nGitHub Pages: https://awano27.github.io/ai-news-site/" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Push failed. Check the output above." -ForegroundColor Red
}

Write-Host "`n=== Complete ===`n" -ForegroundColor Green