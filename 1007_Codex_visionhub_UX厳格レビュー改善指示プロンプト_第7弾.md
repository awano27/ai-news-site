# Codex 指示プロンプト — 生成器・テンプレート側の読みにくさ・遅さ・操作不能を直す（UX 厳格レビュー 第7弾）

対象リポジトリ: `C:\develop\ai-news-site`（本番 https://visionhub.jp/）
根拠: `1007_visionhub_UX厳格レビュー結果レポート.md`（6観点で指摘 → 別エージェントが再計測して反証。本弾は P1 のうち「毎日自動生成されるページの生成器・テンプレート」側）。
前提: 第6弾（`1007_Codex_visionhub_UX厳格レビュー改善指示プロンプト_第6弾.md`）が先に作業ツリーへ入っていてもいなくても独立に実行できるようにしてある。ただし W4 の共有ドロワーが第6弾で入っている場合は、それを壊さない。

**完了の形**: 下記 V1〜V6 の「受け入れ条件」の検証がすべて通り、完了報告（末尾の書式）を書くまで。初回実装で止まらない。落ちた検証は自分で原因を直して再実行する。

---

## 最初に守ること

1. この指示書を最後まで読んでから作業する。
2. **ローカルの `C:\develop\ai-news-site` は origin/main より 170 コミット以上遅れ、未コミット差分も多い。ここでは作業しない・触らない。** origin/main の分離 worktree を作って作業する（第6弾で作成済みなら `C:\develop\ai-news-site-ux6` を再利用してよい。**その場合は第6弾の変更を保持したまま追加で作業する**。無ければ新規に作る）:
   ```
   git -C C:\develop\ai-news-site fetch origin
   git -C C:\develop\ai-news-site worktree add --detach C:\develop\ai-news-site-ux7 origin/main
   ```
3. python は `where python` の先頭が hermes venv になることがある（playwright 不在）。`C:\Users\awano\AppData\Local\Microsoft\WindowsApps\python.exe` を明示する。Node の Playwright は `set NODE_PATH=C:\develop\ai-news-site\node_modules` で参照する。
4. 検証スクリプト・ログ・スクショは worktree 内 `tmp\ux7-verify\` に保存する（コミット対象外。完了報告にパスを書く）。動作確認はターミナル実行の Playwright スクリプトで行う。
5. `.gitignore` が `scripts/` `script/` `.github/` の新規ファイルを無視する。新規ファイルは `git status --ignored --short` で見える化し、「`git add -f` が必要なファイル」として完了報告に列挙する（自分では add しない）。
6. 全ファイル UTF-8（BOM なし）。`.bat` / `.cmd` は ASCII のみ。

## 安全境界（理由つき。変更は作業ツリーに残してレビューに回す）

- `git commit` / `push` / PR 作成 / deploy / `gh workflow run` はしない（レビュー前の成果物を外に出さないため）。`gh run list` `curl -sS` など読み取りは可。
- ssh / scp / リモートアクセス、DB スキーマ変更、外部サービスへの書き込み、GitHub の secrets / variables の変更はしない。
- 実 LLM・実 API の呼び出しはしない。
- **`script/build_day_slides_index.py` は実行しない**（手作りの `presentations/day_slides/meta_index.json` の分類と番号を破壊する）。一覧の再生成は `script/build_day_slides_list.py` のみ。
- ローカル完結の検証（pytest、Node テスト、Playwright、冪等な生成器の再実行、`scripts/check_site_freshness.py`）は承認なしで何度でも実行してよい。

## 停止条件（これ以外では止まらない）

編集対象が origin/main と衝突している、または安全境界に触れないと進めない時だけ停止して報告する。無関係な behind / dirty は完了報告に書いて続行。

---

## 対象

| ID | 内容 | 主な修正先（生成器・テンプレ側。**生成物の HTML は直接編集しない**） |
|---|---|---|
| **V1** | 日次スライド一覧（`day_slides_list`）のヒーロー・CTA・チップ・検索 | `script/build_day_slides_list.py` |
| **V2** | AIランキングのフッター不可視・本文の文字化け・同期 JS による白画面 | `src/generators/ranking_template.py`、`src/generators/ranking_data_parser.py`、`scripts/generate_ranking_input.py` |
| **V3** | 日次レポートのアコーディオン、daily-news の CLS と GitHub/HF 混在 | `src/auto_collect/report_template.html`、`html_report_renderer.py`、`daily_news_template.html`、`daily_news_page.py` |
| **V4** | トップの CLS、ランキング選定、AI 非関連記事 | `index.html`（手書き部分）、`scripts/build-homepage-latest.js` |
| **V5** | デイリーレポート・アーカイブの検索 | `presentations/daily_reports_archive.html`（手書き） |
| **V6** | Web フォントの描画ブロック | `assets/ntt-theme.css` と各ページの `<head>`、生成器テンプレ |

非対象: P2 全般（レポートの「第8弾候補」表）、トップ h1（`#heroIdentity`。固定）、第6弾の領分（sitrep・フォールバック公開・検索索引・ナビ・スライド前後ナビ）。

## 毎日の自動生成で上書きされる場所

| 見た目の場所 | 直接編集 | 直す所 |
|---|---|---|
| `presentations/day_slides_list.html` | 禁止（公開のたびに全面再生成） | `script/build_day_slides_list.py` |
| `presentations/ai_ranking_report_latest.html` と日付版 | 禁止（`build-ranking-preview.yml` が 08:30 JST） | `src/generators/ranking_template.py` ほか |
| `daily-news/index.html`、`daily-news/archive/*.html` | 禁止（06:00 cloud / 08:00 local が再生成） | `src/auto_collect/daily_news_template.html`、`daily_news_page.py` |
| `presentations/auto_daily_report.html` ほか日次レポート | 禁止 | `src/auto_collect/report_template.html`、`html_report_renderer.py` |
| `index.html` の `<!-- fallback:... -->` 内、`news/latest.json` | 上書きされる | `scripts/update_home_fallback.py` / `scripts/build-homepage-latest.js` |
| `index.html` の `<style>`・スクリプト、`daily_reports_archive.html` | 可（手書き） | — |

生成器を直したら、**ローカルで生成器を実行して HTML を作り直し**（実 LLM は呼ばない。fixture / 既存データを入力にする）、その出力に対して検証する。

---

## V1. 日次スライド一覧（P1）

**現象**: モバイルで、最新号に cover 画像がある日は画像内の文字と見出しが重なって読めず、LCP が 10.5 秒（hero 画像が `loading="lazy"`、サムネは原寸 JPEG 最大 423KB、`width/height` なし）。主 CTA「この号を読む →」のコントラストが 1.3:1（`.nb a{color:inherit}` の詳細度が CTA の色に勝つ）。カテゴリチップ 231 個のうち agent 系 146 個が 3.7:1・10px。検索 0 件で何も表示されず、検索語が URL に残らず、16 か月のうち 13 が閉じたままで月ジャンプも無い。
**修正先**: `script/build_day_slides_list.py` — `cover_media()`（:124-128、常に lazy）、CTA（:252 `.nb a`）、`CATS['agent']` の色（:37）、モバイルのヒーロー（:360-362）、`OPEN_MONTHS`（:45）、`applyFilter`（:476-510）。

**要求**:
1. hero に使う画像は lazy にしない（`fetchpriority="high"`、`width`/`height` 指定）。hero 用に縮小版（表示幅の2倍程度、150KB 以下）を使う。縮小版の生成は、公開手順で再現できる形（既存の `scripts/generate_card_thumbs.py` はトップのカード専用で流用不可。新しい小さなスクリプトを `scripts/` に足し、`images/MMDD/` に成果物を置く）にする。全 `<img>` に `width`/`height` を付ける。
2. モバイルでは hero 画像と文字を重ねない（画像は文字の上か下の帯にする）。重ねるなら全テキストが 4.5:1 以上になる不透明度のベールを敷く。h1 は最新号の題より視覚的に弱くしない。
3. CTA の文字色が背景に対して 4.5:1 以上（`.nb a:not(.cta)` にするか、`.nb .cta` に詳細度を上げる）。全チップが文字と背景で 4.5:1 以上かつ 12px 以上（agent 系の色を調整）。
4. 検索: 0 件の時は理由と解除方法を出す空状態（`role="status"`）。検索語とカテゴリを `?q=` `&cat=` に反映して reload で復元する。月への内部リンク（`a[href^="#"]` が月数以上）を設ける。

**受け入れ条件**（再生成した `day_slides_list.html` に対して）:
- `.hero-cover` に `loading="lazy"` が無く `fetchpriority="high"`、`width`/`height` あり。hero 画像の転送サイズ ≤ 150KB（現状 423KB）。全 `<img>` が `width`/`height` を持つ（現状 0/150）。
- Playwright 375x812・1440x900: `.cta` の `color` と `background-color` から計算した比 ≥ 4.5（現状 1.30）。全 `.chip` / `.chip-sm` が 4.5:1 以上かつ `fontSize ≥ 12px`（現状 agent 146 件が 3.73、10px）。
- Playwright 375x812 + 1.6Mbps/150ms/CPU 4x で、最新号に cover がある状態（10/03 号の cover を hero にした HTML を route で配信）の LCP ≤ 4000ms（3回の中央値）。
- `#nbSearch` に `zzzqqq` を入力すると `role="status"` の要素に「見つかりません」等のテキストが出る。`Claude` 入力後に `location.search` が `q=Claude` を含み、reload 後に `#nbHit` が 71 に復元される。

---

## V2. AIランキング（P1）

**現象**: フッターが背景色なしで白・黄文字が見えない（コントラスト 1.07〜1.5）。900px 以下でセクションナビが非表示になり代替が無い（モバイルで 31.7 画面）。Biz スコアピルが 3.13:1。本文に全角ピリオド `．`（27 箇所）と `。.`（20 箇所）、表の区切り行 `---` がデータ行として出る、同一文言の「活用ポイント」の羅列。`mermaid`（1.46MB）と `chart.js` が `<head>` で同期読み込みされ、モバイルで約 12 秒白画面（FCP/LCP 中央値 11.8 秒）。
**原因（検証済み）**: `src/generators/ranking_template.py:713-727` の footer は inline 色が暗背景前提で `.site-footer` の CSS が無い。`:334-335` の `@media(max-width:900px){.nav{display:none}}` に代替が無い。`:31-32` が同期 `<script src>`。空行は `src/generators/ranking_data_parser.py:55-60` が Markdown の区切り行 `|---|---|---:|---:|---|` を行データとして取り込むこと、`．` は `scripts/generate_ranking_input.py:298` の `_safe_text` が `.` を `．` に置換していること（パーサの正規表現 `ranking_data_parser.py:23-24` が説明文中の `.` を許さないため）。

**要求**:
1. footer に暗背景（または明背景用の文字色）をテンプレで定義し、全リンク・文字が 4.5:1 以上。Biz スコアピルと `.badge.high` も 4.5:1 以上。
2. 900px 以下でも、セクションへ移動できる手段（折りたたみ目次か横スクロールのセクションタブ）と「トップへ戻る」を出す。
3. パーサ: ヘッダー直後の区切り行（`^\|[-: |]+\|$`）をスキップし、説明文の正規表現を `(.+?)\sEng Tool:` 相当に変えて `_safe_text` の `.` → `．` 置換をやめる。文末記号の重複を出さない。項目固有の内容が作れない「活用ポイント」行は出さない。件数 0 のセクター行は表に出さない。
4. `mermaid` は描画ブロックにしない（対象の図が表示される直前に動的 import、`@major` バージョン固定）。`chart.js` も初回描画をブロックしない（`defer`）。**図が mermaid 無しでも意味が通る**ことを確認する（失敗時のフォールバック表示を確認）。

**受け入れ条件**（ランキングを fixture / 既存の入力で再生成して検証。実 LLM は呼ばない）:
- Playwright 375x812・1440x900: `footer.site-footer` 内の全 a/strong/span のコントラスト ≥ 4.5（現状 < 1.5）、`.score-pill.score-biz` ≥ 4.5（現状 3.13）。375px で `href` が `#` で始まる可視リンクが ≥ 2。
- 生成 HTML で `grep -c '．'` = 0（現状 27）、`grep -c '。\.'` = 0（現状 20）、`<td>---</td>` を含む行 = 0、同一の「活用領域: …」定型文の重複が 3 件以下。
- モバイル条件（375x812/DPR2/1.6Mbps+150ms/CPU 4x）で、`performance.getEntriesByType('resource')` のうち `renderBlockingStatus==='blocking'` かつ `cdn.jsdelivr.net` が 0 件（現状 2 件）。FCP・LCP の 3 回中央値 ≤ 4000ms（現状 11.8 秒。Google Fonts の影響が大きければ V6 と合わせて評価し、残差は報告）。
- `tests/test_generate_ranking_input.py` と `tests/test_html_report_parser.py` が通る。

---

## V3. 日次レポート・daily-news のテンプレート（P1）

**現象**:
- `auto_daily_report` のアコーディオンがキーボードで開けない（行頭が `div.row-head` でクリックのみ。`report_template.html:906-908`）。閉じた詳細内のリンクが不可視のままフォーカスされる。
- daily-news の CLS がモバイル 0.29〜0.36・PC 0.12〜0.21（Web フォント入れ替えとグラフ領域の高さ未確保。`daily_news_template.html:19` の `display=swap`、`:137,:314-315`）。
- daily-news の 149 件中 35 件が GitHub / HuggingFace の自動エントリ（英語・定型文）で、ニュース本流に混ざり「見逃せない 48」を水増ししている（`daily_news_page.py` の timeline 結合 :268-272、`high_count` 集計 :296、`_render_news_card` :142-178）。

**要求**:
1. 各行の開閉を `button`（または `role="button" tabindex="0"`）にし、Enter/Space で開閉、`aria-expanded` を公開する。閉じている間の詳細内リンクは `inert` か `hidden` で Tab 順とスクリーンリーダーから外す（`html_report_renderer.py:159` 付近の `<div class="row-head">`）。
2. daily-news: グラフ領域（`DIV.metrics`・`SECTION.charts`）は描画前から最終高さを確保する。Web フォントは `font-display:optional`、またはフォールバックに `size-adjust`/`ascent-override` を与えて折り返しを一致させる。
3. daily-news: GitHub / HF の自動エントリはニュース本流から分離し、専用セクション（既定で折りたたみ）に置く。「見逃せない」とカテゴリ件数は記事のみで集計する。英語原題には、原題だと分かるラベルを付ける。説明が作れないエントリは出さない。**`daily-news/*.html` は直接編集しない**。テンプレと `daily_news_page.py` を直して、既存の入力データ（`daily-news/data.json` 等）から再レンダリングして検証する。

**受け入れ条件**:
- Playwright で再生成した `auto_daily_report.html`: 行の開閉ボタン数 = `.row` 数（15）。Tab で各ボタンに到達し Enter で `.row.open` と `aria-expanded="true"`。Tab を 80 回押して、`opacity<0.05` または `visibility:hidden` の祖先を持つ要素にフォーカスが当たらない。
- 再生成した `daily-news/index.html`: モバイル条件・PC 1440x900 各 3 回で layout-shift 合計の中央値 ≤ 0.05（現状 0.29 / 0.12）。layout-shift の sources に `DIV.metrics`・`SECTION.charts`・`DIV#timeline` が含まれない。
- 再生成 HTML で、`GitHub Trending` / `HuggingFace Trending` のカードが `.timeline` 直下に 0 件で専用コンテナ内にのみ存在する。「見逃せない」の数 = 記事カードの score ≥ 80 の件数。`HuggingFace Trending Model` で始まる定型本文のカードが本流に 0。

---

## V4. トップの CLS・ランキング選定・AI 非関連記事（P1）

**現象**:
- PC で CLS 0.104（1280x800 で 0.170）。ヒーローの container 幅が本文途中の遅い `<style>`（`index.html:1863-1865`）にあり、初回描画で 435px → 1280px に跳ねる。
- 「今日のスコア上位 3 本」は自サイトのスライドを固定 5.0 点で 1 位に置き、全件同点で順位根拠が無い。リンク「TOP 10 をすべて見る」の先は 30 日間 Top 30 で別基準。
- カテゴリ別ニュースとランキングに AI 関連フィルタが効かず、ノーベル賞・体重減少薬など非 AI 記事が出る。JS 無効時の静的 HTML と描画後で項目が入れ替わる。

**要求**:
1. `.hero` / `.hero > .container` / `.hero-inner` のルールを、head 内の主 `<style>`（:63-1183）へ移す。本文途中の `<style>` にファーストペイントのレイアウト決定ルールを置かない。
2. ランキング: 自サイトのスライドに固定高得点を付けて順位に混ぜない。ランキングページと同じデータ源・同じ尺度にするか、見出しを「編集部の注目 3 本」等に変えて選定基準を 1 文で示す。リンクラベルの件数・期間はリンク先と一致させる。変更は `index.html`（:2062-2065, 2146-2172）と `scripts/build-homepage-latest.js`（:195-260）の**両方**に同じ規則で入れる（毎日 `build-homepage-latest.js` が静的カードを上書きするため）。
3. AI 関連判定（`isAiRelevant`。`index.html:2092-2172`）を Node 側に移植し、カテゴリとランキングの両方に適用する。静的生成と JS 描画で同じ選定（AI 関連・星の高い順・重複除外）にする。
4. 第6弾の W1（「今日」「本日」の語の切り替え）と同じ箇所を触る。第6弾が入っている場合はその規則に合わせる。

**受け入れ条件**:
- Playwright chromium、キャッシュ無し・無スロットルで 1440x900 と 1280x800 の layout-shift 合計を各 5 回測り、最大値 < 0.05（現状 0.104 / 0.170）。`index.html` で `.hero > .container` の最初の出現行が `</head>` より前。
- `news/latest.json` を route で固定し、JS 無効時と有効時で `#rankingGrid .rc-title` と `#catGrid .cat-title` の配列が完全一致。`sections.research` の先頭に非 AI 記事を置いた fixture で `#catGrid` にその語が出ない。
- `#ranking .section-link` の文言中の N がリンク先 `h2` の Top N と一致。`href` に `day_slide_` を含む `.ranking-card` の `.rc-score` が「5.0 / 5」でない（または `.rc-rank` を持たない）。
- `tests/test_build_homepage_latest.py`・`tests/test_homepage_preserves_same_day_news.py`・`tests/test_homepage_week_titles.py` が通る。`scripts/check_mobile_page_height.py` の契約を壊さない。

---

## V5. デイリーレポート・アーカイブの検索（P1）

**現象**: `daily_reports_archive.html` は 170 件すべてが同一タイトルで、検索が成立しない（「Claude」で 0 件）。全文検索の双子ページと月次ダイジェスト（2026-05）が導線から漏れている。画面の更新時刻の記載（L101・L134 の「07:00」）が実スケジュールと違う。
**修正先**: `presentations/daily_reports_archive.html`（手書き。生成器無し）。`index.json`（`{date,file}`）と `searchable.json` は `src/auto_collect/html_report_archive.py:25` が毎日上書きする。**`index.json` の形は変えない**（既存コードが壊れる）。

**要求**: ページ側で `searchable.json`（毎日生成されている見出し付きのデータ）を取得し、各行に当日の代表見出し（または上位見出し数件）を出し、検索対象にする。`daily_reports/daily_reports_archive.html`（全文検索）への相互リンクを置く。ダイジェスト一覧は `presentations/digests/*.html` の実在ファイルと一致させる。「07:00」は実運用（cloud 06:00 / local 08:00）に合わせて「毎日更新」にする。取得失敗時は現状の一覧表示にフォールバックする。

**受け入れ条件**: Playwright で `.day-item .title` から日付を除いたユニーク数 ≥ 100/170（現状 1）。検索「Claude」の結果件数が 60〜70（`searchable.json` の 64 に対応）。`.digest-card` の `href` 集合 == `presentations/digests/*.html` の集合（現状 2026-05 が欠落）。ページ内に全文検索ページへの `a[href]` がある。モバイル 375px でタップ領域 < 24px の要素が 0（現状 164）。

---

## V6. Web フォントの描画ブロック（P1）

**現象**: Google Fonts の CSS（149KB）が描画をブロックし、11 ページは `assets/ntt-theme.css:11` の `@import` で直列に読み込まれる。モバイルの FCP が `api_docs` / `news_archive` / `slides_index` / `json_archive_viewer` で 1.9〜3.1 秒、`daily_news` は転送量の 86% がフォント。
**修正先**: `assets/ntt-theme.css:11`（`@import` を削除）、`index.html:61`、`presentations/day_slides_index.html:27`、`ai_coding_agents_guide.html:600`、`api_docs.html` / `news_archive.html` / `json_archive_viewer.html` / `recommended_tools/index.html` / `research_resources.html` など ntt-theme を読む各ページの `<head>`、および `day_slides_list`・ランキング・日次レポート・daily-news の生成器テンプレ。

**要求**: クロスオリジン CSS の `@import` を使わない。フォントは `<link rel="preconnect">` + 非ブロッキング読み込み（`media="print" onload="this.media='all'"` など）か、使用ウェイトだけに絞った `font-display:swap` にする。使っていないウェイト（`index.html:61` は 300/400/500/700/900 の 5 ウェイト）を削る。**見出しの数字ベースライン揃え（全角数字 + 日本語 serif の font stack）を壊さない**（トップのヒーロー）。

**受け入れ条件**: 対象ページをモバイル条件で 3 回測り、`document.styleSheets` の `type===3`（`@import`）が 0 件（現状 6 ページ）。`fonts.googleapis.com` 由来の stylesheet で `renderBlockingStatus==='blocking'` が 0 件（現状全ページ 1 件以上）。FCP 中央値: home ≤ 1000ms、`api_docs` / `news_archive` / `slides_index` / `json_archive_viewer` ≤ 1300ms、`daily_news` ≤ 3600ms（ネットワークの揺らぎが大きい場合は 3 回の中央値と最大・最小を併記）。

---

## 全体の検証（最後に必ず実行して結果を貼る）

1. `pytest`（`tests/` 全体。本弾と無関係な失敗は分けて報告）
2. `python scripts/check_site_freshness.py`（ローカル完結モード）
3. V1〜V6 の Playwright 検証スクリプトを `tmp\ux7-verify\` に置いて実行し、ログとスクショ（375x812 / 1440x900）を保存
4. `git status --short` と `git diff --stat`。生成器を実行して作り直した HTML と、その入力データの対応
5. 文字化けが無いこと（日本語が正しく表示されること）。必要が出たら `script/fix_day_slides_mojibake.py` の使用を報告

## 完了報告の書式

```
## 結果
| ID | 判定（✅/⚠️/❌） | 検証コマンドと結果（1行） | 変更ファイル |
## 受け入れ条件の実測値（変更前 → 変更後）
## git add -f が必要な新規ファイル
## 本弾と無関係な既存の失敗・behind/dirty
## 未解決・次弾候補
```
