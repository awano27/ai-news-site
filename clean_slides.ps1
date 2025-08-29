# Daily Slidesから不要なナビゲーションボタンを削除
Write-Host "Daily Slidesのクリーンアップ開始..." -ForegroundColor Yellow

$slideFiles = Get-ChildItem -Path "presentations/day_slides/*.html"
$cleanedCount = 0

foreach ($file in $slideFiles) {
    Write-Host "処理中: $($file.Name)" -ForegroundColor Cyan
    
    $content = Get-Content $file.FullName -Raw
    $originalLength = $content.Length
    
    # ナビゲーションdivを削除
    $pattern1 = '    <div class="navigation">[\s\S]*?</div>\r?\n'
    $content = $content -replace $pattern1, ''
    
    # ナビゲーション関連のCSSを削除
    $pattern2 = '        \.navigation \{[\s\S]*?\}\r?\n\r?\n        /\* Reveal\.js.*?\*/[\s\S]*?\.nav-button:hover \{[\s\S]*?\}'
    $content = $content -replace $pattern2, ''
    
    # 単独のnavigationクラスCSSを削除
    $pattern3 = '        \.navigation \{[\s\S]*?\}'
    $content = $content -replace $pattern3, ''
    
    # nav-button関連のCSSを削除
    $pattern4 = '        \.nav-button \{[\s\S]*?\}\r?\n\r?\n        \.nav-button:hover \{[\s\S]*?\}'
    $content = $content -replace $pattern4, ''
    
    # Reveal.js controlsのz-index設定も削除
    $pattern5 = '        /\* Reveal\.js.*?\*/[\s\S]*?\.reveal \.controls \{[\s\S]*?\}'
    $content = $content -replace $pattern5, ''
    
    if ($content.Length -ne $originalLength) {
        Set-Content -Path $file.FullName -Value $content -NoNewline
        $cleanedCount++
        Write-Host "  ✓ クリーンアップ完了" -ForegroundColor Green
    } else {
        Write-Host "  - 変更なし" -ForegroundColor Gray
    }
}

Write-Host "`n完了！" -ForegroundColor Green
Write-Host "$cleanedCount / $($slideFiles.Count) ファイルがクリーンアップされました。" -ForegroundColor Cyan

Write-Host "`nReveal.jsのコントロールのみが残っています:" -ForegroundColor Yellow
Write-Host "- 右下の矢印でスライドナビゲーション" -ForegroundColor Gray
Write-Host "- キーボードの矢印キーも使用可能" -ForegroundColor Gray
Write-Host "- ESCキーでスライド一覧表示" -ForegroundColor Gray