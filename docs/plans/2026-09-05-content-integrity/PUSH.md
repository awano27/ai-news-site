# Push validation

ユーザーの2026-09-05のpush指示により今回差分のみを専用ブランチへ送信する。

- Base: origin/main c33aafde（元checkoutは1 ahead / 393 behind）。
- Branch: codex/visionhub-content-integrity-20260905
- Worktree: C:/develop/ai-news-site-content-integrity-push
- 既存8ファイルのgit apply --3wayは競合なし。元checkout/既存dirty/ローカル固有コミットは変更・混入なし。
- PASS: 比較ガイドchecker、staged/unstaged diff --check。
- Mixed: python -m pytest tests/test_content_integrity.py tests/test_content_integrity_outputs.py tests/test_coding_guide_integrity.py tests/test_html_report_parser.py tests/test_auto_collect_main.py tests/test_publish_daily_report.py tests/test_build_homepage_latest.py -q → 40 passed, 1 failed in 31.84s。
- 失敗はtests/test_build_homepage_latest.py:43のheroIdentity不在。git show HEADからテスト/HTML/build script/最新slideを一時ディレクトリへ抽出して同じFAILを再現。push-baseline-test.txt参照。無関係の既存問題として変更しない。
- baseline再現の初回はPATH上の別PythonにpytestがなくBLOCKED。実行中のsys.executableを使って上記FAILを再現した。
- 初回REPORT.md/final-tests.txtは旧checkoutでの41 PASSの履歴。最新mainでの結果は本書を参照。
- 開発用の固定1記事preview、個人dirty一覧/hashはcommit対象外。
- 専用ブランチpushのみ。main merge/本番deployは未実施。
