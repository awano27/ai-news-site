# HTMLテンプレート集

## セクションテンプレート

```html
<!-- Product Hunt Golden Kitty Awards {year} 受賞ツール -->
<section class="category-section">
  <div class="category-header">
    <h2>🏆 Product Hunt Golden Kitty {year}【受賞ツール】</h2>
    <p>{year}年のProduct Hunt年間アワード受賞・ノミネートツール</p>
  </div>
  <div class="tools-grid">
    <!-- ツールカードをここに追加 -->
  </div>
</section>
```

## ツールカードテンプレート

### 基本カード

```html
<div class="tool-card" data-tags="ai,{追加タグ}" data-audience="biz,dev">
  <div class="tool-header">
    <h3>{ツール名}<span class="badge new">{バッジテキスト}</span></h3>
    <p class="tool-subtitle">{サブタイトル - 1行で概要}</p>
  </div>
  <p class="tool-description">
    {説明文 - 2-3文。受賞情報、主な機能、特徴を含める}
  </p>
  <div class="tool-section">
    <h4>特徴</h4>
    <ul>
      <li>{特徴1 - 主要機能}</li>
      <li>{特徴2 - 差別化ポイント}</li>
      <li>{特徴3 - 技術的特徴}</li>
      <li>{特徴4 - ビジネス的価値}</li>
    </ul>
  </div>
  <div class="tool-section">
    <h4>リンク</h4>
    <ul>
      <li><a href="{公式サイトURL}" target="_blank" rel="noopener" style="color: var(--accent-2);">公式サイト</a></li>
      <li><a href="https://www.producthunt.com/products/{product-slug}" target="_blank" rel="noopener" style="color: var(--accent-2);">Product Hunt</a></li>
    </ul>
  </div>
</div>
```

## バッジ一覧

| バッジテキスト | 用途 |
|--------------|------|
| `GK2024受賞` | Golden Kitty Awards 部門受賞 |
| `GK2024ノミネート` | Golden Kitty Awards ノミネート |
| `GK2024準優勝` | Golden Kitty Awards 準優勝 |
| `PH#1` | Product Hunt デイリー/ウィークリー1位 |
| `新興` | 注目のトレンドツール |
| `定番` | 業界標準ツール |

## タグ一覧

### data-tags（複数可、カンマ区切り）

| タグ | 説明 |
|-----|------|
| `ai` | AI・機械学習関連 |
| `audio` | 音声処理 |
| `video` | 動画処理 |
| `dev` | 開発ツール |
| `automation` | 自動化 |
| `agent` | AIエージェント |
| `design` | デザイン |
| `nocode` | ノーコード |
| `productivity` | 生産性 |
| `meeting` | 会議 |
| `database` | データベース |
| `data` | データ分析 |
| `analytics` | アナリティクス |
| `sales` | セールス |
| `voice` | 音声AI |
| `llm` | 大規模言語モデル |
| `observability` | 監視・観測 |
| `form` | フォーム |
| `reference` | リファレンス |
| `calendar` | カレンダー |
| `mobile` | モバイル |
| `ios` | iOS |
| `web` | Web |

### data-audience

| 値 | 説明 |
|----|------|
| `biz` | ビジネスユーザー向け |
| `dev` | 開発者向け |
| `biz,dev` | 両方向け |

## 挿入位置

新しいセクションは以下の位置に挿入:

```
...
    </section>  <!-- エンターテインメント・ゲームセクション終了 -->

    <!-- ここに新しいセクションを挿入 -->

    <div style="margin-top: 48px; ...">  <!-- フッター開始 -->
```
