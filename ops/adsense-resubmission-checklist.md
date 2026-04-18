# AdSense 再申請チェックリスト

visionhub.jp の AdSense 審査を再送信する前に、以下を全て確認してから申請。

## Pre-Flight (必須 — 1 つでも欠けていたら待つ)

### インフラ
- [ ] 独自ドメイン `visionhub.jp` で稼働している（`awano27.github.io` ではない）
- [ ] HTTPS 強制が ON（GitHub Pages 設定画面）
- [ ] `curl -I https://visionhub.jp/` が 200 OK
- [ ] `/ads.txt` `/robots.txt` `/sitemap.xml` が 200 で配信

### E-E-A-T ページ
- [ ] `/about.html` に運営者の実名ハンドル・経歴・E-E-A-T・FAQ が記載
- [ ] `/privacy-policy.html` に Cookie・AdSense 開示あり
- [ ] `/contact.html` に mailto + GitHub Issues の 2 経路
- [ ] ヘッダー・フッター両方に About / Privacy / Contact リンク

### SEO 基盤
- [ ] GA4 Measurement ID が `config/analytics.json` に設定済み
- [ ] GA4 リアルタイムレポートで自分のアクセスが計測できる
- [ ] `sitemap.xml` が Search Console に登録され「成功」になっている
- [ ] インデックス済みページ**30 件以上**（Search Console → ページ）
- [ ] 主要 Hub 5 本すべてインデックス済み（URL 検査で確認）

### コンテンツ品質
- [ ] Hub 記事が 5 本（Claude Code / モデル比較 / MCP / 資金調達 / Claude料金）
- [ ] 月次 digest が backfill 済み（9 月分以上）
- [ ] 全日次スライドに NewsArticle JSON-LD / OG / 内部リンクバー完備
- [ ] 直近 7 日の新規スライドに運営者コメント段落あり（Scaled Content Abuse 対策）

### ポリシー遵守
- [ ] 暴力・アダルト・ギャンブル・ヘイトなど AdSense 禁止コンテンツなし
- [ ] 他サイトからのコピペが含まれていない（Claude Code 下書きに運営者加筆済み）
- [ ] 画像は自作 or 公正引用の範囲内
- [ ] `ads.txt` は準備済み（pub-XXXX は申請後に差し替え）

## 申請の手順

1. https://www.google.com/adsense/ にログイン（Search Console と同じGoogleアカウント）
2. 「サイト」→「サイトを追加」→ `visionhub.jp`
3. 発行された **AdSense スニペット**（`<script async src=...adsbygoogle.js?client=ca-pub-XXXXX></script>`）をコピー
4. 以下を実行（Claude に依頼でも OK）：
   ```bash
   # config/adsense.json を作成
   cat > config/adsense.json <<EOF
   {
     "publisher_id": "ca-pub-XXXXXXXXXXXXXXXX"
   }
   EOF

   # スニペットを全HTMLに一括挿入
   python scripts/inject_adsense.py

   # ads.txt の pub-ID を差し替え
   # (手動で ads.txt を編集 or sed)

   # コミット & プッシュ
   rtk git add -A
   rtk git commit -m "feat(adsense): activate AdSense on visionhub.jp"
   rtk git push origin main
   ```
5. AdSense ダッシュボードで「審査をリクエスト」→送信
6. 結果を待つ（通常 **2〜14 日**）

## 万一不承認が返ってきたら

拒否理由メールを読み、以下によくあるパターンの対処：

| 拒否理由 | 対処 |
|---|---|
| 「コンテンツの価値が低い」 | Hub 記事に運営者体験の段落を 2〜3 追記、合計文字数を 5,000+ に |
| 「サイトがナビゲートしにくい」 | 内部リンクバー・フッターを整備、404 ページを作成 |
| 「コンテンツがない」 | インデックス済みページが足りていない可能性 → さらに 2〜3 週間待つ |
| 「他者のコンテンツ」 | Hub/スライドで引用比率が高くないか再確認 |

## 承認後の最初の72時間

- [ ] AdSense 画面 → 自動広告 ON（遅延表示を避けるため手動ユニット優先の場合は OFF）
- [ ] 「ブランドセーフティ」でブロックしたいカテゴリを設定
- [ ] 「支払い」→住所・銀行口座登録
- [ ] `ads.txt` の実 publisher-id 反映を確認（`curl https://visionhub.jp/ads.txt`）
- [ ] GDPR メッセージを有効化

## 禁止事項（アカウント停止につながる）

- 自分・家族・友人にクリックを依頼 or 自分でクリック
- `robots.txt` で `Mediapartners-Google` をブロック
- `ads.txt` から publisher-id を削除する
- 成人向け・違法・ヘイトなどの禁止コンテンツを追加する
- 短期間に広告配置を激しく変更する（ボット扱い）
