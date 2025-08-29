# Apply 08/27 excellent styling to all other slides
Write-Host "Applying 08/27 slide styling to all slides..." -ForegroundColor Green

$templateFile = "presentations/day_slides/day_slide_2025_08_27.html"
$slidesDir = "presentations/day_slides"
$slideFiles = Get-ChildItem -Path $slidesDir -Filter "*.html" | Where-Object { $_.Name -ne "day_slide_2025_08_27.html" }

# Extract the perfect CSS from 08/27
$templateContent = Get-Content -Path $templateFile -Raw -Encoding UTF8

# Extract the excellent scrolling CSS section
$perfectCSS = @'

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
'@

# Perfect Reveal.js configuration from 08/27
$perfectRevealConfig = @'
        Reveal.initialize({
            embedded: true,
            width: '100%',
            height: '100%',
            margin: 0,
            minScale: 1,
            maxScale: 1,
            hash: false,
            controls: false,  // Disable slide navigation controls for scrolling
            controlsLayout: 'edges',
            controlsBackArrows: 'faded',
            progress: false,  // Disable progress bar for scrolling
            center: false,
            transition: 'none',  // Disable transitions for scrolling
            backgroundTransition: 'none',
            keyboard: false,  // Disable keyboard navigation for scrolling
            overview: false,  // Disable overview mode
            touch: false,     // Disable touch navigation for scrolling
            loop: false,
            fragments: false  // Disable fragment animations
        });
'@

$fixedCount = 0

foreach ($file in $slideFiles) {
    Write-Host "Processing $($file.Name)..." -ForegroundColor Yellow
    
    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        
        # 1. Fix viewport meta tag
        $content = $content -replace 'maximum-scale=1\.0,?\s*user-scalable=no', 'user-scalable=yes'
        $content = $content -replace 'maximum-scale=1\.0,?\s*', ''
        
        # 2. Add/replace with perfect CSS
        if ($content -match '(<style>\s*)') {
            # Remove existing scrolling fixes if any
            $content = $content -replace '/\* Scrolling fixes[^}]*\*/', ''
            $content = $content -replace 'html,\s*body\s*\{[^}]*overflow[^}]*\}', ''
            
            # Add the perfect CSS right after <style>
            $content = $content -replace '(<style>\s*)', "`$1$perfectCSS`n        "
        }
        
        # 3. Replace Reveal.js configuration with perfect one
        $content = $content -replace 'Reveal\.initialize\s*\(\s*\{[^}]*\}\s*\);?', $perfectRevealConfig
        
        # 4. Ensure proper charset
        if ($content -notmatch 'charset.*utf-8') {
            $content = $content -replace '<meta charset="[^"]*">', '<meta charset="utf-8">'
        }
        
        # Save with UTF-8 encoding
        $content | Set-Content -Path $file.FullName -Encoding UTF8 -NoNewline
        $fixedCount++
        Write-Host "✓ Enhanced $($file.Name) with 08/27 styling" -ForegroundColor Green
        
    } catch {
        Write-Host "✗ Error processing $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Successfully applied 08/27 excellent styling to $fixedCount slides!" -ForegroundColor Green
Write-Host "`nIMPROVEMENTS APPLIED:" -ForegroundColor Cyan
Write-Host "✅ Perfect scrolling behavior from 08/27" -ForegroundColor White
Write-Host "✅ Responsive design for all screen sizes" -ForegroundColor White  
Write-Host "✅ Clean reveal.js configuration" -ForegroundColor White
Write-Host "✅ Consistent viewport settings" -ForegroundColor White
Write-Host "✅ Mobile-optimized layouts" -ForegroundColor White
Write-Host "`nAll slides now have the same excellent readability as 08/27!" -ForegroundColor Green