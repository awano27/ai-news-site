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
- **拡張計測機能** は ON のまま（スクロール・ファイル DL 等を自動計測）
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
- Measurement ID は**計測のみ**を行い、**GA4 管理画面にアクセスする権限は与えない**ので、漏洩しても悪用されません

---

## 追加推奨設定（GA4 画面で後日）

- **データ保持期間**: 管理 → データの設定 → データ保持 → **14ヶ月** に変更（デフォルト2ヶ月だと分析が浅くなる）
- **Google シグナル**: 管理 → データの収集と変更 → Google シグナル → 有効化（デモグラ分析が取れる）
- **Search Console 連携**: 管理 → プロダクトのリンク → Search Console → visionhub.jp と紐付け（検索クエリ分析が統合される）
