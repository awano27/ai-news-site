#!/usr/bin/env python3
"""Capture the retained daily edition and incrementally extend search.

Run after daily-news/data.json publication priority has selected the edition,
then before homepage coverage is refreshed. Legacy dated aggregates and the
homepage's news/latest.json interface are intentionally untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_search_index import atomic_write, build_index, json_bytes, load_json, normalize_daily_payload
from src.auto_collect.publication_priority import prefer_existing


def sync_daily_search(root: Path = ROOT) -> dict:
    root = Path(root)
    candidate = normalize_daily_payload(load_json(root / "daily-news/data.json"))
    capture_path = root / "public-pages/news/daily" / f"{candidate['date']}.json"
    preserved = False
    if capture_path.exists():
        existing = normalize_daily_payload(load_json(capture_path))
        if existing["date"] != candidate["date"]:
            raise ValueError("Snapshot date does not match filename")
        if prefer_existing(existing, candidate):
            candidate = existing
            preserved = True
    # All reads and validation complete before either public file is replaced.
    rows = build_index(root, daily_payload=candidate)
    capture_bytes, index_bytes = json_bytes(candidate), json_bytes(rows)
    atomic_write(capture_path, capture_bytes)
    atomic_write(root / "public-pages/news/search_index.json", index_bytes)
    return {"date": candidate["date"], "total": candidate["total"], "news_count": candidate["news_count"],
            "x_count": candidate["x_count"], "search_total": len(rows), "snapshot": str(capture_path),
            "preserved_richer_snapshot": preserved}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        result = sync_daily_search(args.root)
    except (ValueError, OSError) as exc:
        print(f"[sync_daily_search] ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"[sync_daily_search] {result['date']}: {result['total']} articles "
          f"(news={result['news_count']}, X={result['x_count']}), search={result['search_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
