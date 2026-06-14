"""
src/utils/paths.py — Canonical path constants for the AI-news-site repo.

Single source of truth for all directory/file paths that are currently
hardcoded in ~8 different places across src/, scripts/, script/, and root *.py.

All constants are absolute ``pathlib.Path`` objects anchored to ``PROJECT_ROOT``.
``PROJECT_ROOT`` follows the same resolution order as ``src/auto_collect/config.py``:
  1. ``PROJECT_ROOT`` env var (lets CI/CD workflows pin a path)
  2. Four levels up from this file (src/utils/paths.py → repo root)

Usage
-----
    from src.utils.paths import (
        PROJECT_ROOT,
        NEWS_DIR,
        PUBLIC_NEWS_DIR,
        DAY_SLIDES_DIR,
        INPUT_DAY_DIR,
        DAILY_NEWS_DIR,
        DAILY_REPORTS_DIR,
        slide_html_path,
        news_json_path,
    )
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# Root resolution
# ---------------------------------------------------------------------------

_env_root = os.environ.get("PROJECT_ROOT")
if _env_root:
    PROJECT_ROOT: Path = Path(_env_root).resolve()
else:
    # src/utils/paths.py  →  src/utils  →  src  →  repo root
    PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Core directory constants
# (Each constant documents the file(s) it consolidates)
# ---------------------------------------------------------------------------

# Raw daily text inputs: input/day/MMDD.txt
# Previously hardcoded in:
#   update_news_archive.py:107  "input/day"
#   src/auto_collect/config.py:16  PROJECT_ROOT / "input" / "day"
#   src/generators/day_news_slide_generator.py:392  Path("input/day")
#   scripts/create_daily_slide.py:19  f"input/day/{date_mmdd}.txt"
INPUT_DAY_DIR: Path = PROJECT_ROOT / "input" / "day"

# Processed news JSON: news/YYYY-MM-DD.json
# Previously hardcoded in:
#   script/build_news.py:23  os.path.join(ROOT, 'news')
#   scripts/generate_ranking_input.py:35  REPO_ROOT / "news"
NEWS_DIR: Path = PROJECT_ROOT / "news"

# Versioned/public archive: public-pages/news/
# Previously hardcoded in:
#   update_news_archive.py:108  Path("public-pages/news")
#   src/auto_collect/report_generator.py:26  PROJECT_ROOT / "public-pages" / "news"
PUBLIC_NEWS_DIR: Path = PROJECT_ROOT / "public-pages" / "news"

# Day slides HTML: presentations/day_slides/
# Previously hardcoded in:
#   script/build_day_slides_json.py:16  ROOT / 'presentations' / 'day_slides'
#   src/generators/day_news_slide_generator.py:21  Path("presentations/day_slides")
#   scripts/create_daily_slide.py:162  f"presentations/day_slides/day_slide_2026_{month}_{day}.html"
DAY_SLIDES_DIR: Path = PROJECT_ROOT / "presentations" / "day_slides"

# Daily news timeline page: daily-news/
# Previously hardcoded in:
#   src/auto_collect/daily_news_page.py:30  PROJECT_ROOT / "daily-news"
#   scripts/build_sitemap.py:46  "daily-news"
DAILY_NEWS_DIR: Path = PROJECT_ROOT / "daily-news"

# Auto-generated daily HTML reports: presentations/daily_reports/
# Previously hardcoded in:
#   src/auto_collect/html_report.py:449  PROJECT_ROOT / "presentations" / "daily_reports"
DAILY_REPORTS_DIR: Path = PROJECT_ROOT / "presentations" / "daily_reports"

# Public API output for auto-daily-report JSON
# Previously hardcoded in:
#   src/auto_collect/html_report.py:23  PROJECT_ROOT / "public-pages" / "api" / "auto_daily_report"
PUBLIC_AUTO_REPORT_DIR: Path = PROJECT_ROOT / "public-pages" / "api" / "auto_daily_report"

# Jinja2 / HTML templates
# Previously hardcoded as Path("templates") in:
#   src/generators/day_news_slide_generator.py:25
TEMPLATES_DIR: Path = PROJECT_ROOT / "templates"

# Log output directory
LOG_DIR: Path = PROJECT_ROOT / "logs" / "auto_collect"

# archive_index.json used by multiple consumers
ARCHIVE_INDEX_FILE: Path = PUBLIC_NEWS_DIR / "archive_index.json"

# version.json used by update_news_archive.py
VERSION_FILE: Path = PUBLIC_NEWS_DIR / "version.json"


# ---------------------------------------------------------------------------
# Path-builder helpers (reduce f-string duplication in callers)
# ---------------------------------------------------------------------------

def news_json_path(iso_date: str) -> Path:
    """Return absolute path for ``news/YYYY-MM-DD.json``.

    Args:
        iso_date: Date in ``"YYYY-MM-DD"`` format.

    Example:
        >>> news_json_path("2026-06-13")
        PosixPath('.../news/2026-06-13.json')
    """
    return NEWS_DIR / f"{iso_date}.json"


def public_news_json_path(iso_date: str) -> Path:
    """Return absolute path for ``public-pages/news/YYYY-MM-DD.json``."""
    return PUBLIC_NEWS_DIR / f"{iso_date}.json"


def slide_html_path(iso_date: str) -> Path:
    """Return absolute path for ``presentations/day_slides/day_slide_YYYY_MM_DD.html``.

    Args:
        iso_date: Date in ``"YYYY-MM-DD"`` format.

    Example:
        >>> slide_html_path("2026-06-13")
        PosixPath('.../presentations/day_slides/day_slide_2026_06_13.html')
    """
    y, m, d = iso_date.split("-")
    return DAY_SLIDES_DIR / f"day_slide_{y}_{m}_{d}.html"


def slide_images_dir(mmdd: str) -> Path:
    """Return absolute path for ``presentations/day_slides/images/MMDD/``.

    Args:
        mmdd: 4-character string like ``"0613"``.
    """
    return DAY_SLIDES_DIR / "images" / mmdd


def input_day_txt(mmdd: str) -> Path:
    """Return absolute path for ``input/day/MMDD.txt``."""
    return INPUT_DAY_DIR / f"{mmdd}.txt"


def daily_report_html_path(iso_date: str) -> Path:
    """Return absolute path for ``presentations/daily_reports/auto_daily_report_YYYY_MM_DD.html``.

    Replaces the f-string construction in src/auto_collect/html_report.py:559.
    """
    y, m, d = iso_date.split("-")
    return DAILY_REPORTS_DIR / f"auto_daily_report_{y}_{m}_{d}.html"


def ensure_dirs(*dirs: Path) -> None:
    """Create *dirs* (and parents) if they do not exist.

    Convenience wrapper replacing ``Path.mkdir(parents=True, exist_ok=True)``
    scattered across callers.
    """
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
