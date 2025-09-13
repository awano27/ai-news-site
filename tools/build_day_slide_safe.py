#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path so 'src.*' imports work
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.generators.day_news_slide_generator import DayNewsSlideGenerator
from src.utils.sanitize import sanitize_html
from tools.mojibake_guard import load_rules, sanitize_and_enforce


def build_for(date_mmdd: str) -> Path:
    # mmdd like '0906' -> input file path
    in_path = Path(r'C:/Users/yoshitaka/input/day') / f'{date_mmdd}.txt'
    if not in_path.exists():
        raise SystemExit(f'Input not found: {in_path}')
    gen = DayNewsSlideGenerator()
    data = gen.parse_day_file(in_path)
    html = gen.generate_slide(data)
    html = sanitize_html(html)
    rules = load_rules()
    html_fixed, info = sanitize_and_enforce(html, rules)
    if info['has_mojibake']:
        print(f"[warn] mojibake-like tokens detected: {info['token_counts']}")
    out = Path('presentations/day_slides') / f"day_slide_{data['date'].replace('-', '_')}.html"
    out.write_text(html_fixed, encoding='utf-8')
    print(f'Wrote: {out}')
    return out


def main():
    if len(sys.argv) != 2 or len(sys.argv[1]) != 4 or not sys.argv[1].isdigit():
        print('Usage: python tools/build_day_slide_safe.py MMDD')
        sys.exit(1)
    build_for(sys.argv[1])


if __name__ == '__main__':
    main()
