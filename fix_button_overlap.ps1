# Script to fix overlapping navigation buttons in slides
Write-Host "=== Fixing Navigation Button Overlap ===" -ForegroundColor Green

# Get all slide files
$slideFiles = Get-ChildItem "presentations/day_slides/*.html"

$processedFiles = 0
foreach ($file in $slideFiles) {
    $processedFiles++
    Write-Host "[$processedFiles/$($slideFiles.Count)] Processing: $($file.Name)" -ForegroundColor Yellow
    
    try {
        # Read file content
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        
        # Fix button positioning by moving custom nav buttons to top-right
        # Add CSS for better button positioning
        $cssAddition = @"

        /* Fix navigation button overlap */
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
        
        /* Ensure reveal.js controls don't overlap */
        .reveal .controls {
            bottom: 20px;
            right: 20px;
        }
"@

        # Look for the closing </style> tag and add our CSS before it
        if ($content -match "</style>") {
            $content = $content -replace "</style>", "$cssAddition`n    </style>"
        }
        
        # Add quick navigation HTML right after <body> tag
        $quickNavHTML = @"
<body>
    <div class="quick-nav">
        <a href="../day_slides_index.html" class="quick-nav-btn" title="All Daily Slides">📅 Daily</a>
        <a href="../index.html" class="quick-nav-btn" title="Home">🏠 Home</a>
    </div>
"@
        
        # Replace <body> with our quick nav
        $content = $content -replace "<body>", $quickNavHTML
        
        # Remove any existing overlapping navigation buttons from the slides content
        # Look for patterns like bottom: 20px; right: 20px; in custom nav elements
        $content = $content -replace 'bottom:\s*20px;\s*right:\s*20px;', 'bottom: 20px; left: 20px;'
        
        # Write the updated content
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        Write-Host "  ✅ Fixed: $($file.Name)" -ForegroundColor Green
        
    } catch {
        Write-Host "  ❌ Error processing $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== Git Operations ===" -ForegroundColor Cyan
Write-Host "Adding fixed files..." -ForegroundColor Yellow
git add presentations/day_slides/*.html

Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "fix: Resolve navigation button overlap in all slides

- Move quick navigation to top-right corner
- Prevent overlap with reveal.js controls (bottom-right)
- Add backdrop blur and better styling for nav buttons
- Ensure all slide navigation is accessible

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push origin lightweight-main
git push origin lightweight-main:main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS: Navigation button overlap fixed!" -ForegroundColor Green
    Write-Host "- Quick nav buttons moved to top-right" -ForegroundColor Cyan  
    Write-Host "- Reveal.js controls remain in bottom-right" -ForegroundColor Cyan
    Write-Host "- No more button overlap issues!" -ForegroundColor Cyan
    Write-Host "`nGitHub Pages: https://awano27.github.io/ai-news-site/" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Push failed. Check the output above." -ForegroundColor Red
}

Write-Host "`n=== Complete ===" -ForegroundColor Green