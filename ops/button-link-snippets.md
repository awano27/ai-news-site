# 安全ボタンリンク スニペット集（visionhub.jp 用）

index.html / Hub / スライドに貼り付けできる、**404 リスクゼロ**のボタン HTML 集。
すべて相対パス or 確認済み絶対パスで、`visionhub.jp` カスタムドメインで動作します。

## 1. トップナビ（既に index.html に配置済み）

```html
<nav class="nav" aria-label="グローバル">
  <a href="#this-week">最新スライド</a>
  <a href="#categories">ハイライト</a>
  <a href="#archive">アーカイブ</a>
  <a href="#resources">リソース</a>
  <a href="/about.html">About</a>
  <a href="/privacy-policy.html">Privacy</a>
  <a href="/contact.html">Contact</a>
  <a id="latestSlideHeroBtn" class="cta" href="/presentations/day_slides_index.html">
    今日のスライド <span aria-hidden="true">→</span>
  </a>
</nav>
```

## 2. リソースカード（Hub/ガイド誘導）

```html
<section id="resources" class="section section-dark">
  <div class="res-grid">
    <a class="res-card" href="/presentations/hubs/claude-code-guide-2026.html">
      <span class="res-num">01</span>
      <div class="res-body">
        <div class="res-title">Claude Code 完全ガイド2026</div>
        <div class="res-desc">CLI 導入・MCP・実運用パターンまで網羅。</div>
      </div>
    </a>
    <a class="res-card" href="/presentations/hubs/ai-model-comparison-2026.html">
      <span class="res-num">02</span>
      <div class="res-body">
        <div class="res-title">Claude vs ChatGPT vs Gemini 比較</div>
        <div class="res-desc">料金・性能・向き不向きを毎月更新。</div>
      </div>
    </a>
    <a class="res-card" href="/presentations/hubs/mcp-complete-guide.html">
      <span class="res-num">03</span>
      <div class="res-body">
        <div class="res-title">MCP 完全ガイド</div>
        <div class="res-desc">LLM × 外部ツールの標準プロトコル解説。</div>
      </div>
    </a>
    <a class="res-card" href="/presentations/recommended_tools.html">
      <span class="res-num">04</span>
      <div class="res-body">
        <div class="res-title">おすすめAIツール厳選集</div>
        <div class="res-desc">職種別・用途別カタログ。</div>
      </div>
    </a>
  </div>
</section>
```

## 3. アーカイブ誘導（3 ルート）

```html
<div class="archive-routes">
  <a class="btn" href="/presentations/day_slides_index.html">📅 日次スライド索引</a>
  <a class="btn" href="/presentations/day_slides_list.html">📋 一覧ビュー</a>
  <a class="btn" href="/presentations/json_archive_viewer.html">🗂 JSONアーカイブ</a>
  <a class="btn" href="/presentations/ai_ranking_report_latest.html">🏆 最新ランキング</a>
  <a class="btn" href="/presentations/news_archive.html">🔎 ニュースアーカイブ検索</a>
</div>
```

## 4. フッター（全ページ共通）

```html
<footer class="site-footer">
  <div class="container footer-row">
    <span>© 2026 awano27 — AI Intelligence Hub — AIの最前線を5分で</span>
    <span>
      <a href="/about.html">About</a> ·
      <a href="/privacy-policy.html">Privacy</a> ·
      <a href="/contact.html">Contact</a> ·
      <a href="/credits.html">Credits</a> ·
      <a href="https://github.com/awano27/ai-news-site">GitHub</a>
    </span>
  </div>
</footer>
```

## 5. 日次スライド関連ガイド（スライド本文冒頭に自動注入済み）

`scripts/build_internal_links.py` が全日次スライドに挿入している帯：

```html
<aside class="related-nav" aria-label="関連ガイド">
  <span style="color:#FFCC00;font-weight:700">関連ガイド</span>
  <a href="/presentations/hubs/claude-code-guide-2026.html">Claude Code 完全ガイド</a>
  <a href="/presentations/hubs/ai-model-comparison-2026.html">Claude vs ChatGPT vs Gemini 比較</a>
  <a href="/presentations/hubs/mcp-complete-guide.html">MCP 完全ガイド</a>
  <a href="/presentations/hubs/claude-models-2026.html">Claude モデル料金比較</a>
  <a href="/presentations/hubs/ai-funding-2026.html">AI資金調達まとめ</a>
  <a href="/presentations/digests/YYYY-MM.html">{年月}のまとめ</a>
</aside>
```

## 6. 外部からのレガシー URL 対策（自動）

`/ai-news-site/index.html` にリダイレクトページを配置済み。
古いブックマーク・被リンクが `https://visionhub.jp/ai-news-site/*` で来ても、`meta refresh` + JS で `/ * ` に正規化します。

## 7. 絶対に使ってはいけないアンチパターン

| NG | 理由 | 代替 |
|---|---|---|
| `href="javascript:void(0)"` | AdSense でリンク品質低下と見なされる | `<button type="button">` を使う |
| `href="#"` 単独 | onclick がないと無効リンクに見える | `href="#resources"` のような実アンカー |
| `href="/ai-news-site/..."` | 404 | `href="/..."` |
| `href="http://..."` の外部リンク | HTTPS 混在で警告 | `https://` のみ使う |
| 空の `<a href=""></a>` | NOP リンク | そもそも削除する |

## 8. AdSense 的に好まれるリンク設計

- **内部リンク密度**: 1 ページあたり 5〜15 本（多すぎると SEO 減点）
- **アンカーテキストは具体的に**: ×「こちら」 ○「Claude Code 完全ガイド」
- **1 ページに同一 URL への重複リンク**は 2 本まで
- **外部リンクは `rel="noopener"`** 必須
- **`target="_blank"` は外部リンクのみ**に限定

## 9. 確認コマンド

```bash
# 全ページの 404 リンクスキャン
python -c "
import re, urllib.request, concurrent.futures
from pathlib import Path
urls = set()
for p in Path('presentations').rglob('*.html'):
  for m in re.findall(r'href=\"([^\"#?]+)', p.read_text(encoding='utf-8', errors='ignore')):
    if m.startswith('/') or m.startswith('http'):
      urls.add('https://visionhub.jp' + m if m.startswith('/') else m)
def chk(u):
  try:
    urllib.request.urlopen(u, timeout=8)
    return (200, u)
  except Exception as e:
    return (getattr(e, 'code', 'ERR'), u)
with concurrent.futures.ThreadPoolExecutor(8) as ex:
  bad = [r for r in ex.map(chk, list(urls)[:200]) if r[0] != 200]
print('BROKEN:', len(bad))
for r in bad: print(r)
"
```
