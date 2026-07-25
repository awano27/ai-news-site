"""Fail when daily-news has shipped without X posts on consecutive days.

The X bookmarks come from the local 08:00 JST override run; the 06:00 cloud run
always publishes with none. When the override breaks, daily-news silently keeps
publishing news-only pages and nobody notices -- 2026-07-23..25 went three days
that way. This guard turns that silence into a red build.

A single zero day is legitimate (no bookmarks inside the 36h lookback), so only
consecutive zero days are treated as a failure.

Counting reads the archived page rather than daily-news/data.json because the
archive keeps one committed file per date. `class="x-pill"` marks exactly one
rendered X card, so its occurrence count equals that day's x_count.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ARCHIVE_DIR = Path("daily-news/archive")
ARCHIVE_NAME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.html$")
X_CARD = re.compile(r'class="x-pill"')
DEFAULT_TOLERATED_ZERO_DAYS = 1
REPORT_DAYS = 7


def archive_dates(repo: Path) -> list[date]:
    directory = repo / ARCHIVE_DIR
    if not directory.is_dir():
        return []
    dates: list[date] = []
    for path in directory.iterdir():
        match = ARCHIVE_NAME.match(path.name)
        if match and path.is_file():
            try:
                dates.append(date(*(int(part) for part in match.groups())))
            except ValueError:
                continue
    return sorted(dates)


def count_x_cards(repo: Path, day: date) -> int:
    path = repo / ARCHIVE_DIR / f"{day.isoformat()}.html"
    return len(X_CARD.findall(path.read_text(encoding="utf-8", errors="replace")))


def check(repo: Path, tolerated_zero_days: int) -> int:
    dates = archive_dates(repo)
    if not dates:
        print(f"no archived daily-news pages under {ARCHIVE_DIR}", file=sys.stderr)
        return 1

    recent = dates[-REPORT_DAYS:]
    counts = {day: count_x_cards(repo, day) for day in recent}
    for day in recent:
        print(f"{day.isoformat()} x={counts[day]}")

    window = tolerated_zero_days + 1
    if len(recent) < window:
        print(f"only {len(recent)} archived day(s); need {window} to judge a streak")
        return 0

    streak = recent[-window:]
    if any(counts[day] for day in streak):
        return 0

    days = ", ".join(day.isoformat() for day in streak)
    print(
        f"daily-news shipped with no X posts on {window} consecutive days ({days}).\n"
        "The 08:00 JST local override is the only source of X bookmarks, so it is\n"
        "almost certainly failing. Diagnose with the override log:\n"
        "  C:\\develop\\ai-news-site-automation\\logs\\run_daily_override.log\n"
        "A '[X] collected N bookmarks' line means collection is fine and the\n"
        "publish/git stage is at fault.",
        file=sys.stderr,
    )
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument(
        "--tolerated-zero-days",
        type=int,
        default=DEFAULT_TOLERATED_ZERO_DAYS,
        help="how many consecutive X-less days are still acceptable (default: 1)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.tolerated_zero_days < 0:
        print("--tolerated-zero-days must not be negative", file=sys.stderr)
        return 2
    return check(args.repo.resolve(), args.tolerated_zero_days)


if __name__ == "__main__":
    raise SystemExit(main())
