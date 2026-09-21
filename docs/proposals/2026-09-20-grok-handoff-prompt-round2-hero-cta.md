# Grok 向け指示プロンプト 第 2 ラウンド 追補 A（ヒーロー主 CTA の差し替え設計）

- 作成日: 2026-09-20
- 位置づけ: 第 2 ラウンド（`2026-09-20-grok-handoff-prompt-round2.md`）のタスク 3 をこの追補で置き換える。
  運営者の決定: ヒーローの主 CTA を「今日のスライド」に差し替え、設計記事の入口は残して格下げする。旧タスク 3 のナビ・タグライン・実績数値は T6 に移す
- 使い方: 第 2 ラウンドを実行中の Grok の会話に `---` 以下を貼る。単体でも動くよう現状の事実を埋め込んである。
  Grok はリポジトリを編集せず Markdown で出力し、適用は Claude Code 側で行う

---

あなたは visionhub.jp のグロース担当（UX・SEO・計測の設計者）です。
第 2 ラウンドのタスク 3 を、この追補の内容に差し替えて実行してください。
リポジトリの編集は行わず、成果物はすべて Markdown で出力します。適用は別環境（Claude Code）で行います。

## 0. 運営者の決定（変更不可）

- ヒーローの主 CTA を「今日のスライド」に差し替える。併置ではなく置換
- 設計記事「AI記事の『確認済み』をどう管理するか」への入口は残すが格下げする。
  ヒーローからは外すか三次リンクに落とし、カード 03・About・フッターから辿れる状態は維持する
- h1 `#heroIdentity` の文言と要素は変えない
- 肖像（マックス・プランク）の扱いは案ごとに明記する。既定は維持（変更範囲を小さく保つため）

## 1. 現状の事実

### ヒーローの構成（`index.html`）
- 左: h1 `#heroIdentity`「AIの動きを追い、実装と根拠を確かめる。」／p `#heroDescription`「AIニュース、ツール比較、公開コード付きの設計記事。情報収集から技術判断までを支援します。」／
  div `.hero-cta` 内に `#heroArticleBtn`（`btn btn-primary`、href `articles/claim-evidence-design.html`、`data-cta="hero-article"`）と
  `#heroNewsBtn`（`btn btn-ghost`、href `daily-news/`、`data-cta="hero-news"`）
- 右: 肖像画像（`assets/hero-planck.webp`、モバイルは `assets/hero-planck-mobile.webp`）とクレジット
- ヘッダー右上: `#latestSlideHeroBtn`（`class="cta"`、最新スライドへ。`scripts/update_home_fallback.py` が毎日 href とラベルを更新）
- ヒーロー直下: 「5秒 今日の要点」バー（`#sitrepLink` `#sitrepUpdate` `#sitrepDesk` `#sitrepAction`、`data-cta="sitrep"`）
- 2 画面目「目的から読む」: カード 01（`#heroTwist` h3、`#heroWhy` p、`#heroSlideBtn` `data-cta="hero-slide"`）、
  カード 02 `#comparisonCard`（比較ガイド）、カード 03 `#implementationCard`（設計記事）
- 日次更新: `scripts/update_home_fallback.py` が最新スライドから twist・日付を抽出し
  `#heroDate` `#heroTwist` `#heroWhy` `#heroSlideBtn` `#latestSlideHeroBtn` `#sitrep*` を書き換える。
  スライドが無い日は `#heroDate` を「公開スライドなし」、`#heroTwist` を「公開スライドはまだありません」、ボタンを「スライド一覧」に差し替える（空状態の契約）
- 計測: `data-cta` を持つ要素のクリックが GA4 の `cta_click` に送られる設計。GA4 は ID 未投入で未稼働

### 設計記事の位置づけ
- 2026-09-05 の content-integrity 作業で作った「根拠レコードと変更検知」の仕組みを公開コード付きで解説した Engineering Note。
  対象読者は「技術ブログ・AI コンテンツ・社内ナレッジを扱うエンジニア」。サイト各所の「情報区分」「照合日」表示の根拠説明を担う
- 入口は 3 か所: ヒーローの主ボタン、カード 03、About の 1 リンク

### 変更を固定しているテスト（変更案が必要）

| テスト | 現行の主張 |
|---|---|
| `tests/test_build_homepage_latest.py::assert_entry_contract` | h1 は `#heroIdentity` のみ／`#heroDescription` は p／`#heroNewsBtn`→`daily-news/`、`#heroArticleBtn`→記事、`#comparisonCard`→比較ガイド、`#implementationCard`→記事／`#heroArticleBtn` が `btn-primary`、`#heroNewsBtn` が `btn-ghost`／DOM 順で `#heroArticleBtn` が `#heroNewsBtn` より前／`#heroTwist` は h3、`#heroWhy` は p／各 id は一意 |
| 同 `test_entry_contract_rejects_broken_heading_or_primary_link` | `#heroIdentity` の欠落、`daily-news/` と記事 href の差し替えを拒否 |
| 同 復帰テスト | fallback 復帰後も記事 href、`daily-news/` href、「最新スライドを読む」が残る |
| `tests/test_evidence_article.py` | index.html に `#heroArticleBtn` と `#implementationCard` の両方が記事 href で存在／about.html の記事リンクはちょうど 1 つ／日次再生成後も残る |
| `tests/test_update_home_fallback.py` | fallback 更新後も `#heroArticleBtn` と `#implementationCard` の記事 href が残る |

- CLAUDE.md の規約: 「トップの h1（#heroIdentity）はサイトの価値説明として固定。…主要なニュース・設計記事の入口は保持し、サイト名はヘッダーに残す」

### デザイン制約
- CSS トークン `--navy #070F26` `--yellow #FFCC00` `--blue #0d6efd`、Noto Sans JP。配色とフォントは変えない。
  既存クラス `.btn` `.btn-primary` `.btn-ghost` `.hero-cta` を使う
- モバイル 390x844: h1 上端 240px 以下、ヒーロー高さ 680px 以下、主 CTA 下端 760px 以下。PC 1440x900: ヒーロー高さは現状 ±20px
- カバー画像は `presentations/day_slides/images/MMDD/cover.jpg`（1536x1024、150〜350KB）。ヒーローに出す場合はモバイルの転送量に配慮する

## 2. 依頼タスク

### T1 ヒーローの新構成 3 案と推奨
各案について: 主 CTA（今日のスライド）／副 CTA（最新ニュース）／記事リンクの扱い（三次テキストリンク or ヒーローから除去）／
今日の twist と日付をヒーロー内に出すか／肖像の扱い／モバイルの折り返し順／受け入れ基準への適合見込み／変更ファイル数の見込み。
推奨 1 案を理由付きで選ぶ。

### T2 コピー
- 主 CTA・副 CTA・記事リンク（残す場合）の文言を各 3 案、推奨 1 つ。
  主 CTA は「今日の」を含める。日付や twist を動的に埋める場合はプレースホルダを `{twist}` `{date}` で示す
- `#heroDescription` の改稿案 3 つ（日次スライドが中核であることが伝わる 1〜2 文。h1 は変えない）

### T3 推奨案の HTML / CSS スニペット
- `.hero-cta` の新マークアップ。主 CTA の id は既存の `#heroSlideBtn` `#latestSlideHeroBtn` と衝突しない新 id（例 `#heroTodayBtn`）を提案し、`data-cta` 値も指定する
- 追加 CSS は 40 行以内、既存トークンのみ
- `update_home_fallback.py` に追加すべき処理を仕様として書く: 新 id の href／ラベル／twist／日付をどのソースから埋めるか、空状態（公開スライドなし）のときの表示

### T4 テスト契約と規約の変更案
表（テスト名 / 現行アサーション / 変更後アサーション / 理由）で、1 章の 5 つのテストそれぞれについて書く。
方針: `#heroArticleBtn` の「primary かつ先頭」要件を外し、新 id の「primary かつ先頭、href は最新スライド」に置き換える。
記事の到達要件はカード 03 と About に限定する。空状態テストの期待値も更新する。CLAUDE.md の該当行の新しい文言も書く。

### T5 計測と判断ルール
GA4 稼働後 2 週間の `cta_click` を `data-cta` 別に集計する前提で、何を比較し、どの条件で記事リンクを完全に外すか、戻すかを表にする。
数値目標は基準線が出るまで置かず、比率の比較ルールだけ書く。

### T6 ナビ・タグライン・実績数値（旧タスク 3 の 3〜5 項をここで出す）
- ナビの最終案（6 項目以内。同一ページ内アンカーではなく実 URL）と、フッターの購読導線（RSS `feed.xml`、X、ニュースレター仮置き）
- タグライン統一案 3 つと推奨 1 つ。対象はトップの `<title>` と OG、About の title、README。h1 は固定なので対象外
- 実績数値（スライド本数・ニュース件数・連続更新日数）の算出元と表記ルール。
  算出元候補: `public-pages/news/archive_index.json`、`presentations/day_slides_index.html`、`presentations/daily_reports/index.json`

## 3. 出力形式

- 日本語。見出しは T1〜T6。先頭に 10 行以内の要約
- 表は Markdown 表、スニペットはコードブロック
- 現状と異なる前提を置く場合は「仮定」と明記する。h1 の変更案は出さない
- 第 2 ラウンドのほかのタスク（1・2・4・5）はそのまま。タスク 3 だけをこの追補で置き換える
