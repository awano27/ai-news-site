#!/usr/bin/env python3
"""Rebuild the public archive index from real dated news JSON files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DATED_NEWS_FILE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def rebuild_archive_index(news_dir: Path, output: Path) -> int:
    entries: list[dict[str, object]] = []
    for news_file in sorted(news_dir.glob("*.json"), key=lambda path: path.name, reverse=True):
        if not DATED_NEWS_FILE.fullmatch(news_file.name):
            continue

        with news_file.open(encoding="utf-8") as source:
            json.load(source)

        entries.append(
            {
                "date": news_file.stem,
                "file": news_file.name,
                "count": 1,
            }
        )

    rendered = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
    with output.open("w", encoding="utf-8", newline="\n") as destination:
        destination.write(rendered)
    return len(entries)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--news-dir", type=Path, default=REPOSITORY_ROOT / "news")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "public-pages" / "news" / "archive_index.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = rebuild_archive_index(args.news_dir, args.output)
    print(f"Rebuilt {args.output} ({count} entries)")


if __name__ == "__main__":
    main()
