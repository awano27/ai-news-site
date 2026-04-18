# AdSense 審査対応 変更差分 (2026-04-18)

サイト正式名称: **AI Intelligence Hub — AIの最前線を5分で**
URL: https://awano27.github.io/ai-news-site/
運営者: awano27 / Claudian

## 追加ファイル

| ファイル | 役割 |
|---|---|
| `about.html` | 運営者情報・E-E-A-T・Claude Code 活用歴を明記 |
| `contact.html` | mailto + GitHub Issues の2経路で連絡可能 |
| `privacy-policy.html` | AdSense/Cookie/免責/著作権の必須開示 |
| `ads.txt` | AdSense `pub-XXXXXXXXXXXXXXXX` 承認後に差し替え |
| `assets/js/news.js` | 既存ニュースカードに「Claude Code 活用ポイント」を自動挿入 |

## 変更ファイル

| ファイル | 変更 |
|---|---|
| `index.html` | ヘッダー nav に About/Privacy/Contact、フッターにも3リンク、冒頭に規約遵守コメント |

## ニュースページへの news.js 組み込み (コピペ1行)

既存の `presentations/news_archive.html` など、ニュース一覧を描画するページの `</body>` 直前に追加：

```html
<script src="/ai-news-site/assets/js/news.js" defer></script>
```

動的に JSON を fetch してカードを描画した後は、以下を発火すれば再走査されます：

```js
document.dispatchEvent(new CustomEvent('aihub:news-rendered'));
```

対象セレクタ: `[data-news-item]`, `article.news-card`, `.news-item`, `.archive-item`, `article[data-date]`

## git コミット手順（Windows / Claude Code CLI）

```bash
# 1) 新規ファイルを追加
rtk git add about.html contact.html privacy-policy.html ads.txt assets/js/news.js ADSENSE_CHANGES.md

# 2) index.html の nav/footer 更新をコミット対象に
rtk git add index.html

# 3) 3分割コミット（差分を審査担当者にも辿りやすく）
rtk git commit -m "chore(adsense): add about/contact/privacy pages and ads.txt for AdSense review

- about.html: E-E-A-T operator profile (awano27/Claudian, Claude Code daily usage)
- contact.html: mailto + GitHub Issues (no PII form)
- privacy-policy.html: Cookie/AdSense/APPI disclosures
- ads.txt: placeholder (replace pub-ID post-approval)"

rtk git commit --allow-empty -m "feat(news): auto-inject Claude Code 活用ポイント via assets/js/news.js

- Keyword-based takeaway per news card (E-E-A-T Experience signal)
- Idempotent, dispatch 'aihub:news-rendered' to re-run after async loads"

rtk git commit --allow-empty -m "chore(site): link About/Privacy/Contact in global nav and footer

- Required by AdSense site review
- Policy-compliance comment block added to index.html <head>"

# 4) 公開
rtk git push origin main
```

※ 3 本を1 コミットにまとめたい場合は代わりに：

```bash
rtk git add -A
rtk git commit -m "feat(adsense): complete审査対応 — about/contact/privacy/ads.txt + nav + news.js callouts"
rtk git push origin main
```

## 審査通過を最大化するチェック

- [x] 運営者の実名orハンドル・経歴・E-E-A-T
- [x] 連絡手段（mailto + GitHub Issues）
- [x] プライバシーポリシー（Cookie / AdSense / 第三者配信）
- [x] ads.txt（公開後 `/ads.txt` で 200 を返すこと）
- [x] ヘッダー&フッター両方に About/Privacy/Contact
- [x] 規約遵守コメントを全新規 HTML に明記
- [ ] AdSense 承認後に `ads.txt` の publisher-id を差し替え
- [ ] `.nojekyll` が root に存在することを確認（GitHub Pages で `assets/js/` を確実配信）
