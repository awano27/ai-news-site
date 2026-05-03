# TOP ページ IA 再構成 — デザインドキュメント

- 日付: 2026-05-03
- 対象: `c:/develop/ai-news-site/index.html`（ルート TOP ページ）
- スコープ: 情報設計（IA）の再構成のみ。配色・タイポ・既存コンポーネント装飾は維持
- 関連: `news/latest.json`, `public-pages/news/archive_index.json`, `daily_reports/index.json`, `presentations/day_slides/*`

## 背景

現状の TOP（2026-04-18 リデザイン版）は 7 セクション構成で、初見にも常連にも全部見せようとしている：

```
hero → featured-reports(今日の3本) → ranking → categories → this-week → archive → resources
```

「忙しいビジネスパーソンが朝5分で今日と今週を把握する」という主要読者像に対して、

- hero と featured-reports で「今日のスライド」が二重に出てくる（情報の重複）
- ranking と categories が独立セクションとして縦に積まれ、スクロールが長い
- archive が長大なリストで TOP の bottom-heavy になっている

を解消する。

## 目的

- **第1優先 CTA**: 今日のスライドを開く（5分で今日のAIを把握）
- **第2優先**: 今日の別フォーマット（HTMLレポート / Daily News）に深く読む動線
- **想定読者**: 忙しいビジネスパーソン。途中離脱しても満足できる progressive depth

## 新セクション構成（A案）

```
1. Hero            — 今日のスライド（大）+ 主要 CTA
2. Today           — 今日の別フォーマット（HTMLレポート / Daily News）
3. This Week       — 今週のスライド（横スクロール）
4. Today's Highlights — ranking + categories を統合
5. Archive         — 検索ボックス + 月別リンク（リストは別ページに）
6. Resources       — 現状維持（最下部）
```

### Section 1 — Hero（最大変更）

- **左半分**:
  - h1「今日のAIを5分で。」
  - 日付 + 1行サマリ（最新 `news/<date>.json` の `summary` から自動取得）
  - 大型ボタン「今日のスライドを開く」（最新 `presentations/day_slides/day_slide_*.html`）
  - 副CTA（小・横並び 2 リンク）「HTMLレポート」「Daily News」
- **右半分**: 今日のスライドのサムネイル画像（大）→ クリックでもスライドへ
- 高さ ~70vh（次セクションが視界に入る）
- `featured-reports` セクションをここに統合し、独立セクションを廃止

### Section 2 — Today（旧 featured-reports を変形）

- 見出し「今日のAI、もっと読む」
- 2カード横並び:
  - HTMLレポート（最新 `daily_reports/<date>.html` のサムネイル + 抜粋）
  - Daily News（同日の `daily-news/` リンク + ヘッドライン抜粋）
- スライドは hero に集約済みなのでここから外す
- モバイル: 縦積み

### Section 3 — This Week

- 見出し「今週のスライド」
- 横スクロールで直近 7 日のスライドサムネイル + 日付
- 「すべての今週分を見る」リンク
- 構造はほぼ現状維持

### Section 4 — Today's Highlights（新設・統合セクション）

- 見出し「今日のハイライト」
- タブ切替 or 並列 2 カラム:
  - **Ranking**: TOP3 記事（スコア順）+ 元ソース直リンク
  - **Categories**: 4 カテゴリ × 各 3 件（AI Model / Business / Research / Product）
- ranking と categories の独立セクション 2 つを 1 セクションに統合
- モバイル: タブ切替で縦積みを回避

### Section 5 — Archive

- 見出し「過去のすべてのAIニュース」
- 検索ボックス 1 行（キーワード）
- 月別リンク（直近 6 ヶ月）
- 「アーカイブ全件を見る」CTA → 別ページ（`presentations/news_archive.html` 等）
- 既存の長大なリストは TOP から削除し、別ページに移動

### Section 6 — Resources

- 現状維持（最下部）

## モバイル方針

- Hero: 縦積み（タイトル → サムネイル → CTA）
- Section 2: 縦積み（2 カード → 1 カラム）
- Section 4: タブ切替（横並びは諦める）
- 横スクロールカルーセルは Section 3 (this-week) のみ

## ビジュアル方針

- 配色（navy `#070F26` + yellow `#FFCC00` + blue `#0d6efd`）は現状維持
- フォント（Noto Sans JP / Noto Serif）も現状維持
- 今回は **IA だけ** の見直し。CSS トークンは触らない

## 削除/統合まとめ

| 旧 | 新 |
|---|---|
| `featured-reports`（今日の3本）独立セクション | hero と Section 2 (Today) に分割吸収 |
| `ranking` 独立セクション | Section 4 に統合 |
| `categories` 独立セクション | Section 4 に統合 |
| `archive` の長大リスト | 検索ボックス + 月別リンク + 別ページ |

## データソース（既存と同じ）

- `news/latest.json` — 今日のスライド・サマリ
- `public-pages/news/archive_index.json` — アーカイブ index
- `daily_reports/index.json` — HTML レポート index
- `presentations/day_slides/day_slide_*.html` — スライド本体

すべてフロント JS の fetch で動的描画する現方式を踏襲。ビルドステップ追加なし。

## 非ゴール

- 配色・タイポ・コンポーネント装飾の刷新（別案件）
- 新セクションの追加（カテゴリ追加など）
- 既存ページ（`presentations/index.html` など）の見直し
- バックエンド・データ生成パイプラインの変更

## 想定リスク

- 既存 fetch ロジックを再配置するため、JS の if-else チェーン（最新スライド判定）を壊さないよう注意
- archive の長大リストを削除すると、SEO で拾われていた過去日付リンクが消える可能性 → 別ページに残すことで影響を最小化
- バックアップ: `index.html.bak.20260503` を作成してから書き換える

## 次ステップ

- writing-plans スキルで実装プランに展開
