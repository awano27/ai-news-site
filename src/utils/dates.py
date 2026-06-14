"""
src/utils/dates.py — Shared date-parsing helpers.

Canonical implementations for the two date patterns that appear across this
codebase:

1. ``MMDD.txt`` filename  →  ``YYYY-MM-DD`` string
   Defined in update_news_archive.py:parse_date_from_filename (lines 14-28)
   Duplicated (differently) in src/generators/day_news_slide_generator.py:43-58

2. ``date.today().strftime("%m%d")``  →  current MMDD string
   Repeated in src/auto_collect/main.py:72, html_report.py:531,
   report_generator.py:112.

Usage
-----
    from src.utils.dates import mmdd_to_iso, today_mmdd, today_iso, slide_filename_date
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Core: MMDD → YYYY-MM-DD
# ---------------------------------------------------------------------------

_MMDD_RE = re.compile(r"^(\d{2})(\d{2})")
_YYYYMMDD_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})")


def mmdd_to_iso(mmdd: str, *, ref: date | None = None) -> Optional[str]:
    """Convert a bare *MMDD* string to ``YYYY-MM-DD``.

    Chooses the year so that the resulting date is not in the future relative
    to *ref* (defaults to today).  This matches the logic in
    update_news_archive.py:parse_date_from_filename.

    Args:
        mmdd: 4-character string like ``"0913"`` or stem of a filename like
              ``"0913.txt"`` / ``"0913-extra.txt"``.  Leading alpha/suffix is
              stripped.
        ref:  Reference date for year selection (default: today).

    Returns:
        ISO-8601 date string ``"YYYY-MM-DD"``, or ``None`` if *mmdd* cannot
        be parsed.

    Examples:
        >>> mmdd_to_iso("0913")
        '2026-09-13'
        >>> mmdd_to_iso("0913.txt")
        '2026-09-13'
    """
    # Accept bare "MMDD", "MMDD.txt", "MMDD-suffix.txt", Path stems
    s = str(mmdd)
    # Strip file extension and any suffix after the first non-digit after pos 4
    s = re.sub(r"[^\d].*$", "", s[:4] if len(s) >= 4 else s)

    m = _MMDD_RE.match(s)
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    now = ref or date.today()
    year = now.year
    try:
        candidate = date(year, month, day)
    except ValueError:
        return None
    if candidate > now:
        year -= 1
        try:
            candidate = date(year, month, day)
        except ValueError:
            return None
    return candidate.isoformat()  # "YYYY-MM-DD"


def filename_to_iso(filename: str | Path) -> Optional[str]:
    """Extract a date from a slide/news filename and return ISO string.

    Handles both formats found in the codebase:
    - ``MMDD``       → ``"YYYY-MM-DD"`` (update_news_archive.py pattern)
    - ``YYYYMMDD``   → ``"YYYY-MM-DD"`` (day_news_slide_generator.py pattern)
    - ``day_slide_YYYY_MM_DD.html`` → ``"YYYY-MM-DD"`` (slide filenames)

    Args:
        filename: Filename string or Path (basename used; extension ignored).

    Returns:
        ISO date string, or ``None`` if unrecognised.
    """
    stem = Path(filename).stem  # strips extension

    # day_slide_YYYY_MM_DD or auto_daily_report_YYYY_MM_DD patterns
    m = re.search(r"(\d{4})[_-](\d{2})[_-](\d{2})", stem)
    if m:
        try:
            date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        except ValueError:
            pass

    # YYYYMMDD prefix (e.g. "20250826")
    m8 = _YYYYMMDD_RE.match(stem)
    if m8:
        try:
            date(int(m8.group(1)), int(m8.group(2)), int(m8.group(3)))
            return f"{m8.group(1)}-{m8.group(2)}-{m8.group(3)}"
        except ValueError:
            pass

    # Plain MMDD (e.g. "0913", "0913-extra")
    return mmdd_to_iso(stem)


# ---------------------------------------------------------------------------
# Convenience wrappers (replace repeated strftime calls)
# ---------------------------------------------------------------------------

def today_mmdd(ref: date | None = None) -> str:
    """Return today's date as ``"MMDD"`` (e.g. ``"0613"``).

    Replaces: ``date.today().strftime("%m%d")``
    Found in: src/auto_collect/main.py:72, html_report.py:531,
              report_generator.py:112.
    """
    return (ref or date.today()).strftime("%m%d")


def today_iso(ref: date | None = None) -> str:
    """Return today's date as ``"YYYY-MM-DD"`` (e.g. ``"2026-06-13"``).

    Replaces: ``date.today().isoformat()`` / ``strftime('%Y-%m-%d')``
    """
    return (ref or date.today()).isoformat()


def now_jst_str() -> str:
    """Return current JST datetime as human-readable string ``"YYYY-MM-DD HH:MM JST"``.

    Replaces: ``datetime.now().strftime("%Y-%m-%d %H:%M JST")``
    Found in: src/auto_collect/html_report.py:248.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M JST")


def iso_to_japanese(iso: str) -> str:
    """Convert ``"YYYY-MM-DD"`` to Japanese date string ``"YYYY年MM月DD日"``.

    Replaces repeated ``strftime("%Y年%m月%d日")`` calls found in
    report_generator.py:177-178, generate_ranking_latest.py:120-121,144-146.

    Args:
        iso: Date string in ``"YYYY-MM-DD"`` format.

    Returns:
        e.g. ``"2026年06月13日"``.

    Raises:
        ValueError: if *iso* cannot be parsed.
    """
    d = date.fromisoformat(iso)
    return f"{d.year}年{d.month:02d}月{d.day:02d}日"


if __name__ == "__main__":
    from datetime import date as _date
    ref = _date(2026, 6, 14)
    assert mmdd_to_iso("0913", ref=ref)[5:] == "09-13", "mmdd_to_iso month-day check failed"
    assert mmdd_to_iso("1231", ref=ref) == "2025-12-31", "rollback-year check failed"
    assert filename_to_iso("day_slide_2026_06_13.html") == "2026-06-13", "filename_to_iso slide check failed"
    assert iso_to_japanese("2026-06-13") == "2026年06月13日", "iso_to_japanese check failed"
    print("dates.py self-test ok")
