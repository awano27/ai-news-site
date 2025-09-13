#!/usr/bin/env python3
"""
Quick repair for mojibake/double-encoded sequences and broken closing tags
in the published index.html. This is a stopgap for static output only.

What it does:
- Fixes sequences like "E/span>" -> "</span>" (and div, p, button, h1-h6)
- Decodes patterns like "＆amp;＃32;" or "&amp;#32;" to the correct Unicode character

Usage:
  python public-pages/tools/repair_index.py
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'

def decode_weird_numeric_entities(text: str) -> str:
    # Match either ASCII '&' or fullwidth '＆' (U+FF06), and ASCII '#' or fullwidth '＃' (U+FF03)
    pattern = re.compile(r'([&\uFF06])amp;([#\uFF03])(\d+);')

    def repl(m: re.Match) -> str:
        try:
            codepoint = int(m.group(3))
            return chr(codepoint)
        except Exception:
            return ' '

    return pattern.sub(repl, text)

def fix_broken_closing_tags(text: str) -> str:
    # Replace E/<tag> -> </tag>
    tags = ['span','div','button','p','h1','h2','h3','h4','h5','h6']
    for t in tags:
        text = re.sub(fr'E\/{t}>', f'</{t}>', text)
    return text

def main():
    if not INDEX.exists():
        print(f"Not found: {INDEX}")
        return 1

    original = INDEX.read_text(encoding='utf-8', errors='replace')
    fixed = original

    fixed = fix_broken_closing_tags(fixed)
    fixed = decode_weird_numeric_entities(fixed)

    if fixed != original:
        backup = INDEX.with_suffix('.html.bak')
        backup.write_text(original, encoding='utf-8')
        INDEX.write_text(fixed, encoding='utf-8')
        print(f"Repaired. Backup saved to {backup.name}")
    else:
        print("No changes made.")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

