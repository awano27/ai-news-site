# 検証記録
確認日: 2026-09-05 Asia/Tokyo

## 基線
- PASS: `python -m pytest tests/test_auto_collect_main.py tests/test_html_report_parser.py tests/test_publish_daily_report.py tests/test_build_homepage_latest.py -q` → 18 passed in 18.41s (変更前)。
- PASS: CNAME=visionhub.jp、origin=https://github.com/awano27/ai-news-site.git。HEAD=2b86bf95 (2026-08-12)。
- 公開Daily Newsは2026-09-05 08:36 JST。ローカル最新版と日付が異なるため公開版の全文による上書きは行わない。
- ブラウザー起動: `python -m http.server 8765 --bind 127.0.0.1` と `npx.cmd --yes --package @playwright/cli playwright-cli -s=content-integrity open http://127.0.0.1:8765/presentations/ai_coding_agents_guide.html`。基線のconsole errorは `/favicon.ico` 404のみ。
- `package.json`にbuild/test scriptなし。Pages実処理はnode scripts/build-homepage-latest.jsとpython scripts/build_sitemap.pyの後にstatic upload。deploy処理は実行禁止。
- 個人作業のルートPLAN.md等の変更はbaseline-dirty-sha256.jsonで照合する。

- PASS: `python scripts/build_sitemap.py --dry-run` → 652 URLs; 標準XML parserで読取成功。既存sitemap.xmlへの書込みなし。
- 調査: scripts/generate-daily-news-json.jsはpublic-pages/newsの日次JSON→presentations/api/daily-news{,-latest}.json。RSS入力collectorは存在するが、今回確認したauto_collect経路にRSS出力generatorは見つからない。

## 最終結果
最終コマンドと状態はREPORT.md第4節。final-tests.txt: 41 passed in 21.42s。preview-generation.txt: 新規6出力を二度生成PASS。final-guide-check.txt: PASS。
PlaywrightによるPC/390pxガイド・Daily News・Top15訂正文・関連CLI注記を確認。ガイドはscrollWidth=390。Top15は過去7日HTML欠落404、ガイド基線favicon 404を記録し全resource成功とはしない。画面証跡はoutput/playwright/content-integrity/。
既存dirty SHA比較: .gitignore以外すべて一致。.gitignoreは従来allowlistを保持して今回分を追記。全本番操作NOT_RUN。
