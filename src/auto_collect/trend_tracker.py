"""Tag today's stories as new vs continuing relative to the most recent archive.

Used by `html_report.py` to render `🆕 NEW` / `🔁 継続` badges. The comparison
is intentionally lightweight: load the most recent archive HTML, extract its
`.row-title` strings, and fuzzy-match against today's titles with
`difflib.SequenceMatcher`. No DB, no embeddings.
"""

from __future__ import annotations

import difflib
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .config import PROJECT_ROOT

ARCHIVE_DIR = PROJECT_ROOT / "presentations" / "daily_reports"
_FILE_RE = re.compile(r"auto_daily_report_(\d{4})_(\d{2})_(\d{2})\.html")
_TITLE_RE = re.compile(r'<span class="row-title">([^<]+)</span>')


def _previous_titles(today_iso: str) -> Set[str]:
    if not ARCHIVE_DIR.exists():
        return set()
    candidates: List[Tuple[str, Path]] = []
    for p in ARCHIVE_DIR.glob("auto_daily_report_*.html"):
        m = _FILE_RE.match(p.name)
        if not m:
            continue
        iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if iso >= today_iso:
            continue
        candidates.append((iso, p))
    if not candidates:
        return set()
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, latest_path = candidates[0]
    try:
        text = latest_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return set()
    return {t.strip() for t in _TITLE_RE.findall(text) if t.strip()}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def classify(today_titles: List[str], today_iso: str = None, threshold: float = 0.6) -> Dict[str, str]:
    """Map each title → 'new' or 'continuing'.

    threshold is the SequenceMatcher ratio above which a title is treated as
    a continuation of yesterday's coverage. 0.6 catches paraphrased coverage
    while letting genuinely new stories through.
    """
    today_iso = today_iso or date.today().isoformat()
    prev = list(_previous_titles(today_iso))
    if not prev:
        return {t: "new" for t in today_titles}
    prev_norm = [_norm(p) for p in prev]
    out: Dict[str, str] = {}
    for t in today_titles:
        n = _norm(t)
        if not n:
            out[t] = "new"
            continue
        if n in prev_norm:
            out[t] = "continuing"
            continue
        best = max(
            (difflib.SequenceMatcher(None, n, p).ratio() for p in prev_norm),
            default=0.0,
        )
        out[t] = "continuing" if best >= threshold else "new"
    return out


def recent_counts(today_iso: str = None, days: int = 7) -> List[Dict[str, object]]:
    """Return last `days` daily article counts for the trend chart.

    Reads `<meta name="report:total">` from each archive HTML. Falls back to
    counting `<div class="row">` if the meta tag is missing (older archives).
    Result is oldest-first so the chart reads left → right chronologically.
    """
    today_iso = today_iso or date.today().isoformat()
    if not ARCHIVE_DIR.exists():
        return []
    rows: List[Tuple[str, int]] = []
    meta_re = re.compile(r'<meta name="report:total" content="(\d+)"')
    row_re = re.compile(r'<div class="row">')
    for p in ARCHIVE_DIR.glob("auto_daily_report_*.html"):
        m = _FILE_RE.match(p.name)
        if not m:
            continue
        iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if iso > today_iso:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        meta_m = meta_re.search(text)
        if meta_m:
            count = int(meta_m.group(1))
        else:
            count = len(row_re.findall(text))
        rows.append((iso, count))
    rows.sort(key=lambda x: x[0])
    rows = rows[-days:]
    return [{"date": iso, "count": cnt} for iso, cnt in rows]
