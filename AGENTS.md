# AGENTS.md

ai-news-site (visionhub.jp) で作業するエージェント向けの指示。サイト全体の構成と規約は `CLAUDE.md` を読むこと。

## 日次スライドを公開するときは仕上げ処理が必須

`presentations/day_slides/day_slide_YYYY_MM_DD.html` を追加・差し替えたら、コミット前に必ず次を実行する。

```bash
python scripts/finalize_day_slide.py MMDD
```

例: 11月20日のスライドなら `python scripts/finalize_day_slide.py 1120`。複数日を出すときは古い日付から順に、1日ずつ実行する。

このスクリプトがやること:

- スライド本体に og:image・canonical・NewsArticle JSON-LD（datePublished）・計測タグ（`/assets/js/analytics.js`）を入れる
- `presentations/day_slides/meta_index.json`・`list.json`・`presentations/day_slides_list.html` に追加する
- 全スライドの前後ナビ、トップページの fallback、`news/latest.json`、`feed.xml`、`sitemap.xml`、検索インデックスを更新する
- 最後に SEO と計測カバレッジを検査する

冪等でローカル完結なので、何度実行してもよい。承認は要らない。

### コミットに含めるもの

仕上げ処理が書き換えたファイルは**すべて**スライドと同じコミット（または直後のコミット）に含める。スライド本体と `presentations/day_slides_index.html` だけを push すると、OGP・計測タグ・canonical のないページが本番に出て、feed が止まり、Freshness Guard が落ちる（2026-11-20 に 11/19・11/20 で発生）。

手で編集するのは次の3つだけ。それ以外は仕上げ処理の出力をそのまま使う。

- スライド本体
- `presentations/day_slides_index.html`
- `presentations/day_slides/images/MMDD/cover.jpg`

### push 前の確認

出力の最終行が次の形で、終了コードが 0 であること。

```
[9/9] check_slide_seo+check_analytics_coverage: seo=0 coverage=0
```

続けて次の2つが通ること。

```bash
python scripts/check_site_freshness.py
python scripts/check_feed_freshness.py
```

`check_site_freshness.py` は `RESULT: PASS`、`check_feed_freshness.py` は `OK` を出す。どれかが落ちたら push しない。

### 環境の注意

- Windows では `PYTHONUTF8=1` を付けて実行する
- 作業は `origin/main` から切った worktree で行う。`C:\develop\ai-news-site` のローカル main は古い
- `scripts/` `script/` `.github/` `tests/` の新規ファイルは `.gitignore` に弾かれるので `git add -f` で追加する
- 完了条件は `origin/main` への到達と、Pages デプロイ後の本番確認まで
