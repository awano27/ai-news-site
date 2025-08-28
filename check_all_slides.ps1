# Check all slides and identify problematic ones

Write-Host "=== Checking all slides for issues ===" -ForegroundColor Green

$slides = @(
    "day_slide_2025_08_19.html",
    "day_slide_2025_08_20.html", 
    "day_slide_2025_08_22.html",
    "day_slide_2025_08_23.html",
    "day_slide_2025_08_24.html",
    "day_slide_2025_08_27.html"
)

foreach ($slide in $slides) {
    $filePath = "presentations\day_slides\$slide"
    if (Test-Path $filePath) {
        Write-Host "`nChecking $slide..." -ForegroundColor Yellow
        
        # Check file size
        $size = (Get-Item $filePath).Length
        Write-Host "File size: $size bytes"
        
        # Check encoding
        $content = Get-Content $filePath -Raw -Encoding UTF8
        if ($content -match '<!DOCTYPE html>') {
            Write-Host "✓ Valid HTML structure" -ForegroundColor Green
        } else {
            Write-Host "✗ Invalid HTML structure" -ForegroundColor Red
        }
        
        # Check for reveal.js version
        if ($content -match 'reveal\.js@([\d\.]+)') {
            Write-Host "Reveal.js version: $($matches[1])"
        }
        
        # Check for controls setting
        if ($content -match 'controls:\s*(true|false)') {
            Write-Host "Controls: $($matches[1])"
        }
        
        # Check for encoding issues (look for garbled characters)
        if ($content -match '[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]') {
            Write-Host "⚠ Potential encoding issues detected" -ForegroundColor Yellow
        } else {
            Write-Host "✓ No obvious encoding issues" -ForegroundColor Green
        }
        
        # Check title
        if ($content -match '<title>([^<]+)</title>') {
            Write-Host "Title: $($matches[1])"
        }
    } else {
        Write-Host "✗ $slide not found" -ForegroundColor Red
    }
}

Write-Host "`n=== Analysis complete ===" -ForegroundColor Green