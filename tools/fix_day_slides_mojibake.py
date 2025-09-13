#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch-fix common mojibake patterns in presentations/day_slides/*.html.
- Repairs corrupted closing tags like `E/h2>` -> `</h2>`
- Normalizes Japanese date like `2025年09朁E2日` -> `2025年09月02日`
- Removes replacement characters (U+FFFD)
- Keeps file content/style otherwise intact
"""

from __future__ import annotations
from pathlib import Path
import re

DAY_SLIDES_DIR = Path('presentations/day_slides')

# files to skip (already good or variants)
SKIP_SUFFIXES = (
    '_fixed.html', '_clean.html', '_reveal.html', '_detailed.html', '_base.html'
)

# regexes
RE_BAD_CLOSER = re.compile(r'E\/(h[1-6]|div|span|p|button|section|small|strong|em|a|li|ul|ol)>', re.I)
RE_EBR = re.compile(r'Ebr>', re.I)
RE_FFFD = re.compile('\uFFFD')  # replacement char
RE_DATE = re.compile(r'(\d{4})年0?(\d{1,2})朁E0?(\d{1,2})日')
# patterns where 年/月/日 became U+FFFD sequences like "2025�N08��01��"
RE_DATE_FFFD_FULL = re.compile(r'(\d{4})\uFFFDN0?(\d{1,2})\uFFFD\uFFFD0?(\d{1,2})\uFFFD\uFFFD')
RE_DATE_FFFD_YM = re.compile(r'(\d{4})\uFFFDN0?(\d{1,2})\uFFFD\uFFFD')

# targeted text fixes seen across slides (safe, unambiguous)
REPLACEMENTS = {
    'ト�Eクン': 'トークン',
    'MiniCPM?V': 'MiniCPM‑V',
}

def fix_text(s: str) -> str:
    # structural fixes first
    s = RE_BAD_CLOSER.sub(lambda m: f'</{m.group(1)}>', s)
    s = RE_EBR.sub('<br>', s)

    # date normalization: 年..朁E..日 -> 年..月..日
    def _date_repl(m: re.Match) -> str:
        y = m.group(1)
        mm = f"{int(m.group(2)):02d}"
        dd = f"{int(m.group(3)):02d}"
        return f"{y}年{mm}月{dd}日"
    s = RE_DATE.sub(_date_repl, s)
    # Fix FFFD-based date patterns before stripping FFFD
    s = RE_DATE_FFFD_FULL.sub(lambda m: f"{m.group(1)}年{int(m.group(2)):02d}月{int(m.group(3)):02d}日", s)
    s = RE_DATE_FFFD_YM.sub(lambda m: f"{m.group(1)}年{int(m.group(2)):02d}月", s)

    # finally remove any remaining replacement chars
    s = RE_FFFD.sub('', s)

    # simple word-level safe replacements
    for k, v in REPLACEMENTS.items():
        s = s.replace(k, v)

    return s

def main() -> int:
    changed = []
    for p in sorted(DAY_SLIDES_DIR.glob('day_slide_*.html')):
        if p.name.endswith(SKIP_SUFFIXES):
            continue
        orig = p.read_text(encoding='utf-8', errors='ignore')
        fixed = fix_text(orig)
        if fixed != orig:
            p.write_text(fixed, encoding='utf-8', newline='\n')
            changed.append(p)
    if changed:
        print('Fixed files:')
        for c in changed:
            print('  ', c)
    else:
        print('No changes made.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
