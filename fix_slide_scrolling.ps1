# Fix scrolling issues in all slide files
Write-Host "Fixing slide scrolling issues..." -ForegroundColor Green

$slidesDir = "presentations/day_slides"
$slideFiles = Get-ChildItem -Path $slidesDir -Filter "*.html"

foreach ($file in $slideFiles) {
    Write-Host "Processing $($file.Name)..." -ForegroundColor Yellow
    
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    
    # 1. Fix viewport meta tag - allow user scaling and remove maximum-scale
    $content = $content -replace 'maximum-scale=1\.0,\s*user-scalable=no', 'user-scalable=yes'
    
    # 2. Add/update CSS for better scrolling
    if ($content -match '(<style>)') {
        $scrollingCSS = @"
        
        /* Scrolling fixes and responsive improvements */
        html, body {
            height: 100%;
            overflow-y: auto !important;
            overflow-x: hidden;
            -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS */
        }
        
        .reveal {
            position: relative !important;
            height: auto !important;
            min-height: 100vh;
            overflow: visible !important;
        }
        
        .reveal .slides {
            position: relative !important;
            width: 100% !important;
            height: auto !important;
            top: 0 !important;
            left: 0 !important;
            margin: 0 !important;
            padding: 20px !important;
            text-align: center !important;
            overflow: visible !important;
            transform: none !important;
        }
        
        .reveal .slides section {
            position: relative !important;
            width: 100% !important;
            max-width: 1200px !important;
            height: auto !important;
            min-height: auto !important;
            top: auto !important;
            left: auto !important;
            margin: 0 auto 30px auto !important;
            padding: 20px !important;
            display: block !important;
            overflow: visible !important;
            transform: none !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        
        /* Hide reveal.js controls for scrolling mode */
        .reveal .controls,
        .reveal .progress,
        .reveal .playback,
        .reveal .slide-number {
            display: none !important;
        }
        
        /* Responsive design improvements */
        @media screen and (max-width: 768px) {
            .reveal .slides section {
                padding: 15px !important;
                margin: 0 10px 20px 10px !important;
            }
            
            .reveal h1 {
                font-size: 1.8em !important;
            }
            
            .reveal h2 {
                font-size: 1.5em !important;
            }
            
            .reveal h3 {
                font-size: 1.3em !important;
            }
            
            .stats-grid {
                grid-template-columns: 1fr !important;
            }
        }
        
        @media screen and (max-width: 480px) {
            .reveal .slides section {
                padding: 10px !important;
                margin: 0 5px 15px 5px !important;
            }
            
            .reveal h1 {
                font-size: 1.5em !important;
            }
            
            .content-card {
                padding: 1rem !important;
            }
        }
        
        /* Print styles */
        @media print {
            .reveal .slides section {
                page-break-after: always;
                page-break-inside: avoid;
            }
        }
"@
        
        # Insert the new CSS after the opening style tag
        $content = $content -replace '(<style>)', "`$1`n$scrollingCSS"
    }
    
    # 3. Update Reveal.js configuration to disable slide navigation
    if ($content -match 'Reveal\.initialize\s*\(\s*\{') {
        # Add embedded: true to make it work better for scrolling
        if ($content -notmatch 'embedded:') {
            $content = $content -replace '(Reveal\.initialize\s*\(\s*\{)', @"
`$1
            embedded: true,
            width: '100%',
            height: '100%',
            margin: 0,
            minScale: 1,
            maxScale: 1,
"@
        }
    }
    
    # Save the updated content
    $content | Set-Content -Path $file.FullName -Encoding UTF8 -NoNewline
    Write-Host "✓ Fixed $($file.Name)" -ForegroundColor Green
}

Write-Host "`n✅ All slides have been fixed for scrolling!" -ForegroundColor Green
Write-Host "Changes made:" -ForegroundColor Cyan
Write-Host "  - Viewport meta tag updated to allow user scaling" -ForegroundColor White
Write-Host "  - Added CSS for proper vertical scrolling" -ForegroundColor White
Write-Host "  - Made layouts responsive for mobile devices" -ForegroundColor White
Write-Host "  - Disabled reveal.js slide navigation in favor of scrolling" -ForegroundColor White
Write-Host "  - Added smooth scrolling support for touch devices" -ForegroundColor White