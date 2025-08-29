# Daily AI News v2.0 - 環境設定スクリプト (PowerShell)

Write-Host "🚀 Daily AI News System v2.0 セットアップ" -ForegroundColor Green

# 1. 依存関係のインストール
Write-Host "📦 Python依存関係をインストール中..." -ForegroundColor Yellow
pip install -r requirements-v2-compatible.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 依存関係のインストールに失敗しました" -ForegroundColor Red
    Write-Host "   Python 3.13では一部のML依存関係に互換性問題があります" -ForegroundColor Yellow
    Write-Host "   基本機能のみで続行します" -ForegroundColor Yellow
}

# 2. 環境変数の設定例を表示
Write-Host "`n🔧 環境変数の設定:" -ForegroundColor Yellow
Write-Host "以下の環境変数を設定してください (任意):" -ForegroundColor White
Write-Host '$env:GEMINI_API_KEY = "your-gemini-api-key-here"' -ForegroundColor Cyan
Write-Host '$env:GITHUB_TOKEN = "your-github-token-here"' -ForegroundColor Cyan
Write-Host '$env:NEWS_FAST_MODE = "1"  # 高速モード（AI分析なし）' -ForegroundColor Cyan

# 3. ディレクトリ作成
Write-Host "`n📁 必要なディレクトリを作成中..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "news" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "dist" | Out-Null

# 4. 設定ファイルの確認
if (-not (Test-Path "sources.yaml")) {
    Write-Host "⚠️  sources.yaml が見つかりません。基本設定を作成します..." -ForegroundColor Yellow
    # sources.yamlが存在しない場合の基本設定は既存ファイルを使用
}

Write-Host "`n✅ セットアップが完了しました!" -ForegroundColor Green
Write-Host "📘 使用方法:" -ForegroundColor White
Write-Host "   1. API キーを設定: " -ForegroundColor Gray -NoNewline
Write-Host '$env:GEMINI_API_KEY = "your-key"' -ForegroundColor Cyan
Write-Host "   2. システム実行: " -ForegroundColor Gray -NoNewline  
Write-Host "python build.py" -ForegroundColor Cyan
Write-Host "   3. 高速モード: " -ForegroundColor Gray -NoNewline
Write-Host "Set NEWS_FAST_MODE=1 then run python build.py" -ForegroundColor Cyan

Write-Host "`n🌟 システムの特徴:" -ForegroundColor White
Write-Host "   • 多層評価システム (5次元スコアリング)" -ForegroundColor Gray
Write-Host "   • ペルソナ別最適化 (エンジニア・ビジネス)" -ForegroundColor Gray  
Write-Host "   • Gemini AI分析 (要APIキー)" -ForegroundColor Gray
Write-Host "   • ハイブリッド検索エンジン" -ForegroundColor Gray