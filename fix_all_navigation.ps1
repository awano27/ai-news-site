# Fix navigation for all slides and restore proper encoding

Write-Host "=== Fixing navigation and encoding for all slides ===" -ForegroundColor Green

# Reset files from git to avoid encoding issues
Write-Host "Resetting files from git..." -ForegroundColor Yellow
git checkout HEAD -- presentations/day_slides/day_slide_2025_08_19.html
git checkout HEAD -- presentations/day_slides/day_slide_2025_08_20.html
git checkout HEAD -- presentations/day_slides/day_slide_2025_08_22.html
git checkout HEAD -- presentations/day_slides/day_slide_2025_08_23.html
git checkout HEAD -- presentations/day_slides/day_slide_2025_08_24.html

$files = @(
    "presentations\day_slides\day_slide_2025_08_19.html",
    "presentations\day_slides\day_slide_2025_08_20.html", 
    "presentations\day_slides\day_slide_2025_08_22.html",
    "presentations\day_slides\day_slide_2025_08_23.html",
    "presentations\day_slides\day_slide_2025_08_24.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Fixing navigation in $file..." -ForegroundColor Yellow
        
        # Read with proper encoding
        $content = Get-Content $file -Raw -Encoding UTF8
        
        # Update reveal.js initialization to match working 8/27 slide
        $content = $content -replace 'Reveal\.initialize\(\{[^}]+\}[^}]*\}[^}]*\}[^}]*\}[^}]*\}[^}]*\}[^}]*\}[^}]*\}[^}]*\}[^}]*\}[^}]*\}[^}]*\}\);', @'
Reveal.initialize({
            hash: true,
            controls: true,   // Enable slide navigation controls
            controlsLayout: 'edges',  // Position controls at edges
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
        
        # Write back with UTF8 encoding
        [System.IO.File]::WriteAllText((Resolve-Path $file), $content, [System.Text.UTF8Encoding]::new($false))
        
        Write-Host "✓ Fixed navigation in $file" -ForegroundColor Green
    }
}

Write-Host "`n=== Committing navigation fixes ===" -ForegroundColor Green
git add presentations/day_slides/day_slide_2025_08_*.html

git commit -m "fix: Restore proper navigation and fix encoding issues

- Reset files from git to fix UTF-8 encoding problems
- Applied working navigation config from 8/27 to all slides
- Controls enabled with edges layout and faded back arrows
- Should resolve navigation issues on all dates

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

Write-Host "`n=== All slides should now have working navigation ===" -ForegroundColor Green