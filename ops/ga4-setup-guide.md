# GA4 セットアップガイド（visionhub.jp 用）

このドキュメントの指示に従って **GA4 Measurement ID (`G-XXXXXXXXXX`)** を取得してください。取得後、`config/analytics.json` に書き込めば `scripts/inject_analytics.py` が全HTMLに自動で埋め込みます。

所要時間: **5〜10分**

---

## 手順

### 1. Google Analytics にアクセス

https://analytics.google.com/ を開いてログイン（Search Console と同じGoogleアカウント推奨）

### 2. プロパティを作成

- 左下の「**管理**」（歯車アイコン）→ **アカウント**列の「作成」→ **プロパティ**
- アカウント名: `awano27` または任意
- プロパティ名: `AI Intelligence Hub (visionhub.jp)`
- タイムゾーン: **日本**
- 通貨: **日本円 (JPY)**
- ビジネス情報: 「ブログ/出版」「小規模」「リードの創出」などお好みで
- 目標: 「ベースラインレポートを取得する」をチェック

### 3. データストリームを設定

- プラットフォーム: **ウェブ**
- ウェブサイトの URL: `https://visionhub.jp`
- ストリーム名: `visionhub.jp`
- **拡張計測機能は OFF**。独自イベントとの重複・URL等の自動送信を防止。
- 「ストリームを作成」

### 4. Measurement ID をコピー

- ストリーム詳細画面の右上に表示されます
- 形式: `G-XXXXXXXXXX`（Gから始まる10文字の英数字）
- **これをコピー**

### 5. config/analytics.json にペースト

`config/analytics.json` を作成し、以下の内容で保存：

```json
{
  "measurement_id": "G-XXXXXXXXXX",
  "stream_url": "https://visionhub.jp"
}
```

※ `G-XXXXXXXXXX` を実際にコピーしたIDに差し替え。

### 6. （後で）Claude に「GA4 IDを取得しました」と伝える

あとは私が以下を実行します：
- `assets/js/analytics.js` に GA4 スニペット埋め込み
- `scripts/inject_analytics.py` で全HTMLに `<script>` タグを一括注入
- コミット・プッシュ

### 7. 導入後の確認

- GA4 画面 →「**レポート**」→「**リアルタイム**」
- ブラウザで https://visionhub.jp/ を開く
- 数秒〜数十秒で「**過去30分間のアクティブユーザー: 1**」が表示されれば成功

---

## セキュリティ上の注意

- `G-XXXXXXXXXX` は**公開情報**です。GitHub にコミットして問題ありません（ブラウザが読む値なので秘匿不可能）
- Measurement ID は**計測のみ**を行い、**GA4 管理画面にアクセスする権限は与えない**ものではありません。不正な計測データの送信には注意が必要です

---

## 追加推奨設定（GA4 画面で後日）

- **データ保持期間**: 管理 → データの設定 → データ保持 → **14ヶ月** に変更（デフォルト2ヶ月だと分析が浅くなる）
- **Google シグナル**: 無効。広告パーソナライズも無効。
- **Search Console 連携**: 管理 → プロダクトのリンク → Search Console → visionhub.jp と紐付け（検索クエリ分析が統合される）

---

## 投入後の確認

`config/analytics.json` の `measurement_id` を実値にしたら:

```
py -3 scripts/check_analytics_config.py
```

exit 0 なら形式は正しい。placeholder（`REPLACE` / `XXXX`）や `G-` 以外の値なら exit 1。


## 2026-11-15 公開設定
- ポップアップ・国判定なしの自動計測。プライバシーページの停止／再開からブラウザごとの設定が可能。
- DNT/GPC、停止保存済み、保存設定読取失敗時にはタグを読み込まない。
- 公開configの旧 measurement_id は null のまま。新loaderは optout_measurement_id だけ読む。旧JSキャッシュの意図しない計測を防ぐ。
- クエリ・フラグメント・自由入力・完全な外部URLは送らない。広告機能/拡張計測は有効にしない。
- node --test tests/analytics_consent.cjs で回帰確認。
- 海外からもアクセス可能。地域別法令への適合を技術設定だけで保証するものではない。
