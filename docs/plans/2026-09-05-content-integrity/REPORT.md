# VisionHub 技術・数値訂正の実施報告

確認日: 2026-09-05（Asia/Tokyo）。本番未反映。

## 1. 対応結果

比較ガイドと関連Copilot CLIページの承認・隔離の混同、Hooksの唯一性、根拠のない製品順位をローカル修正した。Crusoeは公開記事を原文と照合し、URLに紐づく永続訂正をニュース生成経路へ組み込んだ。41件の関連テストがPASS。固定1記事の新規出力とブラウザー表示を確認した。

ローカルHEADは2026-08-12で、9月5日の完全なDaily News入力は存在しない。今回のニュースHTMLは固定1記事による隔離プレビューであり、公開141件のフィード全体を復元・置換したものではない。最新本番の訂正済み完全版を作成済みとは扱わない。

## 2. 修正一覧・根拠

主張ごとの対象・判定・根拠節は [guide-audit.md](guide-audit.md) と [news-audit.md](news-audit.md) に記録。

|対象|修正前|修正後|判定・根拠|
|---|---|---|---|
|比較ガイドの実行環境・sandbox表・本文|Claude Codeはsandboxなし、完全アクセス、承認で安全確保|Bashと子プロセス、OS、有効化、読書込み・ネットワーク、例外、通常権限との違いを明記|誤り／条件不足。[Sandboxing](https://code.claude.com/docs/en/sandboxing) の各隔離・権限・retry節|
|比較ガイドHooks・差別化|唯一、他製品に存在しない、根拠のない優劣|Claude/Copilotをイベント、実行面、設定範囲、判断能力で説明。Cloud Agent固有制限を明記|誤り／未確認。[Claude Hooks](https://code.claude.com/docs/en/hooks)、[Copilot Hooks](https://docs.github.com/en/copilot/reference/hooks-reference)|
|関連Copilot CLI|--allow-allはsandboxなし|ツール・パス・URLの承認とsandboxを分離|誤り。[Allowing tools](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools)、[CLI overview](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/overview)|
|Crusoe本文と派生情報|概要$30Bに対し本文の企業価値$30億。根拠不明の円換算|企業価値300億米ドル、調達30億米ドル、別件契約130億米ドルを帰属付きで区別。円換算を除去|内部不一致は誤り。原文は報道への帰属として確認。[TechCrunch本文](https://techcrunch.com/2026/09/03/crusoe-reportedly-raises-3b-at-a-30b-valuation/) 第1段落・契約段落|

主担当による追加確認: Claude Hooks公式の設定場所表（個人・プロジェクト・管理・Web）、PreToolUse節、Copilot公式のHooks locations/Cloud agent execution environmentを読み、設定パスと適用範囲を追記した。ガイドの訂正履歴は該当制御仕様だけの確認と明記。表に残っていた「完全自律」「Review→Merge全自動」と未検証の価格階層不存在も中立化した。料金・モデル表全体を最新確認済みとはしていない。

## 3. 原因と再発防止

- ガイド: リポジトリ内ではHTML直接管理。生成元を新設せず、直接修正＋既知誤記・根拠リンク・適用条件の検査を追加。Pages workflowのpackaging前に接続。
- ニュース: processorの要約等→formatter→日次テキスト→Top15 parser/renderer/API、別経路でDaily News HTML/JSON。保存前・再読込時に同じURL訂正を適用する。
- 最初の数値不一致を実証できる地点は公開Daily News本文。9月5日のraw取得結果・LLM応答がないため、その手前の最初の混入地点はUnknown。LLMが原因と断定しない。
- 訂正はtitle/tldr/summary/points/metrics/evidenceまで一貫して置換し、誤数値の残留を防ぐ。訂正注記と記事保留statusをformatter/parserで保持する。
- million/billion/万/億をDecimalで正規化。同指標・通貨・event_dateの構造化矛盾を検査。小数、NaN/Infinity、円と米ドル、モデルの30B、過去比較を回帰検査。
- 未知記事の文章解析は限定的な検出であり、同一企業・時点・出来事をあらゆる文章から確定するものではない。曖昧な指標・過去比較は警告、人の原典確認が必要。明示的な構造化矛盾は過去比較という単語があっても保留する。
- 保留は該当記事のみ。外部取得失敗に連動した全記事停止、外部依存テスト、有料API呼出しは追加していない。

## 4. 検証結果

|状態|コマンド／検証|結果|
|---|---|---|
|PASS|`python -m pytest tests/test_content_integrity.py tests/test_content_integrity_outputs.py tests/test_coding_guide_integrity.py tests/test_html_report_parser.py tests/test_auto_collect_main.py tests/test_publish_daily_report.py tests/test_build_homepage_latest.py -q`|41 passed in 21.42s。ログ: final-tests.txt|
|PASS|`python scripts/check_coding_guide_integrity.py`|既知誤記・必要な直接根拠・条件チェック|
|PASS|`python docs/plans/2026-09-05-content-integrity/regenerate_preview.py`|隔離した新規6出力を二度生成。HTML/JSON/日次テキストに旧数値なし。preview-generation.txt|
|PASS|outputs test内の既存Node generators|formatter→archive抽出→public-pages入力→homepage JSON、daily-news API 2種。Node時計を固定し将来日付で劣化しないfixture|
|PASS|`python scripts/build_sitemap.py --dry-run`|652 URL、XML parse成功。既存sitemapへの書込みなし|
|PASS|対象ファイルに限定した`git diff --check`|今回差分の空白問題なし|
|FAIL→PASS|回帰の修正前後|guide-verification.log、outputs-red.txt、review-red.txt、undated-red.txt、evidence-red.txt。補足欄の旧値残留、明示claimの歴史語による迂回、日時を持たないprocessor入力の誤保留を再現して修正|
|PASS（表示）|Playwright CLI、127.0.0.1:8765|比較表・直接出典・訂正履歴・関連CLI注記、Daily News、展開後Top15。390pxでガイドscrollWidth=390|
|BLOCKED（完全な無エラー画面）|ローカルTop15プレビュー|未取得の過去7日分HTMLへの404が7件。ガイド基線はfavicon.icoの404。訂正表示は確認済みで、全リソース成功とはしない|
|NOT_RUN|外部APIを用いた全収集、9/5全フィードの再生成、GitHub上の新CI、deploy|権限・範囲に従い未実施|

画面証跡: `output/playwright/content-integrity/`。生成プレビュー: `outputs/content-integrity-2026-09-05/fixture-preview/`。どちらも開発用の確認物。全アーカイブを再生成していない。

## 5. 未確認・公開前の残件

- 最新公開版と古いローカルcheckoutの整合を確認し、最新の完全な9/5入力に訂正を適用してから公開を判断する必要がある。この作業では既存dirtyを保つため丸ごとの更新をしていない。
- Crusoeの今回の企業発表、契約締結日、元LLM応答は未確認。報道帰属を維持する。
- ガイドのCodex/Antigravityの未確認仕様と価格・モデル表全体は確認済み扱いにしない。検査は事実全般の保証ではない。
- RSS出力は今回の生成経路で確認できなかった。RSS入力collectorとは区別する。
- 既存の日次HTML時刻処理はホストのローカル時刻依存。UTCホストでのJST表示問題は別の既存課題として記録し、今回の数値訂正で改修していない。
- 全worktreeのdiff checkは既存input/day/0809.txtと0811.txtの空白問題が残る。今回対象の差分はPASS。

## 6. 変更ファイル

本体: `.gitignore`（既存2行を保ち今回allowlistを追記）、`.github/workflows/pages.yml`、`presentations/ai_coding_agents_guide.html`、`presentations/copilot-guide/cli.html`、`scripts/check_coding_guide_integrity.py`、`src/auto_collect/content_integrity.py`、`src/auto_collect/processor.py`、`src/auto_collect/daily_news_page.py`、`src/auto_collect/formatter.py`、`src/auto_collect/html_report_parser.py`、`src/auto_collect/html_report_renderer.py`。

テスト: `tests/test_content_integrity.py`、`tests/test_content_integrity_outputs.py`、`tests/test_coding_guide_integrity.py`。

監査・コマンド結果・PLAN・再生成補助: 本ディレクトリ。新規検査と監査をgit statusで確認できるようallowlistを追加し、stageはしていない。既存dirtyのSHA-256比較は`.gitignore`以外すべて一致。トップindex.html/news/latest.json等の既存作業を保持した。

## 7. 公開状態とレビュー

ローカル修正・検証のみ。本番未反映。commit、push、merge、deployは実施していない。

独立したSol reviewerは、同指標検査の迂回と時刻依存testの修正後、限定範囲で追加blockerなしと判定した。主担当はさらにprocessorの日時なし入力を検査し、記事投稿日を出来事日にしないunknown処理を修正、最終41件を再実行した。

今後の計画運用の提案: 既存PLAN.mdがdirtyの場合は、今回同様に作業別PLANへ分離し、開始時の既存差分と今回差分を別々に保存する。AGENTS.md自体は変更していない。

最終補足: 古い日次ファイルのtop-level impact/actionable/evidence_labelも訂正時に消去・Claimへ変更し、Factラベルへの誤昇格を防ぐテストを追加。evidence-red.txtで修正前FAILを確認後、上記41件を再実行した。
