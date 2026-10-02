# 2026-10-03 コードベース改善結果

第1・2段階（C1〜C11）のローカル修正・統合と関連回帰検証を実施した。指定・関連20モジュールは **173 passed**。全テストは **352 passed / 45 failed** で、全件合格ではない。画面確認は機能・安全性に問題を検出しなかったが、390pxで一部の横方向はみ出しを確認したため **PARTIAL**。現在のローカル成果物は鮮度とGA4設定の検査に失敗し、公開準備は **BLOCKED**。実CI・デプロイ・公開後確認は **NOT_RUN**。

第3段階は [UX1〜UX6の具体案](UX-PROPOSALS.md) を作成した。選択は未実施であり、画面構成・主要CTAを変更する案は実装していない。効果は未測定。

## 対象と既存作業の保護

- リポジトリ: `C:\develop\ai-news-site`、ブランチ `main`。
- 開始・終了HEAD: `02425136b114a46ff5e805ab1f216bf60536ed2a`（変更なし）。
- 対象リポジトリでstage・commit・push・merge・deployなし。検証用Git操作は一時リポジトリ内だけ。
- 既存dirtyの `CLAUDE.md` と `.claude/skills/daily-ai-slide-generator-skill/SKILL.md` は開始時SHA-256と一致。
- 保存済み `daily-news/index.html` と `daily-news/news_detail.html` はHEADのバイト列と一致。古い入力による再生成を行っていない。
- 変更は追跡済み49ファイル、追加・配布予定のコード/設定19ファイルと専用作業記録。詳細は [CHANGE-FILES.md](CHANGE-FILES.md)。追加予定には以前から存在したignore済み依存も含む。まだコミットされていないため、実際の配布済み状態ではない。
- 既存untracked作業を削除・復元・stageしていない。全既存untrackedの内容ハッシュを取得したわけではないため、その全バイト列の同一性を証明したとはしない。
- [PLAN.md](PLAN.md)、[開始状態](baseline-status.txt)、[保護検査](preservation.json)。

## C1〜C11の結果

| 項目 | 現行指摘の成立と実修正 | ローカル検証 | 残る制約 |
|---|---|---|---|
| C1 HTML安全性 | 成立。描画後のentity decodeでescaped入力が実タグへ戻ることをHEADで再現。入力を描画前に正規化し、Jinjaのescapingを保持。チャートをネイティブ配列とtojsonへ変更。月次テンプレートのitems sliceも修正 | 悪意あるHTML、onerror、引用符、`</script>`、二重entity、日本語、固定時刻で2回同一生成。ランキング/月次fixtureとブラウザで注入なし | 保存済み全ページの再生成は未実施。旧SlideGeneratorの日次経路は既存のgenerated_at未定義を探索時に確認し、今回のランキング/月次合格とは区別 |
| C2 clean checkout依存 | 成立。workflowが参照するignore済み依存を限定的に非ignore化。config/ingest/validate、collectors、detail generator、sources、requirementsを追加予定として明示 | 追跡済み＋明示した追加予定ファイルから一時clean treeを作成し、entrypoint import、fixture build_news、生成/計測注入を検証 | 実コミット後checkout・CIはNOT_RUN。秘密を配布対象へ追加していない |
| C3 生成結果 | 成立。必須処理の失敗を成功へ変えない。日付/run_id/phase/全失敗数/必須失敗数/成果物のfreshness・サイズ・mtime・hash・内容検証をrun manifestに記録。生成と公開で同一run_id | アーカイブsubprocess非0、生成例外、同日stale、空HTML、壊れたJSON、誤日付、run_id不一致、改ざんを拒否。任意OG失敗と必須失敗を分離 | 実収集・有料APIはNOT_RUN。出力契約を変更する際はvalidatorも更新が必要 |
| C4 公開連携 | 成立。自動pushを行う8経路から、実際のpush成功SHAを再利用workflowへ渡し、検証→Pagesを接続。checkout/検証/パッケージ/deploy revisionを同じSHAへ固定 | workflow構造・SHA handoffのfixture、YAML parse、actionlint。Pagesパッケージで生成・計測注入後の再検査を行う設計 | 実Actions、repository権限、Pages設定、公開後SHAはNOT_RUN。Vercel経路はUnknown |
| C5 日時契約 | 成立。HNの今日・昨日のJST窓をUTC epochへ変換。公開/収集/対象日時をprocessor・text・JSON・HTMLへ保持。不明を新着と推測しない | 今日/昨日/古い/翌日未来/不正/不明/UTC-JST境界fixture。昨日許容を維持 | 同じJST日の後の時刻は従来の暦日選別として許容し、時計時刻基準の排除は導入していない。実収集はNOT_RUN |
| C6 Gitと途中失敗 | 成立。書き込み前に既存stageを拒否。Gitモードでは対象dirtyも拒否。直接公開とtransaction対象を分離し、home/feed/旧slide/meta_indexを含め復元。対象repoのfinalizerを別processで呼ぶ | 一時Git repoでstaged保護、dirty home/旧slide保護、途中失敗復元、新規出力削除、無関係dirty非stage、対象helper実行 | 実repoの公開Git操作はNOT_RUN。書き込み成功後の公開許可をこの検証で得たことにはしない |
| C7 根拠ラベル | 成立。top/nested labelを共通検証し、情報分類と照合状態を分け、HTML/JSON/textへ伝搬。不正/不足は不明・照合未確認 | 根拠なしFact、不正label、通常記事の派生物、移行済み記事のfingerprint回帰が成功 | URLやモデル分類だけで照合済みとしない。fingerprintの自動更新なし |
| C8 鮮度 | 成立。コメントだけで成功する旧挙動を再現。HTMLParserでfeat-cardとslide-cardを別々に検査し、実際のリンク先ファイルとXML sitemapを確認 | 両カードPASS、片方/コメント/旧リンク/不存在/script内文字列/sitemapコメントFAIL | 現行成果物は09/12ファイル欠落、09/10・11 index欠落でFAIL。内容は正しい対象日入力がないため未修復 |
| C9 自己修復 | 成立。Pages build APIと失敗無視を廃止し、actions:writeでPages workflowをdispatch。応答不良、要求受理、対象run成功、回復を別状態とする | HTTP異常、dispatch拒否、受理だけ、run失敗、回復成功をCLI終了コードも含めmock検証 | 実dispatch・公開回復はNOT_RUN。repository設定変更なし |
| C10 計測 | 成立。公開HTMLの共通inventoryにDaily News/設計/比較/スライドを含め、除外理由を定義。コメントをタグと数えない。生成元へloaderを保持し、注入も同じ対象定義を使用 | fixture再生成でタグ維持。無効ID拒否、localhost/DNT維持、mock上のslide_view/scroll/CTA/outboundを確認 | 実ID未設定でconfig FAIL。保存済み5ページにタグ不足。実GA4到達NOT_RUN。実IDを推測せず本番イベント送信なし |
| C11 推薦の意味 | 成立。既存の編集推薦を維持して「今日の注目3本」に統一。編集推薦へ架空の5点を表示しない。リンクは「30日間のTOP30」。静的buildとruntimeの選定を一致 | JS有効/無効、再生成2回の同一性、名称・選定・スコア表示のfixture/ブラウザ確認 | 保存されたニュースの鮮度そのものをこの表示修正で保証しない |

詳細: [C2/C4/C9](C2-C4-C9.md)、[C3/C6](C3-C6.md)、[C5/C7とError500](C5-C7.md)、[修正前再現](main-baseline.json)。各担当の途中件数より、以下の主担当最終実行結果を採用する。

## 最終検証

隔離した一時venvを使用した。対象プロジェクトの依存設定・global環境を置き換えていない。

```powershell
$py = 'C:\Users\awano\AppData\Local\Temp\visionhub-1003-venv\Scripts\python.exe'
& $py -m pytest tests/test_claim_evidence.py tests/test_static_claim_evidence.py tests/test_claim_evidence_preflight.py tests/test_content_integrity.py tests/test_claim_evidence_news.py tests/test_html_report_parser.py tests/test_auto_collect_main.py tests/test_build_homepage_latest.py tests/test_homepage_claim_evidence.py tests/test_evidence_article.py tests/test_guide_policy_evidence.py tests/test_slide_claim_evidence.py tests/test_render_safety.py tests/test_site_freshness.py tests/test_analytics_contract.py tests/test_article_contract.py tests/test_distribution_workflows.py tests/test_publish_daily_report.py tests/test_daily_override_automation.py tests/test_publish_image2_day_slide.py -q
& $py -m pytest tests -q
& $py docs/plans/2026-10-03-codebase-improvement/compare_baseline.py
& $py docs/plans/2026-10-03-codebase-improvement/browser_check.py
& $py docs/plans/2026-10-03-codebase-improvement/final_checks.py
& $py scripts/check_site_freshness.py --json
& 'C:\Users\awano\AppData\Local\Temp\visionhub-1003-tools\actionlint.exe' -shellcheck= -pyflakes=
git diff --check
```

| 対象 | 結果と証拠 |
|---|---|
| 指定12＋関連8モジュール | **173 passed / 60.56s**。[regression-final.log](regression-final.log) |
| tests全件 | **352 passed / 45 failed / 103.33s**。[regression-all.log](regression-all.log) |
| 失敗のHEAD比較 | 同じ2モジュールを隔離HEADコピーで実行し46 failed / 6 passed。現在の失敗test IDはすべてHEADでも失敗。HEADで失敗したslide_card_desc_filledは現在成功。[supplemental-head-baseline.log](supplemental-head-baseline.log) |
| workflow | YAML14件parse PASS。actionlint v1.7.12 PASS、shellcheck/pyflakesとの連携なし。[actionlint.log](actionlint.log)は成功時空 |
| 技術比較/根拠 | coding-guide PASS、claim-evidence PASS（登録済み静的4ページと固定Crusoe記事のみ、原資料fetchなし）。[static-checks.json](static-checks.json) |
| diff/既存dirty | diff --check PASS、既存dirty hash一致、stage空、HEAD不変。[preservation.json](preservation.json) |
| 現行HTML/設定 | freshness FAIL、GA4 config FAIL、生HTML coverage916/921で5不足。失敗をskip/無条件成功へ変更していない |
| CI/デプロイ/公開後 | **NOT_RUN**。ローカルのworkflow検証は実環境証拠ではない |

全件失敗は `tests/test_day_slides_latest_contract.py` と `tests/test_ux_improvements.py`。前者はHEADにもないextract_archive_slides/sync_day_slides_index/check_index_latest_contract等の追加API、後者は未実装のrankingTitle等のID・blurb・1024pxナビ等を前提とする。両テストは既存のignore対象で、今回変更・削除・skipしていない。全件合格やこれら機能の実装完了は主張しない。

## 実ブラウザと生成物

既存ChromiumをPlaywrightから実行し、一時サイトで390px/1440pxのホーム、Daily News、設計記事、技術比較、既存day slide、悪意ある入力を含むランキングを確認した。ホームはJS無効も確認し、計14条件。外部通信とChart/mermaidをmockし、本番GA4イベントは送信していない。

- page error、console error、失敗HTTP応答は0。悪意あるscript/onerrorは実行されなかった。
- ナビ、Daily News検索（2件→1件→0件表示）、推薦ラベルとJS無効の静的表示を確認。
- 1440pxは横はみ出しなし。390pxではDaily Newsが402px、既存slideが403px、長い悪意ある入力のランキングfixtureが591px。このためレイアウト判定はPARTIAL。外部Chart実描画や外部fontの見た目は未検証。
- 生成元の修正は一時fixture生成で検証。保存済み当日コンテンツを古い入力で更新していない。

実行コード: [browser_check.py](browser_check.py)、[結果JSON](browser/results.json)、[browser-final.log](browser-final.log)。画像: [390pxホーム](browser/390-0.png)、[390px Daily News](browser/390-1.png)、[1440pxホーム](browser/1440-0.png)、[1440pxランキングfixture](browser/1440-5.png)。

## 公開前の残件

1. 日次コンテンツ: 2026-09-12のslideファイル、09-10/11のindexエントリを正しい対象日入力で復元する必要がある。[current-freshness.json](current-freshness.json)。
2. GA4: 運営者の実measurement IDが必要。`G-REPLACE-ME`を維持し無効設定として検出した。現在のGA4到達はNOT_RUN。
3. 保存済みloader不足: daily-news/index.html、news_detail.html、presentations/ai_news_detail_latest.html、ai_ranking_report_20250901.html、daily_ai_news_report_20250826.html。今回修正した生成元とPages一時artifact注入を利用し、正しい入力から更新する段階が必要。
4. 保存済みGoogle Error500: 29要約中21件。Git履歴で外部daily-ai-newsからのCSV deploy由来を確認。現行外部build.pyの翻訳エラー本文を成功としてキャッシュし得る経路と整合するが、当該外部SHAが手元にないため正確な当時のバックエンドはUnknown。外部repoは読み取りのみ、保存済み記事は未修復。[C5-C7.md](C5-C7.md)。
5. 実Actions/Pagesの権限・検証→公開→公開SHA確認、自己修復後の回復、GA4到達は未実行。push/deploy/dispatchや実イベント送信へ進む場合は、依頼文のローカル作業境界に従い、具体的な対象と操作の承認が必要。今回はその操作を実施していない。
6. 390pxレイアウトと既存全件テストの追加仕様は残件として上記に記録。選択が必要なUX案は [UX-PROPOSALS.md](UX-PROPOSALS.md) に分離。

## Jevとレビュー

Jev: shadowのeffort判断を3回記録し、モデル/effortを変更しなかった。担当最終reviewのテスト範囲に対する低確信は主担当の差分レビュー・最終関連回帰・全件検証・HEAD比較で確認した。最終jev_verifyは、関連173成功/全件45失敗/画面PARTIAL/公開BLOCKEDの4主張をverified（confidence0.94〜1.00）と判定。判断補助であり公開許可や実行証拠として扱っていない。[jev.log](jev.log)、[jev-final.json](jev-final.json)。

再利用workflowのgithub contextは呼出元に対応するため、定期生HTML検査の区別はevent_nameではなくinputs.refの有無を用いる。Pagesパッケージ後のcoverageは常に検査する。[GitHub公式仕様](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations#github-context)。
