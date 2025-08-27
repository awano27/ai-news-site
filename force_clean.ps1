# 完全にクリーンなリポジトリを作成
Write-Host "完全クリーンなリポジトリを作成します..." -ForegroundColor Yellow

# 1. 現在の重要なファイルをバックアップ
$backupDir = "../ai-news-site-clean"
Write-Host "バックアップ作成中: $backupDir" -ForegroundColor Cyan

# バックアップディレクトリを作成
if (Test-Path $backupDir) {
    Remove-Item -Recurse -Force $backupDir
}
New-Item -ItemType Directory -Path $backupDir | Out-Null

# 必要なファイルのみコピー（.git, node_modules, .serenaを除外）
$excludeList = @(".git", "node_modules", ".serena", ".venv", "__pycache__", "*.pkl", "*.cache", "logs", "dist")
$filesToCopy = Get-ChildItem -Path "." -Recurse | Where-Object { 
    $path = $_.FullName.Replace((Get-Location).Path, "")
    $excluded = $false
    foreach ($exclude in $excludeList) {
        if ($path -like "*$exclude*") {
            $excluded = $true
            break
        }
    }
    -not $excluded
}

Write-Host "ファイルをコピー中..." -ForegroundColor Cyan
foreach ($file in $filesToCopy) {
    $relativePath = $file.FullName.Replace((Get-Location).Path, "")
    $targetPath = Join-Path $backupDir $relativePath
    $targetDir = Split-Path $targetPath -Parent
    
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    if (-not $file.PSIsContainer) {
        Copy-Item -Path $file.FullName -Destination $targetPath -Force
    }
}

# 2. クリーンディレクトリに移動
Set-Location $backupDir

# 3. 新しいGitリポジトリを初期化
Write-Host "`n新しいGitリポジトリを初期化中..." -ForegroundColor Green
git init

# 4. すべてのファイルを追加
git add -A

# 5. 初期コミット
Write-Host "初期コミット作成中..." -ForegroundColor Green
git commit -m "Initial commit: AI News Intelligence Platform v2.0

Complete system with:
- 26 daily slides with Reveal.js
- Full 30-position ranking report  
- Integrated dashboard
- Clean navigation without duplicates
- All features working properly

No large files or cache included"

# 6. リモートを追加
git remote add origin https://github.com/awano27/ai-news-site.git

# 7. 強制プッシュ
Write-Host "`n強制プッシュ実行中..." -ForegroundColor Yellow
git push -u origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 成功！クリーンなリポジトリが作成されました" -ForegroundColor Green
    Write-Host "`n次の手順:" -ForegroundColor Cyan
    Write-Host "1. cd $backupDir" -ForegroundColor White
    Write-Host "2. 古いディレクトリ (ai-news-site) は削除可能です" -ForegroundColor White
    Write-Host "`nGitHub Pages URL:" -ForegroundColor Cyan
    Write-Host "https://awano27.github.io/ai-news-site/" -ForegroundColor Green
    Write-Host "https://awano27.github.io/ai-news-site/presentations/" -ForegroundColor Green
} else {
    Write-Host "エラーが発生しました" -ForegroundColor Red
}