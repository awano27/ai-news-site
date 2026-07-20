#!/usr/bin/env python3
"""
Fix mojibake in presentations/day_slides/*.html by applying sanitize_html and
removing typical stray artifacts (U+FFFD and ASCII 'E' inserted between
non-ASCII characters).

This script is idempotent and safe to run multiple times. It only writes files
when changes occur.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

# Local import (repo path)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.sanitize import sanitize_html  # type: ignore


RE_E_BETWEEN_NONASCII = re.compile(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])')


def repair_text(html: str) -> str:
    out = sanitize_html(html)
    # Remove replacement chars (�)
    out = out.replace('\uFFFD', '')
    # Remove stray 'E' between non-ASCII chars
    out = RE_E_BETWEEN_NONASCII.sub('', out)
    return out


def main() -> int:
    day_dir = ROOT / 'presentations' / 'day_slides'
    if not day_dir.exists():
        print('no day_slides directory')
        return 0
    changed = 0
    for p in sorted(day_dir.glob('day_slide_*.html')):
        try:
            raw = p.read_text(encoding='utf-8', errors='replace')
            fixed = repair_text(raw)
            if fixed != raw:
                p.write_text(fixed, encoding='utf-8')
                changed += 1
                print('+ fixed', p.name)
        except Exception as ex:
            print('! error', p, ex)
    print('changed files:', changed)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

