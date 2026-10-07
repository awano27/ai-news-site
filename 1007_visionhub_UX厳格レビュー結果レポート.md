# visionhub.jp UX 厳格レビュー結果レポート（2026-10-07）

対象: https://visionhub.jp/ とその主要19ページ（PC 1440x900 / モバイル 375x812・DPR2・1.6Mbps+150ms・CPU 4x）。コード根拠は origin/main `3a0aa945`。

方法: 6観点（トップ / ナビ / 読解 / ハブ / 性能 / アクセシビリティ）が独立にレビューし、別のエージェントが各指摘を**再計測して反証を試みた**。下表の「最終」は反証後の重大度。

結果: 初回指摘 71 件 → 最終 P0 3 / P1 23 / P2 44 / 取り下げ 1。検証者が追加した見落とし 10 件。

- 重大度: P0 = 誤情報・機能不全 / P1 = 主要導線での明確な摩擦 / P2 = 仕上げ・一貫性
- 判定: confirmed = 再現 / corrected = 現象はあるが数値・原因・重大度を修正
- 指示プロンプト化の状況: P0 と導線系 P1 → 第6弾、生成器テンプレ側の P1 → 第7弾、P2 → 第8弾候補（未着手）

## 最優先の所見（P0）

- **home-01** 「今日の要点」が2日前(10/3号)の内容のまま、10/5号スライドへのリンクと「今日」ラベルで表示されている
  - 根本原因: index.html:1269-1278 に sitrep 文言が静的にハードコード（aria-label も 1269 行で『Claude Frontier Academy』固定）。scripts/update_home_fallback.py:234-246 の refresh_sitrep() は href しか自動更新せず、文言は CLI 引数（--sitrep-update 等）を渡した時だけ更新されるため、渡し忘れると古い文言が残る。ラベル『本日のスライド』は index.html:2071・2150…
  - 修正先: scripts/finalize_day_slide.py:54（update_home_fallback に sitrep 引数を渡す／スライドから導出）、scripts/update_home_fallback.py:234-246（data-slide-date 付与、遅延時は『今日』を『最新』『MM/DD』に切替、aria-label も更新）、scripts/build-homepage-latest.js:201 と index.html の todaySlideItem(2146-2150)/ランキ…

- **reading-01** 日次レポート(Top15)がLLM失敗時のフォールバック出力のまま公開され、英語タイトル・要約の複写・途中切れ・「重要記事0」を表示している
  - 根本原因: src/auto_collect/processor.py:257-295 の _fallback_process が LLM 不調時に title=原題(英語)、tldr=tagline[:80](:287)、summary=tagline[:300] を返し score を最大でも40+20程度に抑える。src/auto_collect/html_report_renderer.py:232 は score>=80 のみ high_score に数え(:312 で {{HIGH}} に代入)、src/auto…
  - 修正先: (1) src/auto_collect/llm_provider.py:128 の既定モデル 'meta/llama-3.3-70b-instruct' は NVIDIA NIM で 2026-08-26 に EOL(HTTP 410)。現行モデルへ更新し .github/workflows/auto-daily-report-cloud-fallback.yml で NVIDIA_MODEL を env 指定、scripts/secrets.local.bat.example:18-19 の記述も更新。(2)…

- **hubs-01** ニュースアーカイブ検索が古い索引を読み、直近45日のニュースと43本のスライドが検索不能。「毎朝07:00に更新」も偽
  - 根本原因: scripts/build_search_index.py:110-125 (main) を呼ぶ workflow・スクリプトが無い（.github scripts script src を grep しても参照なし。finalize_day_slide.py も呼ばない）。public-pages/news/search_index.json は直近のスライド PR (#115/#116) で手元実行された分だけが入り、その時点で存在したスライドしか拾っていない。presentations/news_archi…
  - 修正先: scripts/build_search_index.py は出力器。毎日の取込みは .github/workflows/daily-archive.yml:75 の `git add public-pages/news/*.json` が search_index.json も拾えるため、ここに build_search_index の実行ステップを追加するのが最短。generate-daily-news-json.yml:60 の git add 対象にも search_index.json は無いので同様に…


## 全指摘（観点別）


### トップページ（home）

| ID | 最終 | 判定 | 指摘 | ページ | 修正先（検証済み） |
|---|---|---|---|---|---|
| home-01 | P0 | confirmed | 「今日の要点」が2日前(10/3号)の内容のまま、10/5号スライドへのリンクと「今日」ラベルで表示されている | / | scripts/finalize_day_slide.py:54（update_home_fallback に sitrep 引数を渡す／スライドから導出）、scripts/update_home_fallback.py:234-246（data-slide-date 付与、遅延時は『今日』を『最… |
| home-03 | P1 | confirmed | 「今日のスコア上位3本」は自サイトのスライドを固定5.0点・1位に置き、全件5.0点で順位根拠がなく、「TOP 10」リンク先は30日間 Top 30 で別基準・別内容 | /, /presentations/ai_ranking_report_latest.html | index.html:2062-2065,2146-2172（コピー・pin・件数表記）、scripts/build-homepage-latest.js:195-260（collectRankingItems の同点処理・自社スライドの固定5.0）。静的カードは bhl.js が毎日上書きするの… |
| home-04 | P1 | confirmed | カテゴリ別ニュースとランキングに AI 関連フィルタが効かず非AI記事（ノーベル賞・体重減少薬）が出る。JS無効時HTMLと描画後で項目が入れ替わる | / | index.html:2092-2172,2695-2737（isAiRelevant を共有しカテゴリにも適用）、scripts/build-homepage-latest.js:195-260（Node 側へ同判定を移植）。毎日の bhl.js 実行で静的カードが上書きされるため両方同時に直す。 |
| home-06 | P1 | corrected | desktop の CLS 0.104 はヒーロー container の幅指定が本文中の遅い <style> にあるため、初回描画で 435px→1280px に跳ねる | / | index.html の head 内主 <style>（:63-1183）へ :1863-1865 の .hero / .hero > .container / .hero-inner ルールを移す。bhl.js は CSS を触らないので上書きの危険なし。 |
| home-02 | P2 | corrected | 「最新データ: 2026-10-05 09:00 JST」「最終更新 09:00」は実際の更新時刻ではなく、スライド日付に固定時刻 09:00 を付けた値で、同じ画面の他の日付と矛盾する | / | scripts/build-homepage-latest.js:121-125,411-413,721（generated_at を実生成時刻、スライド日付は別キー slide_date）、index.html:2521-2523,2562-2567（表示と日付ゲート）、scripts/buil… |
| home-05 | P2 | corrected | 最初のビューに『今日何が新しいか』が出ない。最新スライドの題名は desktop で y≈880 以降、mobile で約1.4画面下 | / | index.html（hero/sitrep 直下に最新スライドの日付+題名を置く、または sitrep を同一スライド由来にする）、scripts/update_home_fallback.py と scripts/build-homepage-latest.js:416-457 の fallb… |
| home-07 | P2 | confirmed | latest.json の日付判定が厳しすぎ、日付不一致または取得失敗でカテゴリ欄の正常な静的カードを『更新中 / Latest data pending』に置き換える | / | index.html:2511-2523,2695-2705,2223-2227（日付ゲートを news_date 基準にし、失敗時は静的カードを残す）。JS 直書きで生成物ではない。 |
| home-08 | P2 | confirmed | カテゴリ別ニュースのカードは題名と出典のみで、日付・要約が無く、右上の円＋斜線アイコンは意味を持たない。『注目4カテゴリ』と実際3枚 | / | index.html:2247,2695-2737,845-861 と scripts/build-homepage-latest.js の collectCategoryItems（静的カード生成）。両方揃えて直す。 |
| home-09 | P2 | confirmed | ページ長（desktop 7.8画面 / mobile 11.6画面）に対し、重複導線・空白カード・同一画像の使い回し・定数だけの統計パネルが密度を下げている | / | index.html の resources(:2333-2440)・archive stats(:2303-2306)・比較バナー(:1941-1949)。手書き部で生成物ではない。ただし #statSlides は bhl.js:481 が毎日上書き。 |
| home-10 | P2 | confirmed | ラベルの用語揺れと不要な英語装飾ラベル（同じ行き先に3種の呼称、VIEW DETAIL×12、Explore 等） | / | index.html（ラベル直書き・cardHtml）と scripts/build-homepage-latest.js:222-245（静的ランキングタグ）。 |
| home-11 | P2 | corrected | ヒーローの肖像写真（マックス・プランク）は意図が伝わらず、mobile では右端の細片が日付テキストに重なり出典も非表示 | / | index.html:335-356 と :1869-1870（メディアクエリ順序と width 指定の整理、credit の可視化）。手書き CSS で生成物ではない。 |
| home-12 | P2 | confirmed | 順位数字・補助ラベルの低コントラストと極小タップ領域（rc-rank 1.51:1、ラベル 11px で 4.07:1、フッターリンク高さ19px） | / | index.html 手書き CSS（.rc-rank、補助ラベル色、フッターリンクの padding/min-height）。静的ランキングカードの HTML は bhl.js が生成するが色は CSS 側。 |

### ナビゲーション・導線（nav）

| ID | 最終 | 判定 | 指摘 | ページ | 修正先（検証済み） |
|---|---|---|---|---|---|
| nav-01 | P1 | corrected | モバイルで ntt-theme 系ヘッダーのナビが全消しし、ドロワーも無い（ランキングも同様） | slides_list, coding_agents_guide, news_archive, recommended_ | assets/ntt-theme.css (the HTML snippet is only a comment, and each of the 11 pages carries its own copy of the header markup). Static pages are edite… |
| nav-04 | P1 | confirmed | ホームのヘッダーが sticky にならず、スクロールすると消えてモバイルのメニューボタンに戻れない | home | index.html only, in the <style> block (not a generated section). Replace html/body overflow-x:hidden with overflow-x:clip (or hide only on body). The… |
| nav-06 | P1 | confirmed | daily-news のヘッダーがモバイル 375px で崩れ、ロゴ・日付・ナビがヘッダー外にはみ出す | daily_news | src/auto_collect/daily_news_template.html. daily_news_page.py renders it (TEMPLATE_PATH) for both daily-news/index.html and archive pages. The 06:00 … |
| nav-02 | P2 | corrected | ヘッダー/フッター/ナビが8系統に分裂し、同じ「ニュース」「リソース」でもページごとに行き先と項目が違う | home, daily_news, slides_index, slides_list, slide_latest, r | No shared header component exists. Static pages (index.html, about/contact/404, articles, ntt pages, day_slides_index.html) are hand-edited. Generate… |
| nav-03 | P2 | corrected | CTA・ナビの文言が行き先と合わない（「今日のスライド」は2日前、「最新スライド」が2通り、「比較」など） | home, slides_index, slides_list, coding_agents_guide, news_a | The ntt label lives in the per-page copies (10+ static files plus the ntt-theme.css comment) and in script/build_day_slides_list.py:388-392, which is… |
| nav-05 | P2 | corrected | 古い日次スライド 59 ページの「PDFダウンロード」が全て 404 | slide_latest | The 60 old files in presentations/day_slides/ are hand-authored static pages that daily generation does not touch. Fix them with a one-time bulk scri… |
| nav-07 | P2 | corrected | スライド内の「ブランド/Archive」リンクが 404 になる日がある（09/14・09/15 ほか） | slide_latest | The 4 slide files in presentations/day_slides/ are static, hand-written pages and daily generation does not rewrite them. Fix ai_governance_guide.htm… |
| nav-08 | P2 | corrected | 役割が重なる一覧ページが並立し、孤立ページとハブ/ダイジェストの行き止まりがある | slides_index, slides_list, daily_reports_archive, news_archi | index.html (hand-written), presentations/ai_archive_searchable.html and presentations/daily_reports_archive.html (static), src/auto_collect/report_te… |
| nav-09 | P2 | confirmed | About/Privacy/Contact へ辿れないページが 19 ページ中 11 ページ | daily_news, slides_list, slide_latest, ranking, coding_agent | ntt pages: edit each page's footer plus the ntt-theme.css comment snippet (static). daily-news and auto_daily_report: src/auto_collect/daily_news_tem… |
| nav-10 | P2 | corrected | ブランド名・配色・フォントがページ群で別サイトのように切り替わる | home, daily_news, auto_daily_report, article_claim_evidence, | index.html brand-text and about/contact/404/hub (static). daily_news_template.html and report_template.html (daily overwrite, template only). article… |
| nav-11 | P2 | confirmed | ナビドロワーのキーボード操作が不完全（フォーカスがドロワーに入らない／Esc 不可／閾値不一致） | home, slides_index, auto_daily_report | index.html (JS setOpen around lines 2836-2864 plus the 880 constant), src/auto_collect/report_template.html (906-920, daily overwrite so template onl… |
| nav-12 | P2 | corrected | /daily-news-csv/ のヘッダーが旧ドメイン(awano27.github.io)を指し、モバイルでは戻る導線が消える | daily_news | This file is not generated in this repo. It is deployed daily from the awano27/daily-ai-news repository, so any edit here is overwritten by the next … |

### 読解・本文ページ（reading）

| ID | 最終 | 判定 | 指摘 | ページ | 修正先（検証済み） |
|---|---|---|---|---|---|
| reading-01 | P0 | corrected | 日次レポート(Top15)がLLM失敗時のフォールバック出力のまま公開され、英語タイトル・要約の複写・途中切れ・「重要記事0」を表示している | auto_daily_report | (1) src/auto_collect/llm_provider.py:128 の既定モデル 'meta/llama-3.3-70b-instruct' は NVIDIA NIM で 2026-08-26 に EOL(HTTP 410)。現行モデルへ更新し .github/workflows/a… |
| reading-02 | P1 | corrected | daily-news の大半を占める GitHub/HuggingFace 自動エントリ(35/149件)が英語・情報ゼロのまま同じニュースカードとして混在し、『見逃せない 48』も水増ししている | daily_news | src/auto_collect/daily_news_page.py(timeline.extend が github/benchmark を記事と同一 timeline に結合する :268-272 付近、high_count = score>=80 を種別無視で集計 :296、_render… |
| reading-03 | P1 | confirmed | モバイルで daily-news / auto_daily_report の固定ヘッダーからロゴ・日付が溢れ、本文や絞り込みバーに重なる | daily_news, auto_daily_report | src/auto_collect/daily_news_template.html:58-76(.bar 固定高52・.bar-logo/.bar-date に nowrap なし)、:140-146(.filter-bar sticky top:52px)、:270-282(モバイル @medi… |
| reading-04 | P1 | corrected | ランキングの本文に全角ピリオド・二重句点・定型の『活用ポイント』・空のプレースホルダ行が混入している | ranking | 空行の原因はレビュアーの『セクター行が0件でも出力』ではなく src/generators/ranking_data_parser.py:55-60 が Markdown 表の区切り行 '/---/---/---:/---:/---/'(scripts/generate_ranking_input… |
| reading-05 | P1 | confirmed | ランキングページ末尾の導線が背景と同色で読めず、モバイルでは31.7画面あるのにセクションナビが非表示になる | ranking | src/generators/ranking_template.py:713-727(footer の inline 色が暗背景前提で .site-footer の CSS が無い)、:334-335(@media(max-width:900px){.nav{display:none}} で代替な… |
| reading-06 | P1 | corrected | 前後のスライドへ移動できない日がある(10/3 は『翌日』が『一覧へ』のまま、10/4 には『翌日』が無い)。ナビの形式も日ごとにバラバラ | slide_latest | 生成器は正しい: scripts/inject_slide_nav.py:19-45,68-86 は全スライドを走査して前後を毎回再計算する冪等処理で、`python scripts/inject_slide_nav.py` を再実行するだけで 10/03 の翌日リンクは直る(CLAUDE.md … |
| reading-07 | P2 | confirmed | Claude Code ガイドがモバイルで横にはみ出す(unbreakable な code 見出し) | hub_claude_code | presentations/hubs/claude-code-guide-2026.html:125(code{...} に overflow-wrap なし)、:315(h3 内の長い code)。手書き静的HTMLで日次 cron に上書きされない(sitemap/内部リンク/JSON-LD … |
| reading-08 | P2 | corrected | 長文ガイド類で更新日が古く、37.7画面のページに目次が無く、読了後の次の行動も欠けている | coding_agents_guide, hub_claude_code, digest_2026_05 | presentations/ai_coding_agents_guide.html(手書き)、presentations/hubs/claude-code-guide-2026.html:412-430(固定リスト)、scripts/build_monthly_digest.py(月次出力。前後リ… |
| reading-09 | P2 | corrected | ランキングページはモバイルで本文が11秒間表示されない(同期読み込みの mermaid 1.46MB と chart.js がhead に残っている) | ranking | src/generators/ranking_template.py:31-32 の2つの <script> を </body> 直前(インライン初期化 :728-760 の直前)へ移動、または defer+DOMContentLoaded 初期化へ。mermaid.initialize が :7… |
| reading-10 | P2 | confirmed | daily-news カードの走査性が低い(日時なし・日本語が斜体・X投稿は題名=本文・見出しと『開く』が同リンク・チャート読込でレイアウトが大きく動く) | daily_news | src/auto_collect/daily_news_page.py:142-178(_render_news_card)/:181-213(_render_x_card、alt は :191 で空文字固定)、src/auto_collect/daily_news_template.html:2… |
| reading-11 | P2 | confirmed | スライドのヒーロー見出しが375pxでカタカナ語の途中・括弧の途中で改行される | slide_latest | .claude/skills/daily-ai-slide-generator-skill/SKILL.md(雛形となる CSS 規約)と当日の presentations/day_slides/day_slide_2026_10_05.html:34,161,253,285 に `word-br… |
| reading-12 | P2 | confirmed | 補助文字の色トークン(#6a6a82)とバッジ配色が AA 未満で、11px 前後の小文字に使われている | daily_news, auto_daily_report, ranking | src/auto_collect/daily_news_template.html:31、src/auto_collect/report_template.html:36(--t3 を明るくする)、src/generators/ranking_template.py:296(.score-biz … |

### 一覧・アーカイブ系ハブ（hubs）

| ID | 最終 | 判定 | 指摘 | ページ | 修正先（検証済み） |
|---|---|---|---|---|---|
| hubs-01 | P0 | confirmed | ニュースアーカイブ検索が古い索引を読み、直近45日のニュースと43本のスライドが検索不能。「毎朝07:00に更新」も偽 | news_archive, home, api_docs | scripts/build_search_index.py は出力器。毎日の取込みは .github/workflows/daily-archive.yml:75 の `git add public-pages/news/*.json` が search_index.json も拾えるため、ここに… |
| hubs-03 | P1 | corrected | 日次スライド一覧のモバイルヒーロー: 最新号に cover 画像がある日は画像内の文字と見出しが重なって読めず、LCP が 10.5 秒 | slides_list | script/build_day_slides_list.py:124-128 の cover_media が常に loading="lazy" decoding="async" を出力し、:399 の hero にも流用。モバイルの重なりは :360-362。presentations/day_… |
| hubs-04 | P1 | corrected | 日次スライド一覧の主CTA『この号を読む →』が文字色の詳細度負けでコントラスト 1.3:1。エージェント系チップも 3.57:1/10px | slides_list | script/build_day_slides_list.py:252（`.nb a` を `.nb a:not(.cta)` にする、または `.nb .cta` に詳細度を上げる）と :37 の CATS['agent'] の色（#008300）。presentations/day_slide… |
| hubs-05 | P1 | confirmed | デイリーレポート・アーカイブ: 170 件すべて同一タイトルで検索が成立せず、全文検索の双子ページと月次ダイジェスト(2026-05)が導線から漏れている | daily_reports_archive, home | presentations/daily_reports_archive.html は手書きで生成器なし。index.json と searchable.json は src/auto_collect/html_report_archive.py:25 rebuild_archive_index（レ… |
| hubs-06 | P1 | confirmed | API ドキュメントと llms.txt が案内する /news/YYYY-MM-DD.json は 2026-06-14 以降 404（実データは /public-pages/news/） | api_docs | presentations/api_docs.html:176-177 と、説明例 :183 付近。llms.txt:10-12 も同様。両ファイルとも手書きで生成器・workflow は無い（llms.txt は最新スライド行を手で更新している）。日次生成で上書きされる危険は無い。ただしドキュメ… |
| hubs-09 | P1 | confirmed | 日次スライド一覧: 検索 0 件で何も表示されず、検索状態が URL に残らず、16 か月のうち 13 が閉じたまま月ジャンプも無い | slides_list | script/build_day_slides_list.py（:45 OPEN_MONTHS、:438 付近の #nbHit、:476-510 の applyFilter、main 内への空状態ノード追加）。presentations/day_slides_list.html は全面再生成物のた… |
| hubs-02 | P2 | corrected | 日次スライド一覧(day_slides_index)の件数・並び順・欠落が実データと不一致（429 表示 vs 実在 431、10月が 10/04,10/05,10/03 の順） | slides_index, slides_list, home | presentations/day_slides_index.html は手書きで、日次生成物ではない。CLAUDE.md が『手で更新』と定める対象。update_month_archive（scripts/publish_image2_day_slide.py:454）が slide_card… |
| hubs-07 | P2 | corrected | 一覧系ハブの役割分担が画面で伝わらず相互導線が欠け、同じ語の検索結果・件数が各ページで食い違う | slides_index, slides_list, news_archive, daily_reports_archi | slides_list は script/build_day_slides_list.py の生成物で、公開ごとに上書きされるため、リンクは生成器側に入れる。slides_index・news_archive・daily_reports_archive・json_archive_viewer は手… |
| hubs-08 | P2 | corrected | ニュースアーカイブの分類・出典・URL・要約が生データのまま（posts 2,116件、出典空 396件、壊れた URL 40件、ニュース要約 0件） | news_archive | scripts/build_search_index.py:89-96（category/source/summary の詰め込み）と :116-121（2MB 超過時の summary 削除）。presentations/news_archive.html:225 の option 生成。索引は… |
| hubs-10 | P2 | corrected | JSONアーカイブビューア: 509 件を全件一斉描画（モバイル 212 画面）、DL リンクが全件同一の 3.3MB ファイル、ボタンが縦書き化、詳細モーダルが操作不能 | json_archive_viewer | presentations/json_archive_viewer.html:450-504（renderArchiveList）、:236（.archive-actions に flex-wrap）、:386（searchInput）、:528-568（viewDetails）。手書きで生成器な… |
| hubs-11 | P2 | corrected | おすすめツール: 更新日が 39 日前で止まり、バッジ 206 と表示件数 226 が不一致、『最近追加』が 67 件で意味を成さず、9セクション・モバイル 82.7 画面に目次も固定フィルターも無い | recommended_tools | presentations/recommended_tools/index.html:367（更新日）、:369（バッジ）、:2676-2716（MAY_ADDED / RECENT_ADDED）、:64（.controls）。presentations/recommended_tools.js … |
| hubs-12 | P2 | corrected | モバイルの一覧でタイトル切り詰めと検索入口の遠さ・小さい操作部品が多い | slides_index, slides_list, daily_reports_archive | script/build_day_slides_list.py:366-368（モバイルの .card .t / .d）。slides_list は公開ごとに上書きされるので生成器側のみ。presentations/day_slides_index.html の .slide-title と pr… |

### 性能（perf）

| ID | 最終 | 判定 | 指摘 | ページ | 修正先（検証済み） |
|---|---|---|---|---|---|
| perf-01 | P1 | confirmed | ranking: 1.46MB の mermaid をヘッド同期で読み込み、モバイルで約12秒間白画面 | ranking | src/generators/ranking_template.py:31-32(script タグ)、:731(mermaid.initialize)、:745 以降(new Chart)。生成物 presentations/ai_ranking_report_latest.html と ai_… |
| perf-02 | P1 | corrected | Google Fonts CSS(149KB)がレンダーブロッキング、11ページは ntt-theme.css の @import で直列チェーン | home, slides_index, slides_list, api_docs, news_archive, rec | assets/ntt-theme.css:11(@import 削除)＋ ntt-theme を読む各ページに非ブロッキング link を追加。手保守: assets/ntt-theme.css, index.html:61, presentations/day_slides_index.html… |
| perf-03 | P1 | corrected | slides_list: LCP の hero カバー画像が loading=lazy、サムネも原寸 JPEG(最大423KB)・width/height なし | slides_list | script/build_day_slides_list.py:124-128(cover_media に hero 用の分岐: loading 属性なし・fetchpriority=high・width/height、strip/thumb 用に縮小サムネの URL)。presentations… |
| perf-04 | P1 | corrected | daily-news: CLS がモバイル0.29〜0.36、デスクトップ0.12〜0.21(Webフォント入れ替えとグラフの高さ未確保) | daily_news | src/auto_collect/daily_news_template.html:19(display=swap → optional、またはフォールバックの size-adjust/ascent-override で折り返しを一致、または日本語本文のウェブフォント廃止=perf-05)と :1… |
| perf-05 | P2 | corrected | Web フォントの転送量が過大(Noto Sans JP が12〜62本、daily-news では総転送の86%)かつページごとに構成がバラバラ | daily_news, coding_agents_guide, slides_index, ranking, home | assets/ntt-theme.css:11、index.html:61、presentations/ai_coding_agents_guide.html:600、presentations/day_slides_index.html:27(手保守)。生成物: src/auto_collect… |
| perf-06 | P2 | confirmed | ホーム(デスクトップ)CLS 0.104: ヒーロー途中のインライン <script> で先頭だけ描画され後からヒーローが伸びる | home | index.html:1232-1241 のインライン script(#heroFreshnessLag 直後)。この script は heroDate の span が空のときだけ書くフォールバックで、span は生成器が常に埋める(fallback:latest-slide マーカー内)ため… |
| perf-07 | P2 | corrected | ホーム(モバイル)LCP 2.1〜2.7s: ヒーロー背景(CSS background)が CSS 解決後に初めて発見される | home | index.html:37 付近の head に max-width:768px 用 preload を追加(手保守)。index.html はスクリプトでマーカー内(fallback)・CSP meta・#categories のみ再生成される。head の preload 行は上書き対象外。 |
| perf-08 | P2 | corrected | news_archive: 検索結果の後読みで下の「機能カード」が押し出され、デスクトップ CLS 0.08 | news_archive | presentations/news_archive.html(手保守の静的ファイル、生成元なし)の #searchResults へ min-height(読み込み中のスケルトン相当)。search_index.json は scripts/build_search_index.py が生成する… |
| perf-10 | P2 | confirmed | daily-news の HTML が 375KB(gzip 75KB): インライン report-data の items 137KB は未使用 | daily_news | src/auto_collect/daily_news_page.py:317("items": timeline)と :340(json.dumps(report_data) をそのまま {{REPORT_DATA_JSON}} へ)。インライン用に items を除いた dict を作り、:3… |
| perf-11 | P2 | confirmed | api/daily-news.json が 556KB(gzip)/2.9MB: entries と items が同一内容の重複 | json_archive_viewer, api_docs | scripts/generate-daily-news-json.js:308-309, 323-324, 312, 327(items 削除と整形出力の見直し)。presentations/api/daily-news.json と daily-news-latest.json は .githu… |
| perf-09 | drop | corrected | home が起動時に不要なデータを追加取得(latest.json 二重取得、day_slides_index.html 27KB を no-store で取得) | home | index.html(手保守)だが修正価値が低い。変更する場合は latest.json を1回取得して共有するだけに留め、day_slides_index.html の fetch は残す。 |

### アクセシビリティ（a11y）

| ID | 最終 | 判定 | 指摘 | ページ | 修正先（検証済み） |
|---|---|---|---|---|---|
| a11y-01 | P1 | confirmed | 日次スライド一覧のヒーロー主CTA「この号を読む →」が 1.3:1、カテゴリチップ 231 個が AA 未達 | slides_list | script/build_day_slides_list.py (CSS :252/:271, CATS :37-38, chip :121 and :278). presentations/day_slides_list.html is generated: regenerated by scr… |
| a11y-03 | P1 | confirmed | AIランキングのフッターが背景色なしで白/黄文字が見えず、Biz スコアピルが 3.13:1 | ranking | src/generators/ranking_template.py (:713-727 footer markup with inline #fff/var(--yellow)/#7e8799 and NO .site-footer CSS anywhere in the file; :296 … |
| a11y-04 | P1 | confirmed | AIデイリーレポートのアコーディオンがキーボードで開けず、閉じた詳細内のリンクが不可視のままフォーカスされる | auto_daily_report | src/auto_collect/report_template.html (:383 .row-head style, :435-442 collapsed .row-detail, :906-908 click-only listener) and src/auto_collect/html_… |
| a11y-02 | P2 | corrected | モバイルのメニュー展開時にフォーカスが背面へ抜ける（トップ・スライド索引）。Esc 後のフォーカス復帰もない | home, slides_index, auto_daily_report | index.html (nav before toggle at :1201; setOpen at :2841 in current origin/main, reviewer's :2836 is a few lines off; drawer breakpoint :212 max-widt… |
| a11y-05 | P2 | corrected | トップの配色トークンが AA 未達（ランキング順位 1.51:1、週カード 3.85:1 ほか）、写真クレジットが 10px/透過 .55 | home | index.html (hand-edited static file; tokens :82 --on-dark-mu2, :85 --on-light-mu2; .sitrep-sep :605, .sitrep-key :611, .week-day :774, .week-go :811,… |
| a11y-06 | P2 | confirmed | ダーク系レポート 2 ページの補助文字色 --t3 (#6a6a82) が 3.3〜3.8:1 | daily_news, auto_daily_report | src/auto_collect/daily_news_template.html:31 and src/auto_collect/report_template.html:36 (--t3). Both pages are regenerated daily (06:00 JST cloud f… |
| a11y-07 | P2 | corrected | ランドマーク・スキップリンク・見出し階層がページごとにばらばら（main 欠落 4 ページ、スキップリンクは 19 ページ中 4） | daily_news, ranking, auto_daily_report, json_archive_viewer, | src/auto_collect/daily_news_template.html:285-302, src/auto_collect/report_template.html:765-792, src/generators/ranking_template.py:365-373 and :396… |
| a11y-08 | P2 | corrected | 12px 未満の文字が「読ませる情報」にも使われている（記事ごとの出典・score・開くリンク、根拠注記、引用元） | daily_news, slides_list, coding_agents_guide, slide_latest, | assets/claim-evidence.css (:2 font-size .78rem, :15 caveat opacity; hand-edited, but claim-evidence blocks are inserted by scripts/render_claim_evide… |
| a11y-09 | P2 | corrected | smooth スクロールと無限点滅が prefers-reduced-motion で止まらない | home, daily_news, auto_daily_report | index.html:99 (hand-edited), presentations/day_slides_index.html (smooth scroll rule), src/auto_collect/daily_news_template.html:42 and src/auto_coll… |
| a11y-10 | P2 | corrected | モバイルのタップ領域不足（開く ↗ 149 件が 40x20、レポート CTA 170 件が 103x20 かつ同一リンク二重） | daily_news, daily_reports_archive, home, slide_latest, ranki | src/auto_collect/daily_news_template.html:240 (.card-foot a.open; regenerated daily), presentations/daily_reports_archive.html:73 and JS template :20… |
| a11y-11 | P2 | confirmed | Claude Code ガイドがモバイルで横スクロール（scrollWidth 402 > 375）、原因は h3 内の長い code | hub_claude_code | presentations/hubs/claude-code-guide-2026.html:125 (code rule) - hand-edited static page; scripts/build_internal_links.py / build_monthly_digest.py o… |
| a11y-12 | P2 | corrected | JSON アーカイブビューアーのボタンが 3.68:1・1,533 個の操作要素、検索欄などがプレースホルダーのみのラベル（4 ページ） | json_archive_viewer, daily_news, auto_daily_report, recommen | presentations/json_archive_viewer.html (:19 --primary, :242-247 .btn, :386 input; hand-edited), src/auto_collect/daily_news_template.html:325 and src… |

## 検証者が追加した見落とし

| 観点 | 重大度 | 内容 | 原因 |
|---|---|---|---|
| home | P2 | <title>/og:title/twitter が『今日のAIスライド』と断定するが最新スライドは2日前（共有カード・検索結果で鮮度を偽る） | index.html の head 内 <title>・og:title・twitter:title が静的で、finalize_day_slide.py / update_home_fallback.py / build-homepage-latest.js のどれも更新対象にしていない。 |
| nav | P2 | スキップリンクと main ランドマークが ntt 系・daily-news・ランキング・Top15 レポートに無い | The ntt-theme.css snippet has no skip link or main wrapper. daily_news_template.html, report_template.html and ranking_template.py have no main eleme… |
| nav | P2 | sitemap に下書き派生の孤立スライド 13 件が noindex なしで載っている（内部スキル文書も公開） | Working variants were committed to presentations/day_slides/ and listed in sitemap.xml. No guard excludes non-canonical slide filenames. |
| nav | P2 | article・hub・404 の静的ヘッダーはスクロールで消え、長いページでメニュー導線が失われる | Each page has its own header CSS and these have position:static. article uses its own light-theme header. |
| reading | P0 | cloud run が LLM 不通のフォールバック出力を『success』で公開し、正常な local override を上書きする。CI にも検知がない | src/auto_collect/llm_provider.py:128 の既定モデルが EOL。scripts/publish_daily_report.py:198-221 の priority 保護は daily-news/* のみで auto_daily_report 系(presenta… |
| reading | P2 | 月次ダイジェストが 2026-05 で止まっているのにトップ『リソース』カードの最新リンクが 2026-05 のまま(4か月欠落) | scripts/build_monthly_digest.py は CI 外の手動実行(記憶: 月次ダイジェストは手動生成)で、6〜9月分が未生成。トップのリンクも手書き。 |
| perf | P2 | news_archive: 検索インデックス 303KB を初期表示のたびに全件取得 | presentations/news_archive.html:225 でインデックス全体をロード時に取得する設計。検索語やフィルタ未操作でも全件を転送する。 |
| a11y | P2 | daily_news のカテゴリタブ・並べ替え等のトグルが選択状態を色だけで示す（aria-pressed/selected なし）、149 件の「開く ↗」はタイトルと同一リンクの重複 | src/auto_collect/daily_news_template.html の tabs（`<button class="tab on" data-cat=...>`）と card-foot の `<a class="open">開く ↗</a>`、src/auto_collect/rep… |
| a11y | P2 | 320px 幅のリフローが daily_news・auto_daily_report・ranking で破綻（水平スクロール） | daily_news_template.html の header .bar-nav（折り返し・非表示化なし）、report_template.html の .gh-stars（nowrap 想定）、src/generators/ranking_template.py の ranking 見出し/… |
| a11y | P2 | day_slides_index が reduced-motion でも smooth scroll、json_archive_viewer の #sortSelect が無名 | presentations/day_slides_index.html の html{scroll-behavior:smooth} に reduce 上書きなし。presentations/json_archive_viewer.html の sortSelect マークアップに名前なし。いずれ… |

## 補足
- 最新スライドは 2026-10-05（今日の2日前）。スライド制作の遅れ自体は運用の問題で、改修対象ではない。指摘は「遅れた状態をサイトがどう表示するか」に限定している。
- 自動生成物（daily-news / auto_daily_report / ai_ranking_report / day_slides_list / index.html の fallback 領域）は毎日上書きされるため、修正先は生成器・テンプレート側に限る。各指摘の「修正先」はその確認済み。
- 証跡の置き場: scratchpad の `review/evidence2/`（スクショ・計測 JSON）と `review/result.json`（本レポートの元データ全文）。
