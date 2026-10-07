# Codex 指示プロンプト — 「嘘の表示」と「行き止まり」を止める（UX 厳格レビュー 第6弾）

対象リポジトリ: `C:\develop\ai-news-site`（本番 https://visionhub.jp/）
根拠: `1007_visionhub_UX厳格レビュー結果レポート.md`（6観点で指摘 → 別エージェントが再計測して反証、71件中 P0=3 / P1=23 / P2=44）。本弾は **P0 の3件と、導線を断つ P1** だけを扱う。

**完了の形**: 下記 W1〜W5 の「受け入れ条件」の検証がすべて通り、完了報告（末尾の書式）を書くまで。初回実装で止まらない。落ちた検証は自分で原因を直して再実行する。見た目の全面刷新はしない。

---

## 最初に守ること

1. この指示書を最後まで読んでから作業する。
2. **ローカルの `C:\develop\ai-news-site` は origin/main より 170 コミット以上遅れ、未コミット差分も多い。ここでは作業しない・触らない。** 代わりに origin/main の分離 worktree を作って、そこで作業する:
   ```
   git -C C:\develop\ai-news-site fetch origin
   git -C C:\develop\ai-news-site worktree add --detach C:\develop\ai-news-site-ux6 origin/main
   ```
   既に `C:\develop\ai-news-site-ux6` がある場合は、`git status --short` が空で HEAD が origin/main と一致する時だけ再利用する。そうでなければ停止して報告。
3. python は `where python` の先頭が hermes venv になることがある（playwright 不在で壊れる）。`C:\Users\awano\AppData\Local\Microsoft\WindowsApps\python.exe` を明示して使う。Node の Playwright は `set NODE_PATH=C:\develop\ai-news-site\node_modules` で参照する（worktree には node_modules が無い）。
4. 検証スクリプトとログ・スクショは worktree 内の `tmp\ux6-verify\` に保存する（コミット対象外・完了報告にパスを書く）。動作確認は MCP 対話操作ではなくターミナル実行の Playwright スクリプトで行う（証跡を残すため）。
5. `.gitignore` が `scripts/` `script/` `.github/` の新規ファイルを無視する。新規ファイルを作ったら `git status --ignored --short` で見える化し、完了報告に「`git add -f` が必要なファイル」として列挙する（自分では add しない）。
6. 全ファイル UTF-8（BOM なし）。`.bat` / `.cmd` は ASCII のみ。

## 安全境界（理由つき。変更は worktree の作業ツリーに残し、レビューに回す）

- `git commit` / `push` / PR 作成 / deploy / `gh workflow run` はしない（レビュー前の成果物を外に出さないため）。`gh run list` `gh run view --log` `curl -sS` など読み取りは可。
- ssh / scp / リモートアクセス、DB スキーマ変更、外部サービスへの書き込みはしない。
- **実 LLM・実 API の呼び出しはしない**（NVIDIA 等）。テストは mock / fixture で行う。
- GitHub の secrets / variables / 設定値は変更しない。`TYPESAFE_API_KEY` などの秘密情報をログ・出力に出さない。
- `script/build_day_slides_index.py` は**実行しない**（手作りの `presentations/day_slides/meta_index.json` の分類と番号を破壊する。一覧の再生成は `script/build_day_slides_list.py` のみ）。
- ローカル完結の検証（pytest、Node テスト、Playwright、dry-run、冪等な生成器の再実行、`scripts/check_site_freshness.py`）は承認なしで何度でも実行してよい。

## 停止条件（これ以外では止まらない）

- 編集対象ファイルが origin/main と衝突している、または安全境界に触れないと進めない時だけ停止して報告する。
- 無関係な behind / dirty は完了報告に書いて続行する。
- モデル名のように**ユーザー判断が要る値**（W2）は、推測で埋めずに「判断待ち」として完了報告に書き、それ以外の作業は完了させる。

---

## 対象と非対象

| ID | 内容 | 重大度 | 主な修正先 |
|---|---|---|---|
| **W1** | 「今日」と言い張る表示をやめる（要点・ランキング見出し・title） | P0 | `scripts/update_home_fallback.py`、`scripts/build-homepage-latest.js`、`index.html`、`scripts/check_site_freshness.py` |
| **W2** | LLM 失敗時のフォールバック出力を公開しない・検知する | P0 | `scripts/publish_daily_report.py`、`src/auto_collect/`、workflow |
| **W3** | 検索索引を自動再生成し、API 案内の URL を実在に合わせる | P0/P1 | `scripts/build_search_index.py` の配線、`presentations/api_docs.html`、`llms.txt`、`presentations/news_archive.html` |
| **W4** | モバイルでナビに辿れない・ヘッダーが崩れるページを直す | P1 | `index.html`、`assets/ntt-theme.css`、各静的ページ、`src/auto_collect/*_template.html`、`src/generators/ranking_template.py`、`script/build_day_slides_list.py` |
| **W5** | 前後スライドへ移動できない日をなくす | P1 | `scripts/inject_slide_nav.py`、`scripts/check_site_freshness.py` |

非対象（第7弾以降）: 生成器テンプレ側のコントラスト・CLS・LCP 改善、ランキング本文の文字化け、トップのランキング選定、daily-news の GitHub/HF 分離、日次レポートの検索、P2 全般。**トップ h1（`#heroIdentity`）は固定**（CLAUDE.md）なので触らない。

## 毎日の自動生成で上書きされる場所（編集先を間違えない）

| 見た目の場所 | 直接編集 | 直すべき所 |
|---|---|---|
| `index.html` の `<!-- fallback:... -->` 内と `news/latest.json` | 上書きされる | `scripts/update_home_fallback.py` / `scripts/build-homepage-latest.js`（`ai-news.yml` / `generate-daily-news-json.yml` / `pages.yml` が毎日実行） |
| `daily-news/index.html`、`daily-news/archive/*.html` | **禁止** | `src/auto_collect/daily_news_template.html`、`daily_news_page.py`（06:00 cloud / 08:00 local が毎日再生成） |
| `presentations/auto_daily_report.html` ほか日次レポート | **禁止** | `src/auto_collect/report_template.html`、`html_report_renderer.py` |
| `presentations/ai_ranking_report_latest.html`（と日付版） | **禁止** | `src/generators/ranking_template.py`（`build-ranking-preview.yml` が 08:30 JST） |
| `presentations/day_slides_list.html` | **禁止** | `script/build_day_slides_list.py` |
| `index.html` の `<style>`・スクリプト本体、`presentations/day_slides_index.html`、`about.html`、`api_docs.html`、`llms.txt` | 可（手書き） | — （`fallback` マーカー内は生成器が所有） |

---

## W1. 「今日」と言い張る表示をやめる（P0）

**現象（本番 2026-10-07 実測）**: 最新スライドは 10/05（2日前）で、ヒーローは「（2日前）」と出す一方、直下の「今日の要点」は **10/03 号の内容**を 10/05 号へのリンクつきで「今日」と表示する。ランキング見出し「今日のスコア上位 3 本」・カード「本日のスライド」・`<title>` と `og:title`「今日のAIスライド」も日付に依存せず固定。

**原因（検証済み）**:
- `index.html:1269-1278` の sitrep 文言は静的。`scripts/update_home_fallback.py:234` `refresh_sitrep()` は href しか更新せず、文言は `--sitrep-update` 等を渡した時だけ更新される。`scripts/check_site_freshness.py` は sitrep を検査しない。
- 「本日のスライド」は `scripts/build-homepage-latest.js:201`（と `news/latest.json` の `highlight.category`）、`index.html` の JS（`todaySlideItem` 付近 2146-2150）に固定。
- `<title>`・`og:title`・`twitter:title` は静的で、どの生成器も更新しない。
- `build-homepage-latest.js` は毎日 `index.html` を書き換えるので、`index.html` だけ手で直しても翌日戻る。

**要求**:
1. sitrep の3行は、リンク先と同じスライドを根拠にするか、リンク先スライドの日付を明示する。`#sitrepLink` に `data-slide-date="YYYY-MM-DD"` を持たせ、`finalize_day_slide.py` → `update_home_fallback.py` がスライドから導出して更新する（文言の更新を CLI 引数の渡し忘れに依存させない）。導出できない時は「MM/DD の要点」にして古い文言を「今日」と呼ばない。`aria-label` も同じ内容に追従させる。
2. 「今日」「本日」は、そのスライド日付が **JST の今日と一致する時だけ**使う。一致しない時は「最新」「MM/DD」に切り替える。対象は `.sitrep` の見出し、ランキング `h2` とその注記、スライド由来カードのタグ。切り替えは生成器（Node 側）と `index.html` の JS の両方で同じ規則にする。
3. `<title>` / `og:title` / `twitter:title` は日付に依存しない名称（例「毎日のAIスライド｜AI Intelligence Hub」）に固定する。`#heroIdentity` の文言は変えない。
4. `scripts/check_site_freshness.py` に検査を足す（既存の検査・契約は消さない）: sitrep の `data-slide-date` と `href` の日付の一致、スライド日付≠JST今日の時に sitrep・ランキング見出し・`<title>` に「今日」「本日」を含まないこと。違反は非ゼロ終了。

**受け入れ条件**（現状の本番は 1〜3 すべて不合格）:
- Playwright で `/`（origin/main の `index.html` を静的配信したもの）を開き、`#sitrepLink.dataset.slideDate` が存在して `href` の `day_slide_YYYY_MM_DD` と一致する。
- JST 今日と異なる日付の fixture（`latest.json` を route で固定）で、`.sitrep` 見出し・`#ranking h2`・`#ranking .section-note` に「今日」「本日」が出ない。同日の fixture では出てよい。
- `curl` 相当で取得した HTML の `<title>` と `og:title` に「今日」が無い。
- `scripts/check_site_freshness.py` が、`data-slide-date` と `href` を食い違わせたテスト入力で非ゼロ終了し、正しい入力で 0。pytest を追加（`tests/test_build_homepage_latest.py` の既存テストを壊さない。`generated_at` の扱いは第5弾の領分なので変更しない）。

---

## W2. LLM 失敗時のフォールバック出力を公開しない・検知する（P0）

**現象**: 本番の `presentations/auto_daily_report.html` は 10/03〜10/07 の5日分すべてが英語の原題・要約＝タイトルの複写・途中切れで、「重要記事 0」「重要度の高いトピック0件」を表示している。
**原因（検証済み）**: cloud run が LLM 不通（`gh run 37551440384` のログ: NVIDIA が `meta/llama-3.3-70b-instruct` を EOL として HTTP 410）でも `using deterministic heuristic fallback` のまま **success** で公開し、同日 08:28 JST に local override が書いた正常版を、cron 遅延で 09:20 JST に起動した cloud 版が上書きしている。`scripts/publish_daily_report.py:198-221` の `protected_paths` は `daily-news/*` だけで、`presentations/auto_daily_report.*`・`daily_reports/auto_daily_report_YYYY_MM_DD.html`・`public-pages/api/auto_daily_report/latest.json` は保護外。CI は日付の鮮度しか見ないので内容の劣化を検知できない。ヒューリスティックのスコアは上限 75 程度（`src/auto_collect/processor.py:257-295`）で、`>=80` の「重要」に構造的に届かず常に 0 件になる（`html_report_renderer.py:232`）。

**要求**:
1. **モデル名は推測で書かない。** `src/auto_collect/llm_provider.py:128` の既定値を、環境変数（既存の `NVIDIA_MODEL`）が未設定なら「設定が必要」と明確に失敗する形にするか、既存の既定値を残したまま 410 を検知して失敗理由を出す形にする。新しいモデル名と GitHub の variable/secret の設定は**ユーザー判断**として完了報告に書く（`.github/workflows/auto-daily-report-cloud-fallback.yml` には `NVIDIA_MODEL: ${{ vars.NVIDIA_MODEL }}` の参照を足すところまで。値は設定しない）。
2. LLM が使えずヒューリスティックに落ちた出力を、同日の LLM 処理済みレポートの上に**公開しない**。`publish_daily_report.py` の保護対象を `auto_daily_report` 系3パスにも広げ、`src/auto_collect/publication_priority.py` の既存契約（`tests/test_publish_daily_report.py`、`tests/test_daily_override_automation.py`）に合わせる。フォールバック版しか無い日は、`<meta name="report:fallback" content="1">` とページ上部の明示（「要約を生成できなかったため原題を表示しています」程度）を付けて公開してよい。
3. フォールバック時は「重要記事 0 件」「重要度の高いトピック0件」を出さない（算出不能と 0 件を区別する）。切り詰める時は文末か「…」で終える。
4. workflow は、フォールバックが発生した run を warning 以上にして残す（success のまま黙らせない）。`.github/workflows/*.yml` を編集したら push 前提の検査として**重複キーが無いこと**を確認する（PyYAML は重複キーを黙認し GitHub は拒否する。`python -c` でキー重複を検出するスクリプトを `tmp/ux6-verify/` に作って実行）。
5. `scripts/check_site_freshness.py`（または新規 `scripts/check_report_quality.py`）に、本番 `auto_daily_report.html` の `.row-title` の日本語（ひらがな・カタカナ・漢字）含有率 ≥ 80% の契約を足す。

**受け入れ条件**:
- `publish_daily_report.py` に「フォールバック版」を渡すユニットテストで、同日の LLM 処理済み `auto_daily_report.html` が**不変**であること（fixture を使う。実 LLM は呼ばない）。
- フォールバック版を単独でレンダリングした出力に「0件」が出ず、`report:fallback` メタと上部の注記がある。
- 品質チェックが現状の本番 HTML で非ゼロ終了（`.row-title` 日本語率 0/15、`.row-tldr` と `.row-title` の完全一致 11 行）し、日本語要約済みの fixture で 0。
- 既存の `pytest tests/test_publish_daily_report.py tests/test_daily_override_automation.py` が通る。

---

## W3. 検索索引の自動再生成と、API 案内の URL（P0 / P1）

**現象**: ニュースアーカイブ検索が古い索引を読み、直近 45 日のニュースと 43 本のスライドが検索できない（索引の最大日付 2026-08-23 / スライド 388 件 vs 実在 431 件）。画面は「毎朝07:00に更新」と書くが偽。`presentations/api_docs.html` と `llms.txt` は `/news/YYYY-MM-DD.json` を案内するが、2026-06-14 以降の日付は 404（実データは `/public-pages/news/`）。
**原因（検証済み）**: `scripts/build_search_index.py` を呼ぶ workflow・スクリプトがどこにも無い（`finalize_day_slide.py` も呼ばない）。`presentations/news_archive.html:126` の「07:00」は実際の cron（cloud 06:00 / local override 08:00）とも不一致。

**要求**:
1. 索引を毎日自動再生成する: `.github/workflows/daily-archive.yml`（`git add public-pages/news/*.json` が既に `search_index.json` を拾う）に `build_search_index.py` の実行ステップを足し、`generate-daily-news-json.yml` の `git add` 対象にも `search_index.json` を足す。スライド公開時は `scripts/finalize_day_slide.py` の最後にも冪等な再生成を足す。
2. 索引の最終生成日時を画面（`news_archive.html` の説明文付近）に出す。`news_archive.html:126` の「毎朝07:00」は実在する運用（「毎日更新」）に合わせる。`tests/test_news_archive_features.py` は features-grid 内の「07:00」だけを禁止しているので、その外側であることを保つ。
3. `api_docs.html:176-177` と `llms.txt` の日別 JSON URL を実在する形に直し、公開されている JSON（スライドの `list.json` / `meta_index.json`、`daily-news.json`、`searchable.json`、索引の実フィールド）を載せる。
4. 再発防止: `api_docs.html` と `llms.txt` に載った `https://visionhub.jp/...` を全抽出し、`YYYY-MM-DD` は直近 7 日で置換して HTTP 200 を確かめる `scripts/check_doc_urls.py` を追加する（ローカル完結。ネットワーク検査は `--live` 指定時のみ）。`freshness-guard.yml` への組み込みは `--live` で行う。

**受け入れ条件**:
- `search_index.json` を生成し直して、`type=slide` の日付集合が `presentations/day_slides/meta_index.json` の issues の日付集合と一致し（現状 388 vs 431）、`type!=slide` の最大日付が `archive_index.json` の最大日付 −1 日以内（現状 2026-08-23）。
- Playwright で `news_archive.html` の「Copilot」検索結果に `2026-10-05` のスライドが含まれ、状態文字列の「うちスライドN件」が上の件数と一致する。
- `check_doc_urls.py --live` が、現状の本番では `YYYY-MM-DD` 置換の URL で非ゼロ、修正後は 0。
- `tests/test_build_search_index.py`、`tests/test_news_archive_features.py` が通る。workflow 変更後に重複キーが無い。

---

## W4. モバイルでナビに辿れない・ヘッダーが崩れる（P1）

**現象**:
- **ntt-theme 系ページ**（`news_archive`, `api_docs`, `json_archive_viewer`, `ai_coding_agents_guide`, `ai_external_resources`, `ai_governance_guide`, `hermes_agent_guide`, `prompt_engineering_guide`, `research_resources`, `recommended_tools/index.html`）と **`day_slides_list`**、**ランキング**は、880px 以下でナビが全部消え、ドロワーも無い。
- **トップ**はスクロールするとヘッダーが画面から消え、モバイルのメニューボタンに戻れない（`html` と `body` の `overflow-x:hidden` が sticky を殺す。`index.html:99,108`）。
- **daily-news / auto_daily_report** は 375px でロゴ・日付・ナビがヘッダー外にはみ出し、本文や絞り込みバーに重なる。
- ドロワーを開いてもフォーカスが背面へ抜け、Esc で閉じない／フォーカスが戻らない（トップ・`day_slides_index`・`auto_daily_report`）。

**要求（修正先は上の表に従う）**:
1. 共有ドロワーを作る: `assets/ntt-theme.css` に開閉スタイルを、共通 JS を `assets/js/` に置き、ntt-theme 系の静的ページ全部と、生成器側（`script/build_day_slides_list.py`、`src/generators/ranking_template.py`）に同じマークアップを入れる。メニューは「ホーム・ニュース・スライド一覧・ランキング・比較・About」の6項目で、`button[aria-expanded][aria-controls]`、各リンクの高さ 44px 以上。ヘッダー内でブランド文字を隠す場合もロゴがホームへのリンクだと分かるようにする（`aria-label`）。
2. トップ: `overflow-x:hidden` を `overflow-x:clip`（または `body` のみ）に置き換えて、`header.site-header` が sticky で残るようにする。`body.nav-open{overflow:hidden}` は維持する。変更は `index.html` の `<style>` のみ（fallback マーカー内には触れない）。
3. daily-news / auto_daily_report: 375px で `.bar-logo`/`.bar-date` が1行に収まり、ヘッダー高さ内に全要素が入る（日付と副題は小画面で省略してよい）。`.filter-bar` の sticky と合わせた固定 UI の高さを viewport 高の15%以下にする（現状 210px）。**`daily-news/*.html` は直接編集しない**。`src/auto_collect/daily_news_template.html`（`.bar` 58-76、`.filter-bar` 140-146、モバイル `@media` 270-282）と `report_template.html` を直す。
4. ドロワーの操作性: 開いたら最初のリンクかドロワーにフォーカスを移し、Tab はドロワー内（トグル含む）だけを循環し、背面（`main`）は `inert`。Esc または項目選択で閉じてトグルにフォーカスを戻す。`aria-expanded` を状態に合わせる。トップ（`index.html` の `setOpen` ≒2841）、`presentations/day_slides_index.html`（:600-612、スクリプト ≒1348-1372）、`report_template.html:772-785,911-921`。
5. 共通の落とし穴: `backdrop-filter` を持つヘッダー内に `position:fixed` のドロワーを置くと containing block が変わって 48px に潰れる（既知）。モバイル時はヘッダーの `backdrop-filter` を無効化するか、ドロワーをヘッダーの外に置く。

**受け入れ条件**（Playwright。375x812 と 768x1024。現状はいずれも不合格）:
- `news_archive`, `api_docs`, `json_archive_viewer`, `ai_coding_agents_guide`, `recommended_tools`, `day_slides_list`, `ai_ranking_report_latest` のそれぞれで、`button[aria-expanded][aria-controls]` をクリックすると、可視の `header a[href]` に `/`・`/daily-news/`・`/presentations/day_slides_index.html`・`/presentations/ai_ranking_report_latest.html`・`/about.html` が含まれ、各高さ ≥ 44px。
- `/`: 375x812 と 1440x900 で `scrollTo(0,1500)` + 800ms 待機後に `header.site-header.getBoundingClientRect().top === 0` かつ `scrollWidth <= innerWidth`。
- `/daily-news/` と `/presentations/auto_daily_report.html`（375x812 と 390x844。生成器のテンプレから生成した HTML を静的配信して検査してよい）: `header.bar` の全直下の子で `rect.bottom <= header.bottom+1`、`rect.right <= innerWidth`、`header.scrollHeight <= header.clientHeight+1`。`scrollY=3000` で header と `.filter-bar` の最大 bottom ≤ 122px。`.bar-logo.getClientRects().length===1` は合否判定に使わない（flex 子要素ではあふれても 1 を返す）。
- ドロワー（トップ 375 / 1100、`day_slides_index` 375、`auto_daily_report` 375）: 開いて Tab を 15 回押しても `document.activeElement` が `#globalNav` かトグルの内側に留まり、Esc で `aria-expanded==='false'` かつフォーカスがトグル。
- 既存の `scripts/check_mobile_page_height.py` と `tests/test_homepage_week_titles.py` が通る（高さ・週カードの契約を壊さない）。

---

## W5. 前後のスライドへ移動できない日をなくす（P1）

**現象**: 10/03 のスライドは「翌日」が「一覧へ」のまま、10/04 には「翌日」が無い。ナビの書式も日ごとにバラバラ（10/04・10/05 は手書きの `.bottom-nav` が残っている）。
**原因（検証済み）**: `scripts/inject_slide_nav.py` は全スライドを走査して前後を毎回再計算する冪等処理で、生成器は正しい。10/03〜10/05 の出荷で `scripts/finalize_day_slide.py`（ナビ注入を含む）が実行されていない（該当スライドに `slide-nav` ブロックが無いことで確認済み）。さらに `inject_slide_nav.py` は `.bottom-nav` の存在を見ずに `</body>` 直前へ追加するので、手書きナビが残る日にそのまま実行すると二重になる。

**要求**:
1. `inject_slide_nav.py` が、既存の手書き `.bottom-nav`（同じ役割のナビ）を検出して置換する（二重にならない）。冪等であること。
2. 冪等なので承認なしで、10/03・10/04・10/05 を含む全スライドに対して再実行する（変更ファイルは作業ツリーに残す）。
3. `scripts/check_site_freshness.py` に「直近 14 日のスライドで、より新しい日付のスライドが存在するのに翌日リンクが無い／末尾リンクが『一覧へ』のまま」「ナビ領域が1ページに複数ある」を検知する検査を足す。違反は非ゼロ終了。
4. `.claude/skills/daily-ai-slide-generator-skill/SKILL.md` は、ローカル main に未コミットの編集があり衝突するので触らない。手順の追記が必要なら完了報告に「提案」として書く。

**受け入れ条件**:
- 直近 14 日の `presentations/day_slides/day_slide_2026_*.html` について、より新しい日付のファイルが存在する全ページが次の存在日付への href を含み、末尾リンクが「一覧へ」ではなく、ナビ領域が1ページ1個。python で検査して exit 0（現状は 10/03 と 10/04 で不合格）。
- `python scripts/inject_slide_nav.py` を2回続けて実行して、2回目の変更ファイル数が 0。
- `tests/test_inject_slide_nav.py` が通る。モバイル 375px でナビが横にはみ出さない。

---

## 全体の検証（最後に必ず実行して結果を貼る）

1. `pytest`（`tests/` 全体。失敗が本弾と無関係なら、そのテスト名と理由を完了報告に分けて書く）
2. `python scripts/check_site_freshness.py`（追加した検査を含めて、ローカル完結モードで）
3. W1〜W5 の Playwright 検証スクリプトを `tmp\ux6-verify\` に置いて実行し、ログとスクショ（375x812 / 1440x900）を保存
4. `git status --short` と `git diff --stat`（変更ファイル一覧）。`.github/workflows/*.yml` の重複キー検査の結果
5. 全 HTML・Python・JS が UTF-8（BOM なし）で、日本語が文字化けしていない（`script/fix_day_slides_mojibake.py` を使う必要が出たら報告）

## 完了報告の書式

```
## 結果
| ID | 判定（✅/⚠️/❌） | 検証コマンドと結果（1行） | 変更ファイル |
## ユーザー判断が必要なもの（W2 のモデル名、vars 設定など）
## git add -f が必要な新規ファイル
## 本弾と無関係な既存の失敗・behind/dirty
## 未解決・次弾候補
```
