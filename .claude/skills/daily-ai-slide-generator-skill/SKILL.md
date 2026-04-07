# デイリーAIニューススライド生成スキル

## 概要

日付を指定するだけで、AIニュースのPDF資料からストーリー駆動のウェブスライドを自動生成し、GitHubページに公開するまでの全工程を自動化します。

## トリガー

- `MMDDのスライドを作成して`
- `今日のスライドを生成して`
- `0405のスライドをストーリーを意識して作成してください`

## 必要な入力ファイル

```
input/day/
  ├── MMDDslide.txt    # スライド専用テキスト（優先）
  ├── MMDD.txt         # ニュース要約（slide.txtがない場合のフォールバック）
  ├── MMDD.png         # カバー画像
  └── MMDD-Topic.pdf   # スライド元PDF（ファイル名のTopic部分は自動検出）
```

### テキストファイル優先順位

1. **`MMDDslide.txt`** が存在 → これを使う（ストーリー構成済み）
2. **`MMDD.txt`** のみ → これを使う

## 実行手順（チェックリスト）

### Step 1: 入力ファイル確認

```bash
# ファイル存在確認
ls input/day/MMDD*
# PDF ページ数確認
python -c "import fitz; doc = fitz.open('input/day/MMDD-*.pdf'); print(f'Pages: {doc.page_count}')"
```

### Step 2: テキスト読み込み → テーマ・構成決定

- `MMDDslide.txt`（または`MMDD.txt`）を読み込み
- 内容に応じてカラーテーマを選択（過去スライドと被らないように）
- ストーリー構成（章立て）を決定

### Step 3: 生成スクリプト作成 (`tmp_gen_MMDD_html.py`)

以下の構造で Python スクリプトを作成:

```python
#!/usr/bin/env python3
import os, base64, fitz
from PIL import Image

IMG_DIR = "tmp_MMDD"
os.makedirs(IMG_DIR, exist_ok=True)

# 1. PNG → JPG (cover, quality=82)
# 2. PDF → JPG (各ページ, matrix=1.5, jpg_quality=75)
# 3. base64エンコード
# 4. HTML生成（ストーリー駆動レイアウト）
# 5. ファイル出力
```

### Step 4: HTML生成 → 実行

```bash
python tmp_gen_MMDD_html.py
# 出力: presentations/day_slides/day_slide_2026_MM_DD.html
```

### Step 5: 4ファイル更新

以下の4ファイルを**必ず全て更新**する:

| # | ファイル | 更新箇所 |
|---|---------|---------|
| 1 | `presentations/index.html` | hero CTA href / stat-label日付+説明 / highlight-link href / quick-link href+タイトル+説明 / JS if-elseチェーン先頭に追加 / フォールバック表示 |
| 2 | `presentations/day_slides_index.html` | 月の件数+1 / リスト先頭に`<li>`追加（新月の場合は`<details>`セクション新規作成） |
| 3 | `presentations/day_slides_list.html` | 日付範囲テキスト更新 / slides-grid先頭にカード追加 |
| 4 | `presentations/index.html` の6箇所 | (1) hero-cta (2) stat-label (3) highlight-link (4) quick-link (5) JS if-else先頭 (6) フォールバック |

> **注意**: `index.html`(ルート)の`latestSlideHeroBtn`と`latestSlidePathCard`はJSで自動更新されるため、通常は更新不要。

### Step 6: コミット & プッシュ

```bash
git add presentations/day_slides/day_slide_2026_MM_DD.html \
      presentations/index.html \
      presentations/day_slides_index.html \
      presentations/day_slides_list.html
git commit -m "add: [Topic] slide (MM/DD) with full site integration"
# リモートとの同期（コンフリクト自動解決）
git stash && git pull --rebase origin main && git stash pop; git push origin main
```

コンフリクト発生時: `git checkout --theirs <file> && git add <file> && git rebase --continue`

## HTMLテンプレート構造（ストーリー駆動レイアウト）

### 必須セクション

```
header
  ├── breaking-badge (日付 + 製品名)
  ├── h1 (製品の一言紹介 — ストーリーではなく「何ができるか」)
  ├── subtitle (技術的な特徴サマリー)
  └── date

main
  ├── 製品紹介セクション (カバー画像 + stats-grid)
  ├── ストーリーブロック群 (story-block.ch1〜ch5)
  │   ├── 各章: data-chapter属性 + 色分けボーダー
  │   ├── .scene (イタリック背景ブロック — 情景描写)
  │   └── PDFスライド画像 (inline-slides)
  ├── 技術詳細 (highlight-box / feature-grid / vs-grid など)
  ├── 残りPDFスライド
  ├── まとめ (summary-grid)
  └── 参考リンク (links-grid)

footer
  ├── アーカイブ情報
  └── TOPへ戻るリンク
```

### story-block カラールール

| チャプター | ボーダー色 | 用途 |
|-----------|-----------|------|
| ch1 | `--danger` (赤) | 課題・問題提起 |
| ch2 | `--primary` (テーマ色) | 出会い・発見 |
| ch3 | `--accent` (アクセント) | 実践・変革 |
| ch4 | `--warm/cyan` (暖色/寒色) | 技術深掘り・ブレークスルー |
| ch5 | `--safe` (緑) | 結末・解放・エピローグ |

### h1タイトルのルール

- **製品の紹介を一言で**: 「〇〇：△△を実現する□□」
- ストーリーの主人公名やシチュエーションは**書かない**
- 例: `AutoAgent：「職人」から「設計者」への覚醒`
- 例: `TimesFM：1000億データ点で学んだ「未来予測AI」`

### カラーテーマの選び方

過去のスライドと被らないように、以下から選択:

| テーマ | primary | 用途例 |
|--------|---------|--------|
| Dark Red/Gold | `#DC2626` | セキュリティ事件、リーク |
| Dark Blue/Orange | `#2563EB` | Office系、業務自動化 |
| Dark Green/Gold | `#059669` | 予測AI、効率化、コスト削減 |
| Dark Purple/Cyan | `#7C3AED` | エージェント、自律進化 |
| Dark Indigo/Emerald | `#4F46E5` | ローカルAI、デジタル主権 |
| Dark Teal/Orange | `#0D9488` | 検索・リサーチ系 |
| Blue/Rose | `#6366F1` | Computer Use、UI操作系 |
| Orange/Amber | `#EA580C` | 自己進化、Rust系 |

### 使用するグリッドコンポーネント

| コンポーネント | 用途 |
|--------------|------|
| `stats-grid` | 数値KPI（冒頭の製品紹介） |
| `wall-grid` | 課題・障壁（赤背景、3列） |
| `vs-grid` | Before/After比較（1fr auto 1fr） |
| `feature-grid` / `tool-grid` | 機能・ツール紹介（ダーク背景、3列） |
| `model-grid` / `persona-grid` | モデル/ペルソナ紹介 |
| `emergent-grid` / `reveal-grid` | 発見・創発行動 |
| `summary-grid` | まとめ（ダーク背景、3-4列） |
| `flow-steps` | フロー（flexbox + 矢印） |
| `timeline` | 時系列（grid 3列: time/line/content） |
| `links-grid` | 参考リンク（2列） |
| `quote-box.dark` | 引用（ダーク背景、中央揃え） |
| `highlight-box` | 補足情報（左ボーダー） |

## Git コンフリクト解決パターン

自動デプロイ（sync workflow）との競合が頻発するファイル:
- `public-pages/news/version.json` → `git checkout --theirs`
- `public-pages/news/archive_index.json` → `git checkout --theirs`
- `presentations/auto_daily_report.html` → `git checkout --theirs`

## 出力

- **スライドURL**: `https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_YYYY_MM_DD.html`
- **サイズ目安**: 3〜6MB（PDFページ数による）
- **画像**: base64埋め込み（外部依存ゼロ）
