"""
html_report_archive.py — Rebuild the archive index for daily HTML reports.

Extracted from html_report.py; the orchestrator re-exports the symbols.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from .config import PROJECT_ROOT

ARCHIVE_DIR = PROJECT_ROOT / "presentations" / "daily_reports"
ARCHIVE_INDEX_PATH = ARCHIVE_DIR / "index.json"
SEARCHABLE_INDEX_PATH = ARCHIVE_DIR / "searchable.json"

_ARCHIVE_FILE_RE = re.compile(r"^auto_daily_report_(\d{4})_(\d{2})_(\d{2})\.html$")
_TOTAL_META_RE = re.compile(r'<meta name="report:total" content="(\d+)"')
_HIGH_META_RE = re.compile(r'<meta name="report:high" content="(\d+)"')
_ROW_TITLE_RE = re.compile(r'<span class="row-title">([^<]+)</span>')


def rebuild_archive_index() -> int:
    """Rescan ARCHIVE_DIR and rewrite both index.json and searchable.json.

    `index.json` keeps the existing tiny shape (date+file+count) consumed by
    `daily_reports_archive.html`. `searchable.json` is the richer payload
    used by the in-browser full-text search added in Phase 4 — it carries
    per-report totals and the list of headline titles.
    """
    index_reports = []
    search_reports = []
    for p in sorted(ARCHIVE_DIR.glob("auto_daily_report_*.html")):
        m = _ARCHIVE_FILE_RE.match(p.name)
        if not m:
            continue
        iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        index_reports.append({"date": iso, "file": p.name})

        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        total_m = _TOTAL_META_RE.search(text)
        high_m = _HIGH_META_RE.search(text)
        titles = [t.strip() for t in _ROW_TITLE_RE.findall(text) if t.strip()]
        search_reports.append(
            {
                "date": iso,
                "file": p.name,
                "total": int(total_m.group(1)) if total_m else len(titles),
                "high": int(high_m.group(1)) if high_m else 0,
                "titles": titles[:50],
            }
        )

    index_reports.sort(key=lambda r: r["date"], reverse=True)
    search_reports.sort(key=lambda r: r["date"], reverse=True)

    ARCHIVE_INDEX_PATH.write_text(
        json.dumps(
            {
                "generated": date.today().isoformat(),
                "source": "presentations/daily_reports/",
                "count": len(index_reports),
                "reports": index_reports,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    SEARCHABLE_INDEX_PATH.write_text(
        json.dumps(
            {
                "generated": date.today().isoformat(),
                "count": len(search_reports),
                "reports": search_reports,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return len(index_reports)
