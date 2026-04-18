# index.html リデザイン設計書

**日付**: 2026-04-18
**対象**: ルート `index.html`（ランディングページ）のみ
**目的**: Claude Design 風のライト基調デザインで、最新スライドへの導線を強化し、可読性を改善する

---

## 1. スコープ

- 対象ファイル: `c:/develop/ai-news-site/index.html` 1ファイル
- 全面書き換え（バックアップ: `index.html.bak.20260418`）
- 既存サブページ（`presentations/index.html` 等）は今回対象外

## 2. デザインシステム

### カラー（Claude Design 準拠）

```css
--bg:        #faf9f5;  /* off-white, 紙のような温かみ */
--bg-card:   #ffffff;
--bg-soft:   #f3efe7;  /* 薄ベージュ・セクション交互背景 */
--border:    #e8e2d5;
--ink:       #1a1a17;  /* 本文 */
--ink-soft:  #5a5651;
--ink-mute:  #8a857d;
--accent:    #cc785c;  /* Claude オレンジ・主役 */
--accent-d:  #b8654a;  /* hover */
--accent-bg: #fdf2ec;  /* バッジ背景 */
```

### タイポグラフィ

- 見出し: `Noto Serif JP` 700/900
- 本文: `Noto Sans JP` 400/500
- 数字・日付: `JetBrains Mono` 500

### 余白・形状

- max-width: 1120px
- 左右パディング: 24px (mobile) / 48px (desktop)
- セクション縦余白: 56px (mobile) / 96px (desktop)
- 角丸: 12px
- 影は使わず細い `--border` で区切る
- ホバーは `border-color` と `background` 変化のみ。translate/scale なし

## 3. レイアウト構造

### Header（sticky, 64px）

```
[AI Intelligence Hub]  最新スライド  アーカイブ  リソース  About  [今日のスライド →]
```

- 背景: `--bg` 半透明 + `backdrop-filter: blur(12px)`
- 下に 1px の `--border`
- 右端 CTA はオレンジ pill ボタン

### Hero（最新スライド推し / max-height 720px）

2カラム（モバイルは縦積み）:

**左カラム**
- TODAY バッジ（オレンジ小バッジ） + 日付（JetBrains Mono）
- 大見出し: スライドタイトル（48-64px Noto Serif JP）
- 3行サマリー（`news/{today}.json` の `highlight.summary` から動的取得）
- CTA 2つ: 「今日のスライドを見る →」（オレンジ実塗り）/「アーカイブを探す」（アウトライン）
- 補助情報: 「今日のニュースハイライト: {highlight.title}」（小文字）

**右カラム**
- 合成カード（16:9, max 560px）:
  - 背景: `--accent-bg` から `--bg-soft` へのグラデーション
  - 中央に大きな日付（Noto Serif JP 96px）
  - 下部にスライドタイトル（2行省略）
  - 細い `--border`
- スクリーンショット生成は不要

### Section 2: This Week

- 見出し「今週のスライド」+ 右に「すべて見る →」
- グリッド: デスクトップ 4列 / タブレット 2列 / モバイル 1列または横スクロール
- カード（最新7枚 = 1週間分、`archive_index.json` から取得）:
  - 上部: 日付（JetBrains Mono 大）+ 曜日
  - 中央: 件数バッジ「{count} items」
  - 下部: 「スライドを見る →」
  - URL: 日付から自動組立 `presentations/day_slides/day_slide_YYYY_MM_DD.html`
- 背景: `--bg`

### Section 3: カテゴリ別ハイライト

- 見出し「今日のカテゴリ別ハイライト」
- 4カラム（モバイルは2列）:
  - business / tools / posts / research（実データに合わせて調整）
  - `news/{today}.json` の `sections[category][0]` から最新1件
  - 各カラム: カテゴリラベル + タイトル（2行省略）+ source.name + 「→」
- 背景: `--bg-soft`（交互セクション）

### Section 4: アーカイブ入口

- 中央寄せ、コンパクト
- 統計1行: 「{N} スライド · {M} ニュース項目 · 毎朝07:00更新」（`archive_index.json` の長さから算出）
- 大ボタン「ニュースアーカイブを検索 →」
- 補助リンク3つ: 日次スライド一覧 / 月次レポート / RSS
- 背景: `--bg`

### Section 5: リソース・レポート

- 見出し「リソース」
- 3〜4枚カード:
  - 外部リソース（`presentations/ai_external_resources.html`）
  - Claude Code Setup Guide（`presentations/claude_code_setup_guide.html`）
  - おすすめツール（`presentations/recommended_tools.html`）
  - レポート類（`presentations/auto_daily_report.html`）
- 各カード: アイコンスペース（小）+ タイトル + 1行サマリー + 矢印
- 背景: `--bg-soft`

### Footer

- 細いシンプル
- awano27 / GitHub link / 最終更新時刻 / © 2026
- 背景: `--bg`

## 4. データ取得仕様

### 取得方式: 方式A（fetch + フォールバック + skeleton）

**fetch 対象**

| データ | ファイル | 用途 |
|---|---|---|
| 今日の highlight | `news/YYYY-MM-DD.json` | ヒーロー summary, カテゴリハイライト |
| アーカイブ一覧 | `public-pages/news/archive_index.json` | This week 7枚, 統計総数 |

**今日の日付決定ロジック**
1. `archive_index.json` の先頭エントリの `date` を「最新日」として採用
2. `news/{date}.json` を fetch して `highlight` と `sections` を取得
3. fetch 失敗時はハードコードされたフォールバック値を表示

**スライドURL組み立て**
```js
const url = `presentations/day_slides/day_slide_${date.replaceAll('-', '_')}.html`;
```

**フォールバック戦略**
- HTML に「最後のスナップショット値」をハードコード（fetch失敗時もページが破綻しない）
- skeleton placeholder（薄グレー矩形 + パルスアニメ）で fetch 中の体感を改善
- fetch 成功 → DOM置換、失敗 → ハードコード値のまま

**サムネ**: 合成カード（タイトル+日付+グラデーション）。スクリーンショット生成不要

## 5. 実装順序

1. `index.html` を `index.html.bak.20260418` にバックアップ
2. 新 `index.html` を frontend-design スキルで生成（fetch + skeleton + フォールバック含む）
3. ローカルで `python -m http.server 8000` 起動して動作確認
   - fetch 成功時: ヒーロー summary・カテゴリ・統計が動的に入る
   - fetch 失敗時（`offline` トグル）: フォールバック値が表示される
   - 全リンクが正しいスライド/サブページを指す
4. レスポンシブ確認（375px / 768px / 1280px）
5. コミット & プッシュ
6. `MEMORY.md` 更新（フォールバック値の更新タイミングを追記）

## 6. 実装しないもの（YAGNI）

- ダーク/ライト切替
- 検索機能（既存アーカイブ画面に任せる）
- スライドサムネ画像の事前生成
- ニュースAPI連携・SSR
- アニメーション付きグラフ・カウンター
- A/Bテスト用バリアント

## 7. 成功基準

- ファーストビューで「最新スライドのタイトル・日付・要約・CTA」が即視認できる
- すべてのセクションが Claude Design 風（ライト基調・オレンジアクセント・ミニマル）で統一
- モバイル幅でも横スクロールなく快適に閲覧可能
- fetch 失敗時もハードコード値で表示が破綻しない
- 既存スライドへのリンクがすべて正しく機能する
