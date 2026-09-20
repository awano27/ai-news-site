#!/usr/bin/env python3
"""Fail when feed.xml lags behind the newest day slide.

``scripts/build_feed.py`` regenerates the Atom feed from the day-slide files,
but only when ``finalize_day_slide.py`` is run. When a slide is shipped without
finalize, the feed silently stops (it stayed at 2026-08-21 while slides kept
shipping through 2026-09-20). This guard turns that into a red build.

Checks:
  - the newest ``<entry>`` in feed.xml points at the newest
    ``presentations/day_slides/day_slide_YYYY_MM_DD.html``
  - the feed-level ``<updated>`` is not older than that slide date

Usage:
    python scripts/check_feed_freshness.py
    python scripts/check_feed_freshness.py --feed feed.xml --slides presentations/day_slides
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEED = ROOT / "feed.xml"
DEFAULT_SLIDES = ROOT / "presentations" / "day_slides"

SLIDE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
ENTRY_RE = re.compile(r"<entry>.*?</entry>", re.DOTALL)
LINK_RE = re.compile(r'<link\s+[^>]*href="([^"]+)"')
UPDATED_RE = re.compile(r"<updated>(\d{4}-\d{2}-\d{2})")


def newest_slide_date(slides_dir: Path) -> date | None:
    newest: date | None = None
    for path in slides_dir.glob("day_slide_????_??_??.html"):
        m = SLIDE_RE.search(path.name)
        if not m:
            continue
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
        if newest is None or d > newest:
            newest = d
    return newest


def newest_feed_entry_date(feed_text: str) -> date | None:
    newest: date | None = None
    for entry in ENTRY_RE.findall(feed_text):
        link = LINK_RE.search(entry)
        if not link:
            continue
        m = SLIDE_RE.search(link.group(1))
        if not m:
            continue
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
        if newest is None or d > newest:
            newest = d
    return newest


def feed_updated_date(feed_text: str) -> date | None:
    """Return the feed-level <updated> date (the first one, before any <entry>)."""
    head = feed_text.split("<entry>", 1)[0]
    m = UPDATED_RE.search(head)
    if not m:
        return None
    return date.fromisoformat(m.group(1))


def check(feed_path: Path, slides_dir: Path) -> list[str]:
    """Return a list of problems; empty means the feed is fresh."""
    problems: list[str] = []
    if not feed_path.is_file():
        return [f"feed missing: {feed_path}"]
    if not slides_dir.is_dir():
        return [f"slides dir missing: {slides_dir}"]

    text = feed_path.read_text(encoding="utf-8")
    slide_date = newest_slide_date(slides_dir)
    entry_date = newest_feed_entry_date(text)
    updated = feed_updated_date(text)

    if slide_date is None:
        return ["no day slides found"]
    if entry_date is None:
        problems.append("feed has no day-slide entries")
    elif entry_date < slide_date:
        problems.append(
            f"feed newest entry {entry_date} is older than newest slide {slide_date} "
            "(run: python scripts/finalize_day_slide.py MMDD)"
        )
    if updated is None:
        problems.append("feed has no <updated> element")
    elif updated < slide_date:
        problems.append(f"feed <updated> {updated} is older than newest slide {slide_date}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify feed.xml carries the newest day slide.")
    ap.add_argument("--feed", type=Path, default=DEFAULT_FEED)
    ap.add_argument("--slides", type=Path, default=DEFAULT_SLIDES)
    args = ap.parse_args(argv)

    problems = check(args.feed, args.slides)
    if problems:
        for p in problems:
            print(f"[check_feed_freshness] FAIL: {p}", file=sys.stderr)
        return 1
    slide_date = newest_slide_date(args.slides)
    print(f"[check_feed_freshness] OK: feed newest entry matches newest slide {slide_date}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
