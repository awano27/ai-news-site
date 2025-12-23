---
name: producthunt-tools-updater
description: Product Huntから最新のトレンドツール・Golden Kitty受賞ツールを調査し、推奨ツールリスト（recommended_tools.html）に追加する。ツールリストの更新、Product Hunt調査、新規ツール追加、Golden Kitty Awards情報の取得時に使用。
---

# Product Hunt Tools Updater

Product Huntから最新のトレンドツールを調査し、既存のツールリストに追加するワークフロー。

## ワークフロー

### Step 1: 既存ツールリストの確認

1. `presentations/recommended_tools.html` を読み込む
2. 既存のツール名をすべて抽出
3. カテゴリ構造とHTMLフォーマットを把握

### Step 2: Product Hunt調査

以下のソースから最新ツールを検索:

```
WebSearch queries:
- "Product Hunt Golden Kitty {year} winners AI tools"
- "Product Hunt best AI tools {month} {year} trending"
- "site:producthunt.com AI tools launched {month} {year}"
```

WebFetch targets:
- https://www.producthunt.com/golden-kitty-awards
- https://dev.to (Golden Kitty記事)
- https://www.aibase.com (Product Huntランキング記事)

### Step 3: ツール選別

既存リストと比較し、以下の条件で新規ツールを選別:

- 既存リストに未掲載
- Golden Kitty受賞/ノミネート または 月間上位ランク
- ビジネス/開発者向けの実用的なツール

### Step 4: HTMLカード作成

各ツールについて以下のフォーマットでカードを作成:

```html
<div class="tool-card" data-tags="{カテゴリタグ}" data-audience="{対象者}">
  <div class="tool-header">
    <h3>{ツール名}<span class="badge new">{バッジ}</span></h3>
    <p class="tool-subtitle">{サブタイトル}</p>
  </div>
  <p class="tool-description">
    {説明文 - 受賞情報を含む}
  </p>
  <div class="tool-section">
    <h4>特徴</h4>
    <ul>
      <li>{特徴1}</li>
      <li>{特徴2}</li>
      <li>{特徴3}</li>
      <li>{特徴4}</li>
    </ul>
  </div>
  <div class="tool-section">
    <h4>リンク</h4>
    <ul>
      <li><a href="{公式サイトURL}" target="_blank" rel="noopener" style="color: var(--accent-2);">公式サイト</a></li>
      <li><a href="https://www.producthunt.com/products/{slug}" target="_blank" rel="noopener" style="color: var(--accent-2);">Product Hunt</a></li>
    </ul>
  </div>
</div>
```

### Step 5: ファイル更新

1. 新しいカテゴリセクションを追加（例: `Product Hunt Golden Kitty {year}`）
2. エンターテインメントセクションの後、フッター前に挿入
3. セクションヘッダーを含める:

```html
<section class="category-section">
  <div class="category-header">
    <h2>{絵文字} {カテゴリ名}【{タイプ}】</h2>
    <p>{説明}</p>
  </div>
  <div class="tools-grid">
    <!-- ツールカード -->
  </div>
</section>
```

## 属性値リファレンス

### data-tags (カテゴリ)
- `ai` - AI関連
- `audio` - 音声
- `video` - 動画
- `dev` - 開発ツール
- `automation` - 自動化
- `agent` - AIエージェント
- `design` - デザイン
- `nocode` - ノーコード
- `productivity` - 生産性
- `meeting` - 会議
- `database` - データベース
- `data` - データ分析
- `sales` - セールス

### data-audience (対象者)
- `biz` - ビジネスユーザー
- `dev` - 開発者
- `biz,dev` - 両方

### バッジ種類
- `GK{year}受賞` - Golden Kitty受賞
- `GK{year}ノミネート` - Golden Kittyノミネート
- `GK{year}準優勝` - Golden Kitty準優勝
- `PH#1` - Product Hunt #1
- `新興` - トレンド新興ツール

## ツールカテゴリ例

- AI音声・オーディオ: ElevenLabs, Wispr Flow, Voicenotes
- AIエージェント: Lindy, Vapi, CrewAI
- 開発ツール: postgres.new, Helicone AI
- デザイン: Figma AI, Mobbin
- ノーコード: Wegic, HeyForm
