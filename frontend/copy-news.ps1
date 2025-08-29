# newsフォルダをfrontend/publicにコピー
Write-Host "Copying news data to frontend/public..." -ForegroundColor Yellow

$sourcePath = "../news"
$destPath = "public/news"

# publicディレクトリがなければ作成
if (-not (Test-Path "public")) {
    New-Item -ItemType Directory -Force -Path "public" | Out-Null
}

# 既存のnewsフォルダを削除
if (Test-Path $destPath) {
    Remove-Item -Recurse -Force $destPath
}

# newsフォルダをコピー
Copy-Item -Recurse -Force $sourcePath $destPath
Write-Host "News data copied successfully!" -ForegroundColor Green