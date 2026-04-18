#!/usr/bin/env python3
"""Inject a shared 'Related guides' block into every day slide.

Each day slide gets a compact 4-link row pointing to the five Hub
articles + the matching monthly digest. This boosts internal link
density (Google PageRank) and cross-reads (time-on-site), both of
which matter for SEO and AdSense review.

The block is inserted immediately after ``<body ...>`` and marked
``<!-- INTERNAL_LINKS_INJECTED v1 -->`` so re-runs are idempotent.

Usage:
    python scripts/build_internal_links.py --dry-run
    python scripts/build_internal_links.py
    python scripts/build_internal_links.py --force
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDE_DIR = ROOT / "presentations" / "day_slides"
MARKER = "<!-- INTERNAL_LINKS_INJECTED v1 -->"
DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
BODY_OPEN_RE = re.compile(r"(<body[^>]*>)", re.IGNORECASE)

HUBS = [
    ("/presentations/hubs/claude-code-guide-2026.html", "Claude Code 完全ガイド"),
    ("/presentations/hubs/ai-model-comparison-2026.html", "Claude vs ChatGPT vs Gemini 比較"),
    ("/presentations/hubs/mcp-complete-guide.html", "MCP 完全ガイド"),
    ("/presentations/hubs/claude-models-2026.html", "Claude モデル料金比較"),
    ("/presentations/hubs/ai-funding-2026.html", "AI資金調達まとめ"),
]


def block_for(slide_path: Path) -> str:
    m = DATE_RE.search(slide_path.name)
    digest_href = ""
    digest_label = ""
    if m:
        digest_href = f"/presentations/digests/{m.group(1)}-{m.group(2)}.html"
        digest_label = f"{int(m.group(1))}年{int(m.group(2))}月のまとめ"
        if not (ROOT / digest_href.lstrip("/")).exists():
            digest_href = ""

    links = []
    for href, label in HUBS:
        links.append(f'<a href="{href}">{label}</a>')
    if digest_href:
        links.append(f'<a href="{digest_href}">{digest_label}</a>')

    style = (
        "background:#0D1733;border-bottom:1px solid rgba(255,255,255,.08);"
        "padding:10px 18px;font:13px/1.4 'Noto Sans JP',system-ui,sans-serif;"
        "color:#8A9ABF;display:flex;gap:14px;flex-wrap:wrap;align-items:center;"
        "position:relative;z-index:100"
    )
    link_style = (
        "color:#5EE7DF;text-decoration:none;padding:2px 8px;border-radius:999px;"
        "border:1px solid rgba(255,255,255,.08);transition:color .15s"
    )
    nav = " ".join(
        f'<a href="{h}" style="{link_style}">{l}</a>' if "<a" not in f'<a href="{h}"'
        else f'<a href="{h}" style="{link_style}">{l}</a>'
        for (h, l) in [(h, l) for h, l in [
            (l.split('href="')[1].split('"')[0], l.split(">")[1].split("</a>")[0]) for l in links
        ]]
    )

    # Simpler render without the convoluted parsing above:
    anchor_html = " ".join(
        f'<a href="{h}" style="{link_style}">{l}</a>'
        for h, l in (
            [(href, label) for href, label in HUBS] +
            ([(digest_href, digest_label)] if digest_href else [])
        )
    )

    return (
        f"\n{MARKER}\n"
        f'<aside class="related-nav" aria-label="関連ガイド" '
        f'style="{style}">'
        f'<span style="color:#FFCC00;font-weight:700;letter-spacing:.04em">関連ガイド</span>'
        f'{anchor_html}'
        f'</aside>\n'
    )


def process_file(path: Path, force: bool, dry_run: bool) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "skip (non-utf8)"

    if MARKER in text and not force:
        return "skip (already injected)"

    m = BODY_OPEN_RE.search(text)
    if not m:
        return "skip (no <body>)"

    if force and MARKER in text:
        text = re.sub(
            rf"\n?{re.escape(MARKER)}.*?</aside>\s*",
            "",
            text,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
        m = BODY_OPEN_RE.search(text)
        if not m:
            return "skip (no <body> after clean)"

    block = block_for(path)
    new_text = text[: m.end()] + block + text[m.end():]

    if dry_run:
        return f"would inject ({len(block)} bytes)"

    path.write_text(new_text, encoding="utf-8")
    return "injected"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.paths:
        files = []
        for p in args.paths:
            pp = Path(p) if Path(p).is_absolute() else (ROOT / p)
            if pp.is_file():
                files.append(pp)
            elif pp.is_dir():
                files.extend(sorted(pp.glob("day_slide_*.html")))
    else:
        files = sorted(SLIDE_DIR.glob("day_slide_*.html"))

    stats: dict[str, int] = {}
    for f in files:
        r = process_file(f, args.force, args.dry_run)
        key = "would inject" if r.startswith("would") else r
        stats[key] = stats.get(key, 0) + 1

    print(f"[internal_links] {sum(stats.values())} files: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
