#!/usr/bin/env python3
"""Give every daily-news archive snapshot a canonical URL of its own.

Snapshots written before archive_page_html existed either name /daily-news/
as canonical or carry no canonical at all. Rerunning changes nothing.

Usage:
    python scripts/backfill_daily_news_archive_canonical.py [--check]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.auto_collect.daily_news_page import ARCHIVE_DIR, archive_page_html  # noqa: E402

DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Report stale snapshots, write nothing")
    args = ap.parse_args(argv)

    stale = []
    for path in sorted(ARCHIVE_DIR.glob("*.html")):
        if not DATED.match(path.stem):
            continue
        before = path.read_text(encoding="utf-8")
        after = archive_page_html(before, path.stem)
        if after == before:
            continue
        stale.append(path.name)
        if not args.check:
            path.write_text(after, encoding="utf-8", newline="")
    verb = "stale" if args.check else "rewrote"
    print(f"[backfill_daily_news_archive_canonical] {verb} {len(stale)} snapshots")
    return 1 if args.check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
