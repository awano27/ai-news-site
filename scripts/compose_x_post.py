#!/usr/bin/env python3
"""Draft an X (Twitter) post for a given day slide.

Reads the slide's <title> and first paragraph, crops to 280 chars with
a visionhub.jp URL + hashtags, and writes the draft to
``output/x_posts/YYYY-MM-DD.txt`` for the operator to review and
post manually (automated posting is an AdSense/TOS risk).

Usage:
    python scripts/compose_x_post.py                      # latest slide
    python scripts/compose_x_post.py --date 2026-04-18
    python scripts/compose_x_post.py --slide presentations/day_slides/day_slide_2026_04_18.html
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDE_DIR = ROOT / "presentations" / "day_slides"
OUT_DIR = ROOT / "output" / "x_posts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://visionhub.jp"
HASHTAGS = "#生成AI #Claude #AIニュース"
DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def extract_body_lead(text: str, max_chars: int = 140) -> str:
    body_m = re.search(r"<body[^>]*>(.*)</body>", text, re.IGNORECASE | re.DOTALL)
    body = body_m.group(1) if body_m else text
    paragraphs = P_RE.findall(body)
    for p in paragraphs:
        clean = WS_RE.sub(" ", html.unescape(TAG_RE.sub(" ", p))).strip()
        if len(clean) > 20:
            return clean[:max_chars]
    return ""


def pick_slide(args) -> Path | None:
    if args.slide:
        p = Path(args.slide) if Path(args.slide).is_absolute() else (ROOT / args.slide)
        return p if p.exists() else None
    if args.date:
        y, m, d = args.date.split("-")
        p = SLIDE_DIR / f"day_slide_{y}_{m}_{d}.html"
        return p if p.exists() else None
    # latest by filename
    slides = sorted(SLIDE_DIR.glob("day_slide_????_??_??.html"), reverse=True)
    return slides[0] if slides else None


def compose(slide: Path) -> tuple[str, str, str]:
    text = slide.read_text(encoding="utf-8")
    t_m = TITLE_RE.search(text)
    title = WS_RE.sub(" ", html.unescape(t_m.group(1)).strip()) if t_m else slide.name
    lead = extract_body_lead(text)
    m = DATE_RE.search(slide.name)
    date_iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
    url = f"{BASE_URL}/presentations/day_slides/{slide.name}"

    # X posts: Twitter counts URL as 23 characters (t.co wrapping).
    url_cost = 23
    hashtag_cost = len(HASHTAGS) + 1
    budget = 280 - url_cost - hashtag_cost - 4  # spacing

    # Header (date emoji + date + title) — aim for ~60 chars
    header = f"[{date_iso}] " if date_iso else ""
    body_budget = budget - len(header)
    if len(title) > body_budget:
        title = title[: max(10, body_budget - 1)] + "…"
    composed = f"{header}{title}\n\n{lead[:max(0, budget - len(header) - len(title) - 2)]}\n\n{url}\n{HASHTAGS}"
    return date_iso, url, composed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--slide")
    ap.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing file")
    args = ap.parse_args()

    slide = pick_slide(args)
    if not slide:
        print("[compose_x_post] no slide found", file=sys.stderr)
        return 1

    date_iso, url, post = compose(slide)

    if args.stdout:
        print(post)
        return 0

    name = (date_iso or slide.stem) + ".txt"
    out = OUT_DIR / name
    out.write_text(post + "\n", encoding="utf-8")
    print(f"[compose_x_post] wrote {out.relative_to(ROOT)} ({len(post)} chars)")
    print(post)
    return 0


if __name__ == "__main__":
    sys.exit(main())
