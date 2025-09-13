#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

P = Path('presentations/day_slides/day_slide_2025_09_10.html')

def main() -> int:
    if not P.exists():
        print('not found')
        return 1
    s = P.read_text(encoding='utf-8', errors='ignore')
    if "class='sources-section' id='sources'" in s or 'id=\'sources\'' in s:
        print('already')
        return 0
    if "<div class='sources-section'>" in s:
        s = s.replace("<div class='sources-section'>", "<div class='sources-section' id='sources'>", 1)
        P.write_text(s, encoding='utf-8')
        print('patched')
        return 0
    print('nochange')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

