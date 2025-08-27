# ディレクトリ作成スクリプト
Write-Host "Creating necessary directories..." -ForegroundColor Yellow

# ディレクトリのリスト
$directories = @("logs", "news", "dist", "src")

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "   Created: $dir" -ForegroundColor Green
    }
    else {
        Write-Host "   Exists: $dir" -ForegroundColor Gray
    }
}

Write-Host "Directory creation completed!" -ForegroundColor Green