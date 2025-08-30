#!/usr/bin/env python3
"""
Scan presentations/day_slides and emit a machine-readable list at
presentations/day_slides/list.json for clients to build navigation.

Each entry: { "date": "YYYY-MM-DD", "url": "day_slides/day_slide_YYYY_MM_DD.html", "label": "M/D - Title?" }
Title is optional; we derive a short label M/D if not found.
"""
from __future__ import annotations

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DAY_DIR = ROOT / 'presentations' / 'day_slides'
OUT = DAY_DIR / 'list.json'

TITLE_RE = re.compile(r'<h2[^>]*class="slide-title"[^>]*>(.*?)</h2>', re.I|re.S)

def extract_title(html: str) -> str|None:
    m = TITLE_RE.search(html)
    if not m:
        return None
    # Strip tags if any inside
    title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return title or None

def main() -> int:
    DAY_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for p in DAY_DIR.glob('day_slide_*.html'):
        m = re.match(r'day_slide_(\d{4})_(\d{2})_(\d{2})\.html$', p.name)
        if not m:
            continue
        y, mth, d = m.groups()
        date = f"{y}-{mth}-{d}"
        try:
            html = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            html = ''
        title = extract_title(html) or 'AI News'
        label = f"{int(mth)}/{int(d)} - {title[:24]}"  # short label
        items.append({
            'date': date,
            'url': f'day_slides/{p.name}',
            'label': label
        })
    # Sort desc by date
    items.sort(key=lambda x: x['date'], reverse=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
    print('wrote', OUT, len(items))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

