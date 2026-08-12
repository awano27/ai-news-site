#!/usr/bin/env python3
"""
Refreshes "latest" aliases of presentation reports so that integrated_report.html
can always embed the newest pages without hardcoding dates.

It finds the newest files by date in filename. Patterns:
  - presentations/ai_ranking_report_YYYYMMDD.html -> ai_ranking_report_latest.html
  - presentations/daily_ai_news_report_YYYYMMDD.html -> daily_ai_news_report_latest.html
  - presentations/advanced_intelligence_report_YYYYMMDD.html -> advanced_intelligence_report_latest.html

Run locally or in CI (GitHub Actions). Safe to run repeatedly; only updates when needed.
"""

from __future__ import annotations
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PRES = ROOT / 'presentations'

PATTERNS = [
    ('ai_ranking_report_(\d{8})\.html', 'ai_ranking_report_latest.html'),
    ('daily_ai_news_report_(\d{8})\.html', 'daily_ai_news_report_latest.html'),
    ('advanced_intelligence_report_(\d{8})\.html', 'advanced_intelligence_report_latest.html'),
]

def newest_by_pattern(pattern: str) -> Path | None:
    rx = re.compile(f'^{pattern}$')
    cands = []
    for p in PRES.glob('*.html'):
        m = rx.match(p.name)
        if not m:
            continue
        ymd = m.group(1)
        cands.append((ymd, p))
    if not cands:
        return None
    # Sort by yyyymmdd (string order works), pick the latest
    cands.sort(key=lambda x: x[0])
    return cands[-1][1]


def rewrite_alias_canonical(html: str, source_name: str, latest_name: str) -> str:
    """Point canonical/og:url at the alias itself, not the dated source page."""
    src = f'https://visionhub.jp/presentations/{source_name}'
    dst = f'https://visionhub.jp/presentations/{latest_name}'
    return html.replace(src, dst)

def files_differ(a: Path, b: Path) -> bool:
    try:
        return a.read_bytes() != b.read_bytes()
    except Exception:
        return True

def main() -> int:
    if not PRES.exists():
        print('[presentations] directory not found:', PRES)
        return 1

    changed = False
    for patt, latest_name in PATTERNS:
        newest = newest_by_pattern(patt)
        if not newest:
            print(f'- skip: no match for {patt}')
            continue
        target = PRES / latest_name
        html = newest.read_text(encoding='utf-8', errors='ignore')
        html = rewrite_alias_canonical(html, newest.name, latest_name)
        need = (not target.exists()) or (target.read_text(encoding='utf-8', errors='ignore') != html)
        if need:
            target.write_text(html, encoding='utf-8')
            changed = True
            print(f'+ updated: {latest_name} -> {newest.name}')
        else:
            print(f'= up-to-date: {latest_name} -> {newest.name}')

    return 0 if changed else 0

if __name__ == '__main__':
    sys.exit(main())

