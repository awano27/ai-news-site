# 2026-09-05 公開出力の限定訂正

対象URL:

`https://techcrunch.com/2026/09/03/crusoe-reportedly-raises-3b-at-a-30b-valuation`

## 変更対象

- Daily News: `daily-news/data.json`、`daily-news/index.html`、`daily-news/archive/2026-09-05.html`
- 日次入力と Top 15: `input/day/0905.txt`、`public-pages/api/auto_daily_report/latest.json`、`presentations/auto_daily_report.json`、`presentations/auto_daily_report.html`、`presentations/daily_reports/auto_daily_report_2026_09_05.html`、`presentations/daily_reports/searchable.json`
- ホーム派生: `index.html`、`news/latest.json`

各出力の当該1記事だけを、企業価値約300億米ドル、調達額約30億米ドル、5年契約約130億米ドルへ訂正した。TechCrunchのBloomberg報道としての帰属、`Claim`ラベル、訂正注記を日次カードと Top 15 に表示する。`input/day/0905.txt` は parser が認識する `🛠 訂正:` 形式を使う。

`public-pages/news/2026-09-05.json` と `public-pages/news/daily_latest.json` は対象URLへの関連リンクだけを含み、当該記事のタイトル・要約・数値を持たないため変更していない。

## 検証

- `daily-news/data.json` は `items=141`、`total=141`、日付・`generated_iso`・集計メタデータを保持した。
- URL一致するレコードを除いた JSON は基準HEADと意味的に一致した。
- カード、Top 15 行、日次テキスト節、ホームカードを除いたHTML/テキストは基準HEADとバイト一致した。
- 対象区画の古い企業価値・円換算・`Fact`ラベルは残っていないことを確認した。
- `git diff --check` は成功した。

全アーカイブの再生成、外部アクセス、API呼出し、日時や記事件数の更新は行っていない。
