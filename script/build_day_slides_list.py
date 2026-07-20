#!/usr/bin/env python3
"""
Render presentations/day_slides_list.html — the "AI NEWSSTAND" visual archive —
from presentations/day_slides/meta_index.json (built by build_day_slides_index.py).

The page is fully static (SEO-safe, works without JS): latest-issue hero,
"today in 3 lines" brief, this-week strip with a category DNA bar, a sticky
search/filter bar, and month-grouped cover-card grids (<details>, latest three
months open). Search/filter is progressive enhancement via inline vanilla JS.

Cards link to the absolute slide URLs (https://visionhub.jp/...), which
scripts/publish_image2_day_slide.py's validate() step asserts.

Run order (both are idempotent full rebuilds):

    python script/build_day_slides_index.py
    python script/build_day_slides_list.py
"""
from __future__ import annotations

import json
import re
from html import escape
from datetime import date as date_cls
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "presentations" / "day_slides" / "meta_index.json"
OUT = ROOT / "presentations" / "day_slides_list.html"

# Category colors: validated 6-slot categorical palette for dark surface
# #06090d (passes lightness band / chroma / CVD separation / normal-vision
# floor / contrast checks). "other" is a deliberately neutral fold, not a
# seventh identity hue. Brand cyan/green stay UI accents, never category ink.
CATS = {
    "model": ("モデル", "#3987e5"),
    "agent": ("エージェント", "#008300"),
    "arch": ("アーキテクチャ", "#d55181"),
    "infra": ("インフラ", "#c98500"),
    "prod": ("プロダクト", "#199e70"),
    "gov": ("ガバナンス", "#d95926"),
    "other": ("その他", "#7f93a8"),
}
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
OPEN_MONTHS = 3  # newest months rendered expanded


def wd(iso: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    return WEEKDAYS[date_cls(y, m, d).weekday()]


def jp_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{y}年{int(m)}月{int(d)}日"


HIRAGANA_RE = re.compile(r"[ぁ-ん]")


def split_long_clause(part: str) -> list[str]:
    """Split one long sentence into readable lines.

    Prefer 、 boundaries after hiragana (clause ends like 「〜へ移し、」)
    so enumerations like 「Coverage Map、Evidence Graph」stay together;
    fall back to accumulating any 、-separated segments up to ~44 chars.
    """
    chunks: list[str] = []
    buf = ""
    for seg in part.split("、"):
        buf = f"{buf}、{seg}" if buf else seg
        if len(buf) > 24 and HIRAGANA_RE.search(buf[-1]):
            chunks.append(buf)
            buf = ""
    if buf:
        chunks.append(buf)

    lines: list[str] = []
    for chunk in chunks:
        if len(chunk) <= 58:
            lines.append(chunk)
            continue
        acc = ""
        for seg in chunk.split("、"):
            if acc and len(acc) + len(seg) > 44:
                lines.append(acc)
                acc = seg
            else:
                acc = f"{acc}、{seg}" if acc else seg
        if acc:
            lines.append(acc)
    return lines


def make_brief(title: str, description: str) -> list[str]:
    """Derive up to 3 scannable lines from the deck's own description."""
    text = (description or title).strip()
    lines: list[str] = []
    for part in (p.strip() for p in re.split(r"。", text) if p.strip()):
        if len(lines) == 3:
            break
        if len(part) <= 58:
            lines.append(part)
        else:
            lines.extend(split_long_clause(part))
    return [line.rstrip("、") for line in lines[:3]] or [title]


def search_text(issue: dict) -> str:
    return escape(
        " ".join(
            filter(None, [issue["title"], issue["description"], issue["cat_label"], issue["section"], issue["date"]])
        ).lower(),
        quote=True,
    )


def chip(cat: str, small: bool = False) -> str:
    label, _ = CATS[cat]
    cls = "chip chip-sm" if small else "chip"
    return f'<span class="{cls}" style="color:var(--cat-{cat});border-color:var(--cat-{cat})">{label}</span>'


def cover_media(issue: dict, *, cls: str) -> str:
    if issue["cover"]:
        return (
            f'<img class="{cls}" src="{escape(issue["cover"], quote=True)}" alt="" '
            f'loading="lazy" decoding="async">'
        )
    _, color = CATS[issue["cat"]]
    mm_dd = issue["date"][5:7] + "." + issue["date"][8:10]
    return (
        f'<div class="{cls} gen-cover" style="background:'
        f"linear-gradient(135deg, color-mix(in srgb, {color} 45%, #06090d), #06090d 82%);"
        f'border-bottom:2px solid {color}">'
        f'<span class="gd">{mm_dd}</span>'
        f'<span class="gl">AI NEWSSTAND — No.{issue["no"]}</span></div>'
    )


def card(issue: dict) -> str:
    desc = escape(issue["description"][:120]) if issue["description"] else ""
    return f"""      <a class="card" href="{escape(issue["url"], quote=True)}" data-cat="{issue["cat"]}" data-text="{search_text(issue)}" style="--cat:var(--cat-{issue["cat"]})">
        <div class="thumb">{cover_media(issue, cls="thumb-img")}<span class="datebadge">{issue["date"][5:7]}.{issue["date"][8:10]}</span></div>
        <div class="body">{chip(issue["cat"], small=True)}
          <div class="t">{escape(issue["title"])}</div>
          <div class="d">{desc}</div>
        </div>
      </a>
"""


def strip_card(issue: dict) -> str:
    return f"""      <a class="strip-card" href="{escape(issue["url"], quote=True)}">
        {cover_media(issue, cls="strip-img")}
        <div class="p"><div class="date">{issue["date"][5:7]}.{issue["date"][8:10]} {wd(issue["date"])}</div>
          <div class="t">{escape(issue["title"])}</div>{chip(issue["cat"], small=True)}</div>
      </a>
"""


def render(data: dict) -> str:
    issues = data["issues"]  # newest first
    latest = issues[0]
    week = issues[1:8]
    total = len(issues)

    brief_lines = make_brief(latest["title"], latest["description"])
    brief_html = "\n".join(
        f'      <div class="brief-line"><span class="no">{i:02d}</span>'
        f'<span class="gt">&gt;</span><span>{escape(line)}</span></div>'
        for i, line in enumerate(brief_lines, start=1)
    )

    dna_html = "\n".join(
        f'    <span style="background:var(--cat-{i["cat"]})" title="{i["date"][5:7]}.{i["date"][8:10]} '
        f'{escape(CATS[i["cat"]][0])}: {escape(i["title"], quote=True)}"></span>'
        for i in week
    )
    strip_html = "".join(strip_card(i) for i in week)

    months: dict[str, list[dict]] = {}
    for issue in issues:
        months.setdefault(issue["date"][:7], []).append(issue)

    month_sections = []
    for idx, (month, month_issues) in enumerate(months.items()):
        y, m = month.split("-")
        open_attr = " open" if idx < OPEN_MONTHS else ""
        cards = "".join(card(i) for i in month_issues)
        month_sections.append(f"""  <details class="month-group" data-month="{month}"{open_attr}>
    <summary class="month-head"><span class="m">{y}.{m}</span><span class="c"><span class="month-count">{len(month_issues)}</span> 件</span><span class="line"></span></summary>
    <div class="slides-grid">
{cards}    </div>
  </details>
""")

    chips_html = "".join(
        f'      <button class="fchip" data-cat="{cat}" style="--c:var(--cat-{cat})">'
        f'<span class="sw" style="background:var(--cat-{cat})"></span>{label}</button>\n'
        for cat, (label, _) in CATS.items()
        if data["categories"].get(cat)
    )

    max_count = max(data["categories"].values())
    catbar_html = "".join(
        f'        <div class="row"><span>{CATS[cat][0]}</span>'
        f'<div class="bar" style="width:{round(100 * n / max_count)}%;background:var(--cat-{cat})"></div>'
        f"<span>{n}</span></div>\n"
        for cat, n in sorted(data["categories"].items(), key=lambda kv: -kv[1])
    )

    cat_vars = "\n".join(f"      --cat-{cat}: {color};" for cat, (_, color) in CATS.items())
    og_image = (
        f'  <meta property="og:image" content="https://visionhub.jp/presentations/{latest["cover"]}">\n'
        '  <meta name="twitter:card" content="summary_large_image">\n'
        if latest["cover"] else ""
    )
    description_meta = (
        f"2025年7月30日から{jp_date(data['latest'])}までの日次AIニューススライド{total}本を、"
        "カバー画像・要約・カテゴリ付きで一覧できるアーカイブ。今日の要点は3行で把握できます。"
    )

    head = f"""<!DOCTYPE html>
<html lang="ja">

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>日次スライド一覧 — AI Intelligence Hub</title>
  <meta name="description" content="{escape(description_meta, quote=True)}" />
  <link rel="canonical" href="https://visionhub.jp/presentations/day_slides_list.html" />
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="AI Intelligence Hub">
  <meta property="og:title" content="日次スライド一覧 — AI NEWSSTAND">
  <meta property="og:description" content="{escape(description_meta, quote=True)}">
  <meta property="og:url" content="https://visionhub.jp/presentations/day_slides_list.html">
{og_image}  <link rel="stylesheet" href="../assets/ntt-theme.css">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans+JP:wght@400;500;700;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #06090d; --bg2: #0b1118; --bg-card: #0d1420;
      --nb-border: #1a2a3a; --border-soft: rgba(255,255,255,0.06);
      --cyan: #00d4f0; --green: #34d399;
      --ink: #d0dde8; --ink2: #8da0b4; --ink-muted: #6b8399; --ink-white: #f0f4f8;
{cat_vars}
    }}
"""

    css = """    .nb * { box-sizing: border-box; }
    .nb { background: var(--bg); color: var(--ink); font-family: 'Noto Sans JP', -apple-system, sans-serif; line-height: 1.6; }
    .nb a { color: inherit; text-decoration: none; }
    .nb-section { max-width: 1200px; margin: 40px auto 0; padding: 0 clamp(16px, 4vw, 40px); }

    /* hero */
    .hero { position: relative; min-height: 460px; display: flex; align-items: center; overflow: hidden; border-bottom: 1px solid var(--nb-border); }
    .hero-img { position: absolute; inset: 0 0 0 40%; }
    .hero-img img, .hero-img .gen-cover { width: 100%; height: 100%; object-fit: cover; object-position: center right; display: block; }
    .hero-img::after { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, var(--bg) 0%, var(--bg) 18%, rgba(6,9,13,0.82) 45%, rgba(6,9,13,0.12) 85%), linear-gradient(0deg, var(--bg) 0%, transparent 30%); }
    .hero-body { position: relative; z-index: 1; max-width: 1200px; width: 100%; margin: 0 auto; padding: 48px clamp(16px, 4vw, 40px); }
    .hero-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.2em; color: var(--ink-muted); margin-bottom: 4px; }
    .hero-pagetitle { font-size: 15px; font-weight: 700; color: var(--ink2); margin: 0 0 18px; }
    .hero-kicker { display: flex; align-items: center; gap: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.15em; color: var(--cyan); margin-bottom: 12px; }
    .hero-kicker .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); animation: nb-pulse 2s infinite; }
    @keyframes nb-pulse { 50% { opacity: 0.3; } }
    @media (prefers-reduced-motion: reduce) { .hero-kicker .dot { animation: none; } }
    .hero-meta { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--ink2); margin-bottom: 12px; }
    .hero-title { font-size: clamp(25px, 3.8vw, 40px); font-weight: 900; line-height: 1.28; color: var(--ink-white); max-width: 22ch; margin: 10px 0 14px; }
    .hero-lead { max-width: 54ch; font-size: 15px; color: var(--ink2); margin: 0 0 22px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .hero-actions { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
    .cta { display: inline-flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 22px; background: var(--cyan); color: var(--bg); font-weight: 700; font-size: 14px; border-radius: 8px; transition: box-shadow 0.2s; }
    .cta:hover { box-shadow: 0 0 24px rgba(0,212,240,0.4); }
    .read-badge { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--green); border: 1px solid var(--green); border-radius: 8px; padding: 6px 12px; letter-spacing: 0.08em; }

    /* chips */
    .chip { display: inline-flex; align-items: center; gap: 6px; font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.05em; padding: 3px 10px; border-radius: 100px; border: 1px solid; background: rgba(255,255,255,0.02); }
    .chip::before { content: ''; width: 8px; height: 8px; border-radius: 2px; background: currentColor; }
    .chip-sm { font-size: 10px; }

    /* brief */
    .brief { max-width: 1200px; margin: 28px auto 0; padding: 0 clamp(16px, 4vw, 40px); }
    .brief-card { background: var(--bg2); border: 1px solid var(--nb-border); border-radius: 12px; padding: 20px 24px; }
    .brief-card .cmd { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--ink-muted); margin-bottom: 12px; }
    .brief-card .cmd b { color: var(--green); font-weight: 500; }
    .brief-line { display: flex; gap: 12px; align-items: baseline; padding: 6px 0; font-size: 15.5px; line-height: 1.7; }
    .brief-line .no { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--cyan); flex-shrink: 0; }
    .brief-line .gt { font-family: 'JetBrains Mono', monospace; color: var(--green); flex-shrink: 0; }

    /* section head */
    .sec-head { display: flex; align-items: baseline; gap: 14px; margin-bottom: 6px; }
    .sec-head .en { font-family: 'JetBrains Mono', monospace; font-size: 12px; letter-spacing: 0.2em; color: var(--cyan); }
    .sec-head .ja { font-size: 20px; font-weight: 700; color: var(--ink-white); }
    .sec-head .line { flex: 1; height: 1px; background: linear-gradient(90deg, var(--nb-border), transparent); }

    /* DNA bar */
    .dna { display: flex; gap: 2px; margin: 10px 0 16px; }
    .dna span { flex: 1; height: 8px; border-radius: 2px; cursor: default; }
    .dna-cap { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--ink-muted); margin-bottom: 4px; letter-spacing: 0.1em; }

    /* week strip */
    .strip { display: flex; gap: 14px; overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 12px; scrollbar-width: thin; }
    .strip-card { flex: 0 0 232px; scroll-snap-align: start; background: var(--bg-card); border: 1px solid var(--border-soft); border-radius: 12px; overflow: hidden; transition: transform 0.15s, border-color 0.15s; }
    .strip-card:hover { transform: translateY(-2px); border-color: var(--cyan); }
    .strip-img { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }
    .strip-card .p { padding: 10px 12px 12px; }
    .strip-card .date { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--cyan); margin-bottom: 4px; }
    .strip-card .t { font-size: 13px; font-weight: 600; line-height: 1.45; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.9em; margin-bottom: 8px; }

    /* filter bar */
    .filterbar { position: sticky; top: 0; z-index: 50; background: rgba(6,9,13,0.92); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--nb-border); margin-top: 40px; }
    .filterbar-in { max-width: 1200px; margin: 0 auto; padding: 10px clamp(16px, 4vw, 40px); display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
    .searchbox { position: relative; }
    .searchbox input { width: 250px; height: 38px; padding: 0 12px 0 34px; background: var(--bg2); border: 1px solid var(--nb-border); border-radius: 8px; color: var(--ink); font-family: 'JetBrains Mono', monospace; font-size: 12px; }
    .searchbox input:focus { outline: none; border-color: var(--cyan); }
    .searchbox::before { content: '⌕'; position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--ink-muted); font-size: 16px; }
    .fchips { display: flex; gap: 6px; flex-wrap: wrap; }
    .fchip { font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 6px 12px; border: 1px solid var(--nb-border); border-radius: 100px; color: var(--ink2); background: none; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
    .fchip .sw { width: 8px; height: 8px; border-radius: 2px; }
    .fchip:hover { color: var(--ink-white); }
    .fchip.on { color: var(--bg); font-weight: 700; background: var(--c, var(--cyan)); border-color: var(--c, var(--cyan)); }
    .hitcount { margin-left: auto; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--ink-muted); }
    .hitcount b { color: var(--green); font-weight: 500; }

    /* archive months */
    .month-group { border: none; }
    .month-head { display: flex; align-items: baseline; gap: 14px; margin: 36px 0 4px; cursor: pointer; list-style: none; }
    .month-head::-webkit-details-marker { display: none; }
    .month-head::before { content: '▸'; font-family: 'JetBrains Mono', monospace; color: var(--ink-muted); }
    .month-group[open] > .month-head::before { content: '▾'; }
    .month-head .m { font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 700; color: var(--ink-white); }
    .month-head .c { font-size: 12px; color: var(--ink-muted); font-family: 'JetBrains Mono', monospace; }
    .month-head .line { flex: 1; height: 1px; background: linear-gradient(90deg, rgba(0,212,240,0.4), transparent); }
    .slides-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(272px, 1fr)); gap: 18px; margin-top: 14px; }
    .card { background: var(--bg-card); border: 1px solid var(--border-soft); border-radius: 12px; overflow: hidden; position: relative; transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s; content-visibility: auto; contain-intrinsic-size: 300px; }
    .card:hover { transform: translateY(-2px); border-color: var(--cat, var(--cyan)); box-shadow: 0 0 18px color-mix(in srgb, var(--cat, var(--cyan)) 18%, transparent); }
    .card .thumb { position: relative; aspect-ratio: 16/9; overflow: hidden; }
    .thumb-img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .card .datebadge { position: absolute; top: 10px; left: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--ink-white); background: rgba(6,9,13,0.8); padding: 3px 8px; border-radius: 4px; letter-spacing: 0.08em; }
    .card .body { padding: 14px 16px 16px; }
    .card .t { font-size: 14.5px; font-weight: 600; line-height: 1.5; color: var(--ink-white); margin: 8px 0 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 3em; }
    .card .d { font-size: 12.5px; color: var(--ink2); line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 3.2em; }
    .gen-cover { display: flex; flex-direction: column; justify-content: space-between; padding: 14px; background: var(--bg2); }
    .gen-cover .gd { font-family: 'JetBrains Mono', monospace; font-size: 32px; font-weight: 700; color: rgba(255,255,255,0.92); line-height: 1; }
    .gen-cover .gl { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.18em; color: rgba(255,255,255,0.55); align-self: flex-end; }

    /* footer stats */
    .nb-foot { border-top: 1px solid var(--nb-border); margin-top: 64px; }
    .foot-in { max-width: 1200px; margin: 0 auto; padding: 36px clamp(16px, 4vw, 40px); display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 28px; }
    .foot-in h3 { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.2em; color: var(--ink-muted); margin: 0 0 12px; }
    .stat-line { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--green); line-height: 2; }
    .catbar { display: flex; flex-direction: column; gap: 7px; }
    .catbar .row { display: grid; grid-template-columns: 96px 1fr 34px; align-items: center; gap: 8px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--ink2); }
    .catbar .bar { height: 6px; border-radius: 0 3px 3px 0; }
    .foot-links a { display: block; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--ink2); line-height: 2.2; }
    .foot-links a:hover { color: var(--cyan); }

    /* mobile */
    @media (max-width: 680px) {
      .hero { min-height: 0; }
      .hero-img { inset: 0; }
      .hero-img::after { background: linear-gradient(0deg, var(--bg) 8%, rgba(6,9,13,0.82) 55%, rgba(6,9,13,0.3) 100%); }
      .hero-body { padding: 170px 16px 32px; }
      .slides-grid { grid-template-columns: 1fr; gap: 10px; }
      .card { display: grid; grid-template-columns: 42% 1fr; contain-intrinsic-size: 130px; }
      .card .thumb { aspect-ratio: auto; height: 100%; min-height: 96px; }
      .card .gen-cover { aspect-ratio: auto; height: 100%; }
      .card .body { padding: 10px 12px; }
      .card .t { min-height: 0; font-size: 13.5px; margin-top: 4px; }
      .card .d { display: none; }
      .searchbox { flex: 1 1 100%; }
      .searchbox input { width: 100%; }
      .hitcount { margin-left: 0; }
      .month-head .m { font-size: 22px; }
    }
  </style>
</head>
"""

    body = f"""<body class="ntt-page">
  <header class="ntt-header">
    <div class="ntt-header-row">
      <a class="ntt-brand" href="/">
        <span class="ntt-brand-mark">AI</span>
        <span class="ntt-brand-text">INTELLIGENCE HUB<small>DAILY AI INSIGHTS</small></span>
      </a>
      <nav class="ntt-nav">
        <a href="/#this-week" class="is-active">最新スライド</a>
        <a href="/#archive">アーカイブ</a>
        <a href="/#resources">リソース</a>
        <a class="ntt-cta" href="/presentations/day_slides_index.html">今日のスライド →</a>
      </nav>
    </div>
  </header>

<div class="nb">
  <section class="hero">
    <div class="hero-img">{cover_media(latest, cls="hero-cover")}</div>
    <div class="hero-body">
      <div class="hero-eyebrow">ALL SLIDES — AI NEWSSTAND</div>
      <h1 class="hero-pagetitle">日次スライド一覧</h1>
      <div class="hero-kicker"><span class="dot"></span>LATEST ISSUE — 最新号</div>
      <div class="hero-meta">{latest["date"].replace("-", ".")} {wd(latest["date"])} / No.{latest["no"]}</div>
      {chip(latest["cat"])}
      <h2 class="hero-title">{escape(latest["title"])}</h2>
      <p class="hero-lead">{escape(latest["description"])}</p>
      <div class="hero-actions">
        <a class="cta" href="{escape(latest["url"], quote=True)}">この号を読む →</a>
        <span class="read-badge">⏱ 5 MIN READ</span>
      </div>
    </div>
  </section>

  <section class="brief">
    <div class="brief-card">
      <div class="cmd"><b>$</b> today --summary <span style="color:var(--ink-muted)">// {latest["date"]}</span></div>
{brief_html}
    </div>
  </section>

  <section class="nb-section">
    <div class="sec-head"><span class="en">THIS WEEK</span><span class="ja">今週の7本</span><span class="line"></span></div>
    <div class="dna-cap">WEEK DNA — 左が最新（色 = カテゴリ / ホバーで詳細）</div>
    <div class="dna" aria-hidden="true">
{dna_html}
    </div>
    <div class="strip">
{strip_html}    </div>
  </section>

  <div class="filterbar">
    <div class="filterbar-in">
      <div class="searchbox"><input id="nbSearch" type="search" placeholder="タイトル・キーワードで検索…  [/]" aria-label="スライドを検索"></div>
      <div class="fchips" id="nbChips">
        <button class="fchip on" data-cat="all">ALL</button>
{chips_html}      </div>
      <span class="hitcount"><b id="nbHit">{total}</b> / {total} issues</span>
    </div>
  </div>

  <main class="nb-section" id="archive">
{"".join(month_sections)}  </main>

  <footer class="nb-foot">
    <div class="foot-in">
      <div>
        <h3>PUBLICATION</h3>
        <div class="stat-line">{total} issues<br>since {data["since"].replace("-", ".")}<br>毎日更新</div>
      </div>
      <div>
        <h3>CATEGORIES — ALL TIME</h3>
        <div class="catbar">
{catbar_html}        </div>
      </div>
      <div class="foot-links">
        <h3>MORE</h3>
        <a href="/presentations/day_slides_index.html">今日のスライド</a>
        <a href="/presentations/day_slides/list.json">JSON (ナビ用 list.json)</a>
        <a href="/presentations/day_slides/meta_index.json">JSON (メタデータ meta_index.json)</a>
      </div>
    </div>
  </footer>
</div>
"""

    js = """<script>
  (function () {
    var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
    var groups = Array.prototype.slice.call(document.querySelectorAll('.month-group'));
    var hit = document.getElementById('nbHit');
    var input = document.getElementById('nbSearch');
    var activeCat = 'all';
    var openSnapshot = null;

    function applyFilter() {
      var term = input.value.trim().toLowerCase();
      var filtering = term !== '' || activeCat !== 'all';
      if (filtering && openSnapshot === null) {
        openSnapshot = groups.map(function (g) { return g.open; });
        groups.forEach(function (g) { g.open = true; });
      } else if (!filtering && openSnapshot !== null) {
        groups.forEach(function (g, i) { g.open = openSnapshot[i]; });
        openSnapshot = null;
      }
      var visible = 0;
      cards.forEach(function (c) {
        var okCat = activeCat === 'all' || c.getAttribute('data-cat') === activeCat;
        var okTerm = !term || (c.getAttribute('data-text') || '').indexOf(term) !== -1;
        var show = okCat && okTerm;
        c.style.display = show ? '' : 'none';
        if (show) visible++;
      });
      groups.forEach(function (g) {
        var any = Array.prototype.some.call(g.querySelectorAll('.card'), function (c) {
          return c.style.display !== 'none';
        });
        g.style.display = any ? '' : 'none';
      });
      hit.textContent = visible;
    }

    input.addEventListener('input', applyFilter);
    document.getElementById('nbChips').addEventListener('click', function (e) {
      var btn = e.target.closest('.fchip');
      if (!btn) return;
      document.querySelectorAll('.fchip').forEach(function (b) { b.classList.remove('on'); });
      btn.classList.add('on');
      activeCat = btn.getAttribute('data-cat');
      applyFilter();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && document.activeElement !== input) { e.preventDefault(); input.focus(); }
    });
  })();
</script>
</body>

</html>
"""

    return head + css + body + js


def main() -> int:
    data = json.loads(META.read_text(encoding="utf-8"))
    OUT.write_text(render(data), encoding="utf-8")
    print(f"wrote {OUT} ({data['generated_from']} issues, latest {data['latest']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
