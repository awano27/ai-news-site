# Check ALL day slides for encoding issues and other problems

Write-Host "=== Checking ALL day slides ===" -ForegroundColor Green

# Get all day slide files
$slideFiles = Get-ChildItem "presentations\day_slides\day_slide_*.html" | Sort-Object Name

Write-Host "Found $($slideFiles.Count) slide files" -ForegroundColor Yellow

$problematicFiles = @()

foreach ($file in $slideFiles) {
    Write-Host "`nChecking $($file.Name)..." -ForegroundColor Yellow
    
    # Check file size
    $size = $file.Length
    Write-Host "File size: $size bytes"
    
    try {
        # Check encoding
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        
        if ($content -match '<!DOCTYPE html>') {
            Write-Host "✓ Valid HTML structure" -ForegroundColor Green
        } else {
            Write-Host "✗ Invalid HTML structure" -ForegroundColor Red
            $problematicFiles += $file.Name
        }
        
        # Check for reveal.js version
        if ($content -match 'reveal\.js@([\d\.]+)') {
            Write-Host "Reveal.js version: $($matches[1])"
            if ($matches[1] -ne "4.4.0") {
                Write-Host "⚠ Needs update to 4.4.0" -ForegroundColor Yellow
                $problematicFiles += $file.Name
            }
        }
        
        # Check for controls setting
        if ($content -match 'controls:\s*(true|false)') {
            Write-Host "Controls: $($matches[1])"
        } else {
            Write-Host "⚠ No controls setting found" -ForegroundColor Yellow
        }
        
        # Check for navigation buttons (should be removed)
        if ($content -match 'nav-buttons|navigation-card') {
            Write-Host "⚠ Navigation buttons still present" -ForegroundColor Yellow
            $problematicFiles += $file.Name
        } else {
            Write-Host "✓ No navigation buttons" -ForegroundColor Green
        }
        
        # Check for encoding issues (look for garbled Japanese characters)
        if ($content -match '繝｜縺｜蜀｜譎｜譛｜蟷ｴ|繧ｹ繝ｩ繧､繝|繧｢繧､') {
            Write-Host "✗ Character encoding issues detected" -ForegroundColor Red
            $problematicFiles += $file.Name
        } else {
            Write-Host "✓ No obvious encoding issues" -ForegroundColor Green
        }
        
        # Check title
        if ($content -match '<title>([^<]+)</title>') {
            $title = $matches[1]
            Write-Host "Title: $title"
            if ($title -match '繝｜縺｜蜀｜譎｜譛｜蟷ｴ') {
                Write-Host "✗ Title has encoding issues" -ForegroundColor Red
                $problematicFiles += $file.Name
            }
        }
        
    } catch {
        Write-Host "✗ Error reading file: $_" -ForegroundColor Red
        $problematicFiles += $file.Name
    }
}

$uniqueProblematic = $problematicFiles | Select-Object -Unique

Write-Host "`n=== SUMMARY ===" -ForegroundColor Green
Write-Host "Total files checked: $($slideFiles.Count)"
Write-Host "Problematic files: $($uniqueProblematic.Count)"

if ($uniqueProblematic.Count -gt 0) {
    Write-Host "`nFiles needing fixes:" -ForegroundColor Red
    foreach ($file in $uniqueProblematic) {
        Write-Host "- $file" -ForegroundColor Red
    }
} else {
    Write-Host "All files appear to be in good condition!" -ForegroundColor Green
}

Write-Host "`n=== Analysis complete ===" -ForegroundColor Green