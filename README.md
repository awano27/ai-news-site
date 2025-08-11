## Daily AI News サイト — セットアップと自動更新

このフォルダは AI ニュースの自動収集・要約・配信サイトです。`script/build_news.py` が `news/latest.json` を生成し、`index.html` + `news.js` がブラウザ表示します。

### 1) ローカル実行（Windows）
1. PowerShell を開く
2. ディレクトリへ移動
   ```powershell
   cd ai-news-site
   ```
3. 依存インストールとビルド
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -U pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe .\script\build_news.py
   ```
4. `news/latest.json` が作成されます。`index.html` を開くと最新が表示されます。

### 2) SNS/X 連携（任意）
- X の公式APIを使う場合は環境変数 `X_BEARER_TOKEN` を設定してください。
- 代替として `sources.yaml` の `x_rss_base`/`x_rss_accounts` を利用可能です（不安定時は自動スキップ）。

### 3) 毎日自動更新（Windows タスク スケジューラ）
1. タスク スケジューラを開き、新しいタスクを作成
2. トリガー: 毎日 07:30 等
3. 操作: プログラム/スクリプトに以下を指定
   - プログラム/スクリプト: `powershell.exe`
   - 引数の追加: `-ExecutionPolicy Bypass -File "C:\\Users\\<あなたのユーザー名>\\ai-news-site\\script\\run_daily.ps1" -Push`
   - 開始(作業)ディレクトリ: `C:\\Users\\<あなたのユーザー名>\\ai-news-site`

### 4) GitHub Actions での自動更新（任意）
`.github/workflows/update-news.yml` を使うと、毎日ビルドして `news/` をコミットできます。必要に応じてリポジトリに合わせて `permissions` と `secrets` を設定してください。

### 5) カスタマイズ
- 収集元は `sources.yaml` を編集
- スコアリングやカテゴリ判定は `script/build_news.py` の `score`/`classify` を調整
- LLM 要約を使う場合は `OPENAI_API_KEY` を設定（`OPENAI_MODEL` も任意指定可）


