# Daily News 数値整合性監査（Crusoe）

確認日: 2026-09-05（Asia/Tokyo）
対象: `https://visionhub.jp/daily-news/` の 2026-09-05 表示記事「クルーソ、300億ドル評価で30億ドル調達」

## 主張台帳

|掲載箇所|掲載内容|判定|直接の根拠と確認節|対応|
|---|---|---|---|---|
|Daily News 見出し・要約|`$30B` の企業価値、`$3B` の調達額|確認済み（ただし報道帰属）|[TechCrunch: Crusoe reportedly raises $3B at a $30B valuation](https://techcrunch.com/2026/09/03/crusoe-reportedly-raises-3b-at-a-30b-valuation/) の見出しおよび第1段落。TechCrunchは Bloomberg 報道として記載。|訂正後の要約にも「TechCrunchはBloomberg報道として」を残す。|
|Daily News 本文|企業価値が `$30億`、調達額が `$30億ドル`|誤り|同TechCrunchの第1段落は企業価値 `$30 billion`、新ラウンド `$3 billion`。算術上、`$30B = 300億米ドル`、`$3B = 30億米ドル`。|企業価値を約300億米ドル、調達額を約30億米ドルへ訂正。|
|Daily News 本文|Jane Streetとの `$130億` 契約|確認済み（報道帰属）|同TechCrunchの第2段落は、Jane StreetへのGPU・AIインフラ提供の `five-year cloud contract` を `$13 billion` と報道。|契約額を企業価値・調達額とは別の `contract` 指標で記録。|
|契約日|2026-09-03に契約締結|未確認|同記事は `recently signed` とするのみで締結日を記載しない。|`event_date: "unknown"`、`reported_at: "2026-09-03"` と分離。|
|Crusoe自身による公式発表|今回の調達・企業価値・契約の公式確認|未確認|今回確認した根拠はTechCrunch経由のBloomberg報道であり、Crusoeの一次発表ではない。|公式確認済みとは表示しない。|

## 実在する生成経路と不一致地点

`src/auto_collect/main.py` はRSS等を収集し、`LLMProcessor._process_with_llm` のJSON応答に含まれる `summary` / `tldr` をそのまま処理済み記事へ格納する。`src/auto_collect/daily_news_page.py` はその文字列を `daily-news/index.html`、`daily-news/data.json`、日付別HTMLに書き出す。公開本文の不一致は、この未検査の要約文字列がDaily Newsへ渡る経路で再生成され得た。リポジトリには9月5日のローカルDaily Newsアーカイブがなく、実行時の原収集データも残っていないため、最初に数値が食い違った生成段階を「LLM」と断定する証拠はない。

Top 15 は別経路である。`src/auto_collect/html_report_parser.py` が `input/day/MMDD.txt` を読み、`html_report.py` が最新HTML/JSON、公開API、日付別HTMLを生成する。ここにも同じ訂正ガードを適用した。

## 再発防止と限界

`src/auto_collect/content_integrity.py` は、既知のTechCrunch URLへ決定的な訂正データを適用する。企業価値・調達額・契約額を `metric`、`currency`、`event_date`、`reported_at` を持つ構造化主張に分け、million/billion/万/億を百万単位へ正規化する。同一記事内で同じ指標・通貨・出来事の数値が異なれば、その記事だけ `pending_fact_check` として金額を含む要約を保留する。他の記事の生成は継続する。既知訂正はタイトル、要約、箇条書き、数値欄、派生した影響・操作説明を置換し、Daily NewsとTop 15のHTMLには訂正注記を表示する。

数字だけで指標が判別できないケースは自動で事実判定できないため、警告を記録して本文は保留しない。外部サイトへのアクセスや有料APIに依存しない。これは数値の真偽全般を保証する検査ではなく、構造化済みまたは明示的にラベル付けされた同一指標の不一致を防ぐ仕組みである。

## 検証記録

`python -m pytest tests/test_content_integrity.py tests/test_content_integrity_outputs.py tests/test_html_report_parser.py tests/test_auto_collect_main.py -q`
結果: PASS — 21 passed（固定フィクスチャで修正前の `$30B` / `$30億` 同一企業価値がFAILになること、異なる3指標とJPY/USDが非誤検出であること、NaN/Infinity拒否、30Bパラメータ数が金融警告にならないこと、保留記事がformatter/parserを経ても金額を復元しないこと、日次/Top 15の一時出力、二重生成の重複なしを確認）。

`python docs/plans/2026-09-05-content-integrity/regenerate_preview.py`
結果: PASS — 固定したCrusoe 1件だけを隔離出力先で2回生成し、Daily News HTML/JSON/アーカイブ、日次入力、Top 15 HTML/JSONの6出力から誤った `$30億` が消え、`300億米ドル` が残ることを確認。実際の9月5日全件アーカイブの再生成はしていない。

画面ブラウザーでのローカル表示確認: NOT_RUN。公開URL本文のread-only確認は実施済み。ローカル修正・検証のみで、本番デプロイ、commit、pushは未実施。

最終追記: ブラウザー表示確認と派生Node generator検証を主担当が実施。上記NOT_RUN/19件は担当時点の記録で、最終関連suiteは41件PASS（final-tests.txt）。日時なしprocessor入力はevent_date=unknownとし、投稿日を出来事日にしない。旧dayfileのFactラベル・impact/actionableも訂正し報道をClaimとして保持。9/5完全フィード未再生成の制約と画面404はREPORT.md参照。
