# Skill: デイリーAIニューススライド生成

このスキルは、指定した日付のAIニュース情報（テキストおよびPDF）から、ウェブサイト用のスライドHTMLを自動生成し、インデックスを更新してGitに反映させるための最適化されたワークフローです。

## 📋 このスキルの対象者

- ClaudeCodeを使ってAIニューススライドを効率的に生成したい方
- 日次のコンテンツ更新作業を自動化したい方
- GitHubページでスライドを公開している方

## 🎯 このスキルで実現できること

1. PDFからスライド画像への自動変換
2. テーマに合わせたHTMLスライドの自動生成（シンプル構成）
3. インデックスページへの自動追加
4. Git コミット・プッシュまでの一連の自動化

## 🚀 使い方

### 基本的な使い方

```
MMDD（例: 0116）のスライドを作成して
```

または

```
input/dayのMMDD.txt, MMDD.png, MMDD-*.pdfからスライドを生成して
```

### より詳細な指定

```
0116のスライドを「remio 2.0 戦略的導入ガイド」というタイトルで作成して
```

## 📁 必要なファイル構成

```
input/day/
  ├── MMDD.txt         # ニュースの要約テキスト（概要・特徴など）
  ├── MMDD.png         # サマリ画像（最初に大きく表示）
  └── MMDD-Topic.pdf   # スライド元PDF（全ページを画像化）
```

## ⚙️ 処理フロー

### 1. PDF画像変換（PyMuPDF使用）
- `input/day/MMDD-*.pdf` を検索
- 各ページを高解像度（2倍ズーム）でJPG画像に変換
- `input/day/MMDD_slides/slide_001.jpg` 形式で保存
- PyMuPDF (fitz) を使用: `page.get_pixmap(matrix=fitz.Matrix(2, 2))`

### 2. スライドHTML生成（シンプル構成）
- `MMDD.txt` の内容を分析してテーマ・タイトルを抽出
- テーマに合わせたCSS変数（カラースキーム）を設定
- **シンプル構成で生成**:
  1. ヘッダー（日付バッジ、タイトル、サブタイトル）
  2. サマリセクション:
     - **MMDD.png をサマリ画像として最初に大きく表示**
     - 簡潔な概要テキスト（highlight-box）
     - 統計グリッド（4つの数値）
  3. スライドセクション:
     - PDFダウンロードリンク
     - 全スライド画像を縦に並べて表示
  4. フッター
- `presentations/day_slides/day_slide_YYYY_MM_DD.html` として保存

### 3. インデックス更新（4ファイル）
以下のファイルを全て更新:

1. **`presentations/day_slides_index.html`**
   - `<ul class="slides">` の先頭に新エントリを追加

2. **`presentations/day_slides_list.html`**
   - 日付範囲を更新
   - `slides-grid` の先頭に新カードを追加

3. **`presentations/index.html`**
   - ヒーローCTAボタンのhref更新
   - 統計セクションの日付更新
   - クイックリンクセクション更新
   - JavaScript動的コンテンツ（if-elseの**先頭**に追加）
   - JavaScriptフォールバック表示更新

4. **`index.html`（ルート）**
   - ヒーローボタンリンクを最新スライドに更新

### 4. Git反映
- 変更をステージング（HTML + スライド画像）
- コミットメッセージを自動生成
- `git stash && git pull --rebase origin main && git stash pop` でコンフリクト回避
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
