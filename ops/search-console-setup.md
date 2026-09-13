# Search Console / Bing / IndexNow セットアップ（visionhub.jp）

所要時間: 約 10 分。アカウント作成と DNS 変更は運営者のみ。この手順は準備済みのリポジトリ側設定を有効にする。

## 1. Google Search Console（DNS TXT）

1. https://search.google.com/search-console を開く。
2. プロパティ追加 → **ドメイン** `visionhub.jp`（URL プレフィックスではない）。
3. 表示された TXT レコードをドメイン DNS に追加する。反映は数分〜数時間。
4. 「確認」が通ったら **サイトマップ** → `https://visionhub.jp/sitemap.xml` を送信する。
5. （任意）`https://visionhub.jp/feed.xml` はサイトマップではない。RSS リーダー用。

DNS 確認済みならメタタグ方式は不要。HTML に verification メタは入れない（`config/site.json` の `google_site_verification` は P3）。

## 2. Bing Webmaster

1. https://www.bing.com/webmasters を開く。
2. 「Google Search Console からインポート」を選ぶ（GSC が確認済みなら再確認不要）。
3. サイトマップ `https://visionhub.jp/sitemap.xml` が入っていることを確認する。

## 3. IndexNow

リポジトリ側:

- 公開キーファイル: リポジトリルートの `<64桁hex>.txt`（中身はキーそのもの）
- 設定: `config/indexnow.json` の `key` と `key_location`

確認:

```
py -3 scripts/indexnow_ping.py --urls https://visionhub.jp/ --dry-run
```

実送信は日次出荷のときだけ:

```
py -3 scripts/finalize_day_slide.py MMDD --indexnow
```

既定の `indexnow_ping.py` は dry-run。キーは公開情報（検索エンジンが取得する）。

## 4. 投入後の最短チェック

- GSC: サイトマップが「成功」で、最新 `day_slide_YYYY_MM_DD.html` がカバレッジに出始める（数日かかることがある）
- Bing: サイトマップインポート済み
- IndexNow: dry-run の JSON に `host` / `key` / `urlList` がある
