#!/usr/bin/env python3
"""Generate monthly digest pages from news/YYYY-MM-DD.json.

For each month that has at least 1 news file, emit
``presentations/digests/YYYY-MM.html`` — an evergreen pillar page
that lists the highest-rated items (stars >= threshold) across all
categories with links to the original daily slides.

Digests are fresh, substantive content optimised for SEO queries like
"2026年3月 AIニュース まとめ" and feed Google Discover.

Usage:
    python scripts/build_monthly_digest.py
    python scripts/build_monthly_digest.py --force
    python scripts/build_monthly_digest.py --month 2026-04
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEWS_DIR = ROOT / "news"
OUT_DIR = ROOT / "presentations" / "digests"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://visionhub.jp"
SITE_NAME = "AI Intelligence Hub"
TOP_N_PER_CATEGORY = 4

MONTH_JP = {
    1: "1月", 2: "2月", 3: "3月", 4: "4月", 5: "5月", 6: "6月",
    7: "7月", 8: "8月", 9: "9月", 10: "10月", 11: "11月", 12: "12月",
}

CATEGORY_JP = {
    "business": "ビジネス・資金調達",
    "tools": "ツール・プロダクト",
    "research": "研究・論文",
    "posts": "コラム・考察",
    "hardware": "ハードウェア",
    "policy": "政策・規制",
}

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.json$")


def load_news(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def collect_months() -> dict[str, list[Path]]:
    months: dict[str, list[Path]] = collections.defaultdict(list)
    for p in sorted(NEWS_DIR.glob("*.json")):
        m = DATE_RE.match(p.name)
        if not m:
            continue
        ym = f"{m.group(1)}-{m.group(2)}"
        months[ym].append(p)
    return months


def slide_url_for(date_iso: str) -> str | None:
    parts = date_iso.split("-")
    if len(parts) != 3:
        return None
    slide = f"presentations/day_slides/day_slide_{parts[0]}_{parts[1]}_{parts[2]}.html"
    if (ROOT / slide).exists():
        return f"{BASE_URL}/{slide}"
    return None


def gather_month_items(files: list[Path]) -> tuple[list[dict], dict[str, list[dict]]]:
    """Return (highlights, by_category) lists for a month."""
    highlights: list[dict] = []
    by_category: dict[str, list[dict]] = collections.defaultdict(list)
    seen_titles: set[str] = set()

    for p in files:
        data = load_news(p)
        if not data:
            continue
        date_iso = p.stem  # YYYY-MM-DD

        hl = data.get("highlight") or {}
        if hl.get("title"):
            item = {
                "title": hl["title"],
                "blurb": hl.get("summary") or "",
                "stars": hl.get("stars", 0),
                "category": hl.get("category") or "業界動向",
                "source": (hl.get("sources") or [{}])[0],
                "date": date_iso,
                "slide_url": slide_url_for(date_iso),
            }
            if item["title"] not in seen_titles:
                highlights.append(item)
                seen_titles.add(item["title"])

        sections = data.get("sections") or {}
        for cat, items in sections.items():
            if not isinstance(items, list):
                continue
            for raw in items:
                if not isinstance(raw, dict) or not raw.get("title"):
                    continue
                if raw["title"] in seen_titles:
                    continue
                by_category[cat].append({
                    "title": raw["title"],
                    "blurb": raw.get("blurb") or "",
                    "stars": raw.get("stars", 0),
                    "category": cat,
                    "source": raw.get("source") or {},
                    "date": raw.get("date") or date_iso,
                    "slide_url": slide_url_for(raw.get("date") or date_iso),
                })
                seen_titles.add(raw["title"])

    # Sort each bucket by stars desc then date desc
    highlights.sort(key=lambda x: (-int(x.get("stars") or 0), x["date"]), reverse=False)
    for cat in by_category:
        by_category[cat].sort(key=lambda x: (-int(x.get("stars") or 0), x["date"]), reverse=False)
        by_category[cat] = by_category[cat][:TOP_N_PER_CATEGORY]

    return highlights[:6], by_category


def render_item(item: dict) -> str:
    title = html.escape(item["title"])
    blurb = html.escape((item.get("blurb") or "").strip())[:180]
    stars = int(item.get("stars") or 0)
    src = item.get("source") or {}
    src_name = html.escape(src.get("name", "") or "")
    src_url = html.escape(src.get("url", "") or "", quote=True)
    date = html.escape(item["date"])
    slide = item.get("slide_url")
    stars_bar = "★" * stars + "☆" * max(0, 4 - stars)

    links: list[str] = []
    if slide:
        links.append(f'<a href="{html.escape(slide, quote=True)}">当日のスライド →</a>')
    if src_url:
        links.append(f'<a href="{src_url}" rel="noopener">{src_name or "一次ソース"} ↗</a>')
    link_html = " · ".join(links) if links else ""

    return (
        '<article class="digest-item">'
        f'<div class="meta"><span class="date">{date}</span>'
        f'<span class="stars" aria-label="{stars} 点">{stars_bar}</span></div>'
        f'<h3>{title}</h3>'
        + (f'<p>{blurb}…</p>' if blurb else "")
        + (f'<p class="links">{link_html}</p>' if link_html else "")
        + '</article>'
    )


def build_html(ym: str, highlights: list[dict], by_category: dict[str, list[dict]]) -> str:
    y, m = ym.split("-")
    month_title = f"{int(y)}年{MONTH_JP[int(m)]}"
    page_title = f"{month_title}のAIニュースまとめ｜主要発表・論文・資金調達を運営者がピックアップ"
    desc = (
        f"{month_title}のAI業界の動きを、visionhub.jp が毎日収集している "
        f"ニュースから厳選してまとめました。モデル発表・論文・資金調達・ツール公開を"
        f"カテゴリ別に整理し、各記事から当日のスライドと一次ソースに直接アクセスできます。"
    )
    canonical = f"{BASE_URL}/presentations/digests/{ym}.html"

    # compose category sections (exclude empties)
    cat_sections: list[str] = []
    for cat, items in by_category.items():
        if not items:
            continue
        label = CATEGORY_JP.get(cat, cat.capitalize())
        cat_html = [f'<section class="cat"><h2>{html.escape(label)}</h2>']
        for it in items:
            cat_html.append(render_item(it))
        cat_html.append("</section>")
        cat_sections.append("\n".join(cat_html))

    hi_html = "\n".join(render_item(x) for x in highlights) if highlights else '<p class="mute">この月のハイライト情報がまだありません。</p>'

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": page_title,
        "url": canonical,
        "inLanguage": "ja",
        "datePublished": f"{ym}-01",
        "author": {"@type": "Person", "name": "awano27", "url": f"{BASE_URL}/about.html"},
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": f"{BASE_URL}/",
            "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/assets/og/default.png", "width": 1200, "height": 630},
        },
        "about": f"Generative AI monthly digest for {month_title}",
    }, ensure_ascii=False, indent=2)

    tpl = f"""<!DOCTYPE html>
<!-- Monthly digest — generated by scripts/build_monthly_digest.py -->
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(page_title)}</title>
  <meta name="description" content="{html.escape(desc, quote=True)}" />
  <link rel="canonical" href="{canonical}" />
  <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large" />
  <meta name="author" content="awano27 (Claudian)" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="{SITE_NAME}" />
  <meta property="og:title" content="{html.escape(page_title)}" />
  <meta property="og:description" content="{html.escape(desc, quote=True)}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{BASE_URL}/assets/og/default.png" />
  <meta property="og:locale" content="ja_JP" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{html.escape(page_title)}" />
  <meta name="twitter:description" content="{html.escape(desc, quote=True)}" />
  <meta name="twitter:image" content="{BASE_URL}/assets/og/default.png" />
  <!-- SEO_META_INJECTED v1 -->
  <!-- JSONLD_INJECTED v1 -->
  <script type="application/ld+json">
{jsonld}
  </script>
  <!-- GA4_INJECTED v1 -->
  <script src="/assets/js/analytics.js" defer></script>
  <style>
    :root{{--bg:#070F26;--panel:#0D1733;--panel2:#121E42;--ink:#EDF2FF;--mute:#8A9ABF;--mute2:#B5C3E1;--accent:#FFCC00;--accent2:#5EE7DF;--line:rgba(255,255,255,.08)}}
    *{{box-sizing:border-box}}
    body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Inter","Noto Sans JP",system-ui,sans-serif;line-height:1.8;font-size:16px}}
    a{{color:var(--accent2);text-decoration:none}}a:hover{{text-decoration:underline}}
    .container{{max-width:900px;margin:0 auto;padding:0 24px}}
    header.site-header{{border-bottom:1px solid var(--line);padding:18px 0;background:rgba(7,15,38,.92);backdrop-filter:saturate(140%) blur(8px);position:sticky;top:0;z-index:10}}
    .header-row{{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}}
    .brand{{display:flex;gap:10px;align-items:center;color:var(--ink);font-weight:700}}
    .brand-mark{{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:8px;background:var(--accent);color:#111;font-weight:900}}
    .nav a{{color:var(--mute);margin-left:18px;font-size:14px;font-weight:600}}.nav a:hover{{color:var(--ink)}}
    main{{padding:56px 0 96px}}
    .eyebrow{{display:inline-flex;align-items:center;gap:10px;color:var(--mute);font-size:12px;letter-spacing:.18em;text-transform:uppercase;margin-bottom:14px}}
    .eyebrow .dot{{width:8px;height:8px;background:var(--accent);border-radius:50%}}
    h1{{font-size:clamp(28px,4.5vw,40px);line-height:1.25;margin:0 0 12px;letter-spacing:-.01em}}
    h1 .accent{{color:var(--accent)}}
    .lede{{color:var(--mute2);font-size:17px;margin:0 0 28px;max-width:68ch}}
    h2{{font-size:22px;margin:40px 0 10px;padding-left:14px;border-left:4px solid var(--accent)}}
    h3{{font-size:17px;margin:6px 0;color:var(--ink);line-height:1.45}}
    .digest-item{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}}
    .digest-item .meta{{display:flex;gap:14px;font-size:12px;color:var(--mute);letter-spacing:.04em;margin-bottom:6px}}
    .digest-item .stars{{color:var(--accent);font-weight:700;letter-spacing:.08em}}
    .digest-item p{{margin:6px 0 0;color:var(--mute2);font-size:14.5px;line-height:1.7}}
    .digest-item .links{{margin-top:10px;font-size:13px}}
    .digest-item .links a{{margin-right:10px}}
    .mute{{color:var(--mute)}}
    .cta-row{{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}}
    .btn{{display:inline-flex;align-items:center;gap:8px;padding:11px 18px;border-radius:10px;background:var(--accent);color:#111;font-weight:800;font-size:14px}}
    .btn.ghost{{background:transparent;border:1px solid var(--line);color:var(--ink)}}
    .btn:hover{{text-decoration:none;filter:brightness(1.08)}}
    footer.site-footer{{border-top:1px solid var(--line);padding:28px 0;color:var(--mute);font-size:13px}}
    .footer-row{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}}
  </style>
</head>
<body>
  <header class="site-header">
    <div class="container header-row">
      <a class="brand" href="/"><span class="brand-mark">AI</span><span>INTELLIGENCE HUB</span></a>
      <nav class="nav" aria-label="グローバル">
        <a href="/">ホーム</a><a href="/about.html">運営者</a>
        <a href="/privacy-policy.html">プライバシー</a><a href="/contact.html">お問い合わせ</a>
      </nav>
    </div>
  </header>

  <main>
    <article class="container">
      <div class="eyebrow"><span class="dot"></span><span>MONTHLY DIGEST</span></div>
      <h1>{html.escape(month_title)} <span class="accent">AIニュースまとめ</span></h1>
      <p class="lede">
        {html.escape(month_title)}に visionhub.jp が収集・要約した AI 関連ニュースの中から、
        運営者（awano27 / Claudian）が選んだ注目トピックをカテゴリ別に整理しました。
        各項目から当日のスライドと一次ソースへアクセスできます。
      </p>

      <section class="cat"><h2>今月のハイライト</h2>
{hi_html}
      </section>

{''.join(cat_sections)}

      <div class="cta-row">
        <a class="btn" href="/">最新スライドへ</a>
        <a class="btn ghost" href="/presentations/hubs/ai-model-comparison-2026.html">モデル比較ガイド</a>
        <a class="btn ghost" href="/presentations/hubs/claude-code-guide-2026.html">Claude Code ガイド</a>
      </div>

      <p style="color:var(--mute);font-size:12px;margin-top:48px;text-align:center">
        生成：{dt.date.today().isoformat()} ／ © 2026 awano27 — {SITE_NAME}
      </p>
    </article>
  </main>

  <footer class="site-footer">
    <div class="container footer-row">
      <span>© 2026 awano27 — {SITE_NAME} — AIの最前線を5分で</span>
      <span>
        <a href="/about.html">About</a> ·
        <a href="/privacy-policy.html">Privacy</a> ·
        <a href="/contact.html">Contact</a> ·
        <a href="https://github.com/awano27/ai-news-site">GitHub</a>
      </span>
    </div>
  </footer>
</body>
</html>
"""
    return tpl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="Only build this month (YYYY-MM)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    months = collect_months()
    if args.month:
        months = {args.month: months.get(args.month, [])}

    produced = 0
    skipped = 0
    empty = 0

    for ym, files in sorted(months.items()):
        if not files:
            empty += 1
            continue
        highlights, by_cat = gather_month_items(files)
        if not highlights and not any(by_cat.values()):
            empty += 1
            continue

        html_out = build_html(ym, highlights, by_cat)
        out = OUT_DIR / f"{ym}.html"
        prev = out.read_text(encoding="utf-8") if out.exists() else ""
        if not args.force and prev == html_out:
            skipped += 1
            continue
        out.write_text(html_out, encoding="utf-8")
        produced += 1
        print(f"  wrote {out.relative_to(ROOT)} ({len(files)} source files)")

    print(f"[build_monthly_digest] produced {produced}, skipped {skipped} unchanged, {empty} empty")
    return 0


if __name__ == "__main__":
    sys.exit(main())
