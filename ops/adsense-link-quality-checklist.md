# AdSense 審査向け リンク品質チェックリスト

visionhub.jp のリンク全件について AdSense が嫌うパターンを排除するためのチェック。
**毎回の申請前**と**月1回の定期確認**で使う運用ドキュメント。

## A. 404 / 500 / 302 ループがないこと

- [ ] `curl -I` で主要URL全件 `200 OK` を確認
  - [ ] `https://visionhub.jp/`
  - [ ] `https://visionhub.jp/about.html`
  - [ ] `https://visionhub.jp/contact.html`
  - [ ] `https://visionhub.jp/privacy-policy.html`
  - [ ] `https://visionhub.jp/credits.html`
  - [ ] `https://visionhub.jp/ads.txt`
  - [ ] `https://visionhub.jp/robots.txt`
  - [ ] `https://visionhub.jp/sitemap.xml`
- [ ] 5本の Hub 記事すべて `200`
  - [ ] `/presentations/hubs/claude-code-guide-2026.html`
  - [ ] `/presentations/hubs/ai-model-comparison-2026.html`
  - [ ] `/presentations/hubs/mcp-complete-guide.html`
  - [ ] `/presentations/hubs/ai-funding-2026.html`
  - [ ] `/presentations/hubs/claude-models-2026.html`
- [ ] 9本の月次digestすべて `200`
- [ ] 最新5日分の日次スライドが `200`
- [ ] **レガシー `/ai-news-site/*` URL**は redirect 済み（meta refresh + JS）
- [ ] 旧 `awano27.github.io/ai-news-site` → `visionhub.jp` 301 互換動作

## B. アンカー・内部リンクの品質

- [ ] `#resources` など全アンカーが該当 `id` と一致
- [ ] 全 nav メニュー項目が本当にスクロール or 遷移する
- [ ] "こちら" "詳細" 等の**意味のないアンカーテキスト**を撲滅
- [ ] リンクテキストに**検索キーワード**を含める（E-E-A-T 的にもプラス）
- [ ] 同一ページ内で同一URLへのリンクは **2本以下**

## C. 外部リンクの安全性

- [ ] すべての外部リンクは `https://`（mixed content なし）
- [ ] 外部リンクに `rel="noopener"` 付与（セキュリティ対策）
- [ ] アフィリエイト・PRリンクには `rel="sponsored"` 付与
- [ ] ユーザー投稿系があれば `rel="ugc"` 付与
- [ ] 有害サイト・リンクファームへのリンクなし

## D. ボタン・CTA の品質

- [ ] `href="#"` の空リンクは onclick 付きのみ
- [ ] `href="javascript:..."` は使用していない
- [ ] すべての CTA が実在するページに遷移
- [ ] モバイルでタップ領域が 44×44 px 以上
- [ ] ボタンラベルが遷移先を明確に示している（例: ×「詳細」 ○「Claude Code完全ガイドを読む」）

## E. コンテンツ品質（リンク先）

- [ ] リンク先ページに**本文が 500 文字以上**ある（薄ページなし）
- [ ] 未来日付（例: "2099-01-01"）がタイトル/本文にない
- [ ] 「読み込み中…」が永続表示されるページなし（データ取得失敗時のフォールバック必須）
- [ ] タイトル重複がない（複数ページが同じ `<title>` を持たない）
- [ ] 画像はすべて `alt` 属性あり（アクセシビリティ + SEO）

## F. 構造化データ

- [ ] 各ページに JSON-LD（NewsArticle / Article / CollectionPage / AboutPage）
- [ ] canonical URL が正しい visionhub.jp を指す
- [ ] og:image が実在する PNG を指す（404 なし）
- [ ] Twitter Card が `summary_large_image` で設定済み

## G. 自動チェックスクリプト

```bash
# 主要 URL 一括 HTTP ステータスチェック
python -c "
import urllib.request, concurrent.futures
urls = [
  'https://visionhub.jp/',
  'https://visionhub.jp/about.html',
  'https://visionhub.jp/contact.html',
  'https://visionhub.jp/privacy-policy.html',
  'https://visionhub.jp/credits.html',
  'https://visionhub.jp/ads.txt',
  'https://visionhub.jp/robots.txt',
  'https://visionhub.jp/sitemap.xml',
  'https://visionhub.jp/ai-news-site/',
  'https://visionhub.jp/presentations/day_slides_index.html',
  'https://visionhub.jp/presentations/day_slides_list.html',
  'https://visionhub.jp/presentations/ai_ranking_report_latest.html',
  'https://visionhub.jp/presentations/ai_ranking_interactive.html',
  'https://visionhub.jp/presentations/json_archive_viewer.html',
  'https://visionhub.jp/presentations/hubs/claude-code-guide-2026.html',
]
def chk(u):
  try:
    return (urllib.request.urlopen(u, timeout=10).status, u)
  except urllib.error.HTTPError as e: return (e.code, u)
  except Exception as e: return ('ERR', u)
with concurrent.futures.ThreadPoolExecutor(8) as ex:
  for r in ex.map(chk, urls): print(f'{r[0]:>4} {r[1]}')
"

# Discover 適合性チェック（全HTMLに対する構造化データ監査）
python scripts/check_discover_readiness.py --strict

# サイトマップに記載の全URLをクロール（擬似）
curl -s https://visionhub.jp/sitemap.xml | grep -oE 'https?://[^<]+' | \
  xargs -n1 -P8 -I{} curl -sI -o /dev/null -w "%{http_code} {}\n" {}
```

## H. 申請前の最終確認

- [ ] Search Console でインデックス済みページが **30 件以上**
- [ ] Google Search Console の「カバレッジ」に**警告/エラーがない**
- [ ] `sitemap.xml` が「成功」ステータス
- [ ] 上記 A〜F の全チェックがパス
- [ ] 本ドキュメントの更新日を記録

| 確認日 | 担当 | A | B | C | D | E | F |
|---|---|---|---|---|---|---|---|
| 2026-04-19 | awano27 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## I. 審査官目線の NG 例

- **クリックベイト的タイトル**（"衝撃！"、"驚愕！"）→ 使わない
- **実質的にリンク切れ**（ページが存在するが内容が空 / "Coming soon" のみ）→ 全ページ 500 字以上保証
- **被リンク先が AdSense ポリシー違反サイト**（違法DL、海賊版等）→ 外部リンクは精査
- **重複コンテンツ**（他サイトのコピペ）→ 自家生成と運営者加筆で回避
- **ナビゲーションが壊れている**（ハンバーガーが開かない等）→ モバイルで目視確認
