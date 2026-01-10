# Skill: デイリーAIニューススライド生成

このスキルは、指定した日付のAIニュース情報（テキストおよびPDF）から、ウェブサイト用のスライドHTMLを自動生成し、インデックスを更新してGitに反映させるための最適化されたワークフローです。

## 📋 このスキルの対象者

- ClaudeCodeを使ってAIニューススライドを効率的に生成したい方
- 日次のコンテンツ更新作業を自動化したい方
- GitHubページでスライドを公開している方

## 🎯 このスキルで実現できること

1. PDFからスライド画像への自動変換
2. テーマに合わせたHTMLスライドの自動生成
3. インデックスページへの自動追加
4. Git コミット・プッシュまでの一連の自動化

## 🚀 使い方

### 基本的な使い方

```
MMDD（例: 0105）のスライドを作成して
```

または

```
input/dayのMMDD.txt, MMDD.png, MMDD-*.pdfからスライドを生成して
```

### より詳細な指定

```
0105のスライドを「Sentient Sparks: オープンソースAGIコミュニティプログラム」というタイトルで作成して
```

## 📁 必要なファイル構成

```
input/day/
  ├── MMDD.txt         # ニュースの要約テキスト
  ├── MMDD.png         # トップ画像
  └── MMDD-Topic.pdf   # 技術解説等の元PDF
```

## ⚙️ 処理フロー

### 1. PDF画像変換
- `input/day/MMDD-*.pdf` を検索
- 各ページを高解像度（2倍ズーム）でJPG画像に変換
- `input/day/MMDD_slides/slide_001.jpg` 形式で保存

### 2. スライドHTML生成
- `MMDD.txt` の内容を分析してテーマを抽出
- テーマに合わせたCSS変数（カラースキーム）を設定
- `base_template.html` をベースに動的にHTMLを生成
- `presentations/day_slides/day_slide_YYYY_MM_DD.html` として保存

### 3. インデックス更新
- `presentations/day_slides_index.html` を読み込み
- 新しいスライドのエントリを日付順に追加
- Git conflictマーカーがあれば自動クリーンアップ

### 4. トップページ更新
- `index.html` のヒーローボタンリンクを最新スライドに更新
  - `<!-- Updated: YYYY-MM-DD -->` コメントを更新
  - `id="latestSlideHeroBtn"` の `href` を新しいスライドに変更

### 5. Git反映
- 変更をステージング
- コミットメッセージを自動生成
- `git pull --rebase` で最新を取得
- コンフリクトがあれば解決
- リモートにプッシュ

## 🎨 テーマカスタマイズ

スライドのテーマは内容に応じて自動的に設定されます：

### AGI/コミュニティテーマ（紫×ティール）
```css
--primary: #7c3aed;
--accent: #14b8a6;
--bg-light: #f5f3ff;
--bg-dark: #1e1b4b;
```

### 技術/開発テーマ（青×水色）
```css
--primary: #007bff;
--accent: #17a2b8;
--bg-light: #f8f9fa;
--bg-dark: #212529;
```

## ⚠️ 注意点

### スクリプトの再利用
- convert_MMDD.py と create_slide_MMDD.py が自動生成されます
- これらは前日のスクリプトをコピーして日付と内容を更新したものです

### Git操作
- 自動的に `git pull --rebase` を実行します
- コンフリクトは自動解決を試みますが、複雑な場合は手動介入が必要です

### HTMLテンプレート
- `base_template.html` が存在することを前提とします
- プレースホルダー: `{{FULL_TITLE}}`, `{{CSS_VARS_BLOCK}}`, `{{H1_TITLE}}` など

## 🔧 トラブルシューティング

### PDFが見つからない場合
```
Error: No PDF file found for MMDD in input/day/
```
→ `input/day/MMDD-*.pdf` 形式のファイルが存在するか確認してください

### スライド枚数が異なる場合
- PDFのページ数が前日と異なる場合、create_slide_MMDD.py内のループ範囲が自動調整されます
- 画像変換時に実際のページ数が表示されます

### Git コンフリクト
- 複数人で同時編集している場合、インデックスファイルでコンフリクトが発生する可能性があります
- 自動解決を試みますが、失敗した場合は手動でマージしてください

## 📊 成果物の確認

生成されたスライドは以下のURLでアクセスできます：

```
https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_YYYY_MM_DD.html
```

インデックスページ：
```
https://awano27.github.io/ai-news-site/presentations/day_slides_index.html
```

トップページ（最新スライドへのリンク）：
```
https://awano27.github.io/ai-news-site/index.html
```

## 💡 Tips

### 効率的な運用
1. 毎日決まった時間にinput/dayフォルダに素材を配置
2. ClaudeCodeに「今日のスライドを作成して」と指示するだけ
3. 自動的にGitHubページに反映される

### カスタマイズ
- CSS変数を変更することで、サイト全体のテーマを統一できます
- `base_template.html` を編集することで、共通レイアウトを一括変更できます

### バッチ処理
複数日分を一度に生成する場合：
```
0103から0105までのスライドを作成して
```

## 🔄 更新履歴

- 2026-01-05: ClaudeCode向けに最適化、自動コンフリクト解決機能を追加
- 初版: Python スクリプトベースのワークフロー

## 📝 関連ドキュメント

- [SKILL.md](../../SKILL.md) - オリジナルの手動ワークフロー
- [base_template.html](../../base_template.html) - HTMLテンプレート
