# Final comprehensive fix for all slides

Write-Host "=== Final comprehensive fix ===" -ForegroundColor Green

$files = @(
    "presentations\day_slides\day_slide_2025_08_19.html",
    "presentations\day_slides\day_slide_2025_08_20.html", 
    "presentations\day_slides\day_slide_2025_08_23.html",
    "presentations\day_slides\day_slide_2025_08_24.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Processing $file..." -ForegroundColor Yellow
        
        # Read with UTF-8 encoding
        $content = [System.IO.File]::ReadAllText((Resolve-Path $file), [System.Text.Encoding]::UTF8)
        
        # Update reveal.js to 4.4.0
        $content = $content -replace 'reveal\.js@4\.3\.1', 'reveal.js@4.4.0'
        
        # Remove navigation slide section completely
        $content = $content -replace '(?s)\s*<!-- Navigation Slide -->.*?</section>\s*</div>', '</div>'
        
        # Remove nav-buttons CSS
        $content = $content -replace '(?s)\.navigation-card \{[^}]*\}', ''
        $content = $content -replace '(?s)\.nav-buttons \{[^}]*\}', ''
        $content = $content -replace '(?s)\.nav-btn \{[^}]*\}', ''
        $content = $content -replace '(?s)\.nav-btn:hover \{[^}]*\}', ''
        
        # Update reveal.js config to match working template
        $content = $content -replace '(?s)Reveal\.initialize\(\{[^}]*\}\);', @'
Reveal.initialize({
            hash: true,
            controls: true,
            controlsLayout: 'edges',
            controlsBackArrows: 'faded',
            progress: true,
            center: false,
            transition: 'slide',
            backgroundTransition: 'fade',
            keyboard: true,
            overview: true,
            touch: true,
            loop: false
        });'@
        
        # Write back with proper UTF-8 encoding (no BOM)
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText((Resolve-Path $file), $content, $utf8NoBom)
        
        Write-Host "✓ Fixed $file" -ForegroundColor Green
    }
}

Write-Host "`n=== Committing fixes ===" -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_*.html

git commit -m "fix: Final comprehensive fix for all slides

- Updated reveal.js to 4.4.0 for all slides
- Removed navigation buttons completely
- Fixed UTF-8 encoding without BOM
- Applied working reveal.js configuration
- Should resolve all character encoding and navigation issues

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "`n=== All slides should now be fixed ===" -ForegroundColor Green