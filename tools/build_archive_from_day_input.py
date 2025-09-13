#!/usr/bin/env python3
from __future__ import annotations

import re
import json
from pathlib import Path
from datetime import date
from typing import List, Dict

try:
    from ftfy import fix_text  # type: ignore
except Exception:
    def fix_text(s: str) -> str:
        return s

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = Path(r'C:/Users/yoshitaka/input/day')
OUT_DIR = ROOT / 'public-pages' / 'news'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(s: str | None) -> str:
    if not s:
        return ''
    t = fix_text(str(s))
    # strip HTML tags if any
    t = re.sub(r'<[^>]+>', ' ', t)
    # remove PUA and common artifacts (defensive)
    t = re.sub(r'[\uE000-\uF8FF]', '', t)
    t = re.sub(r'[ÃãÂ¢€]', '', t)
    t = re.sub(r'[郢邵隴陝鬯髫鬩縺繝繧]', '', t)
    t = re.sub(r'(蟷ｴ|譛|譌|・ｽ|窶ｦ)', '', t)
    t = re.sub(r'[\u00A0\u2000-\u200B\u3000]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def split_sentences(text: str) -> List[str]:
    # simple Japanese sentence split by 。！？ with fallback to lines
    s = re.split(r'[。！？!?]\s*', text)
    out = [clean_text(x) for x in s if clean_text(x)]
    if not out:
        out = [clean_text(x) for x in text.splitlines() if clean_text(x)]
    return out


def extract_urls(text: str) -> List[str]:
    rx = re.compile(r'https?://[^\s<>"\)]+')
    urls = rx.findall(text)
    # de-dup keep order
    seen = set(); out = []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out


def build_one(mmdd: str, year: int = 2025) -> Path:
    assert len(mmdd) == 4 and mmdd.isdigit()
    src = IN_DIR / f'{mmdd}.txt'
    if not src.exists():
        raise SystemExit(f'Input not found: {src}')
    raw = src.read_bytes()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('cp932', errors='ignore')
    text = fix_text(text)

    # derive date
    m = int(mmdd[:2]); d = int(mmdd[2:])
    day = date(year, m, d)
    iso = day.isoformat()

    # heuristics: first non-empty line is title; next paragraph as summary
    lines = [x.strip() for x in text.splitlines()]
    nonempty = [x for x in lines if x]
    title = clean_text(nonempty[0]) if nonempty else f'Daily AI News {iso}'

    # summary: first paragraph (first ~280 chars)
    paragraphs = [p for p in re.split(r'\n\s*\n+', text) if clean_text(p)]
    sumtext = clean_text(paragraphs[1] if len(paragraphs) > 1 else (paragraphs[0] if paragraphs else ''))
    summary = sumtext[:280]

    # points: first 3 sentences
    points = split_sentences(text)[:3]

    # urls
    urls = extract_urls(text)
    links = [{ 'href': u, 'text': '' } for u in urls[:5]]

    item: Dict = {
        'title': title,
        'score': 80,
        'rank': 1,
        'url': urls[0] if urls else '',
        'date': iso,
        'summary': summary,
        'points': points,
        'links': links,
    }

    out_path = OUT_DIR / f'{iso}.json'
    data = {
        'date': iso,
        'source': str(src),
        'count': 1,
        'items': [item],
    }
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    # update archive index
    idx_path = OUT_DIR / 'archive_index.json'
    index = []
    if idx_path.exists():
        try:
            index = json.loads(idx_path.read_text(encoding='utf-8'))
        except Exception:
            index = []
    # remove existing iso
    index = [x for x in index if x.get('date') != iso]
    index.append({'date': iso, 'file': f'{iso}.json', 'count': 1})
    index.sort(key=lambda x: x['date'], reverse=True)
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')

    print('WROTE', out_path)
    return out_path


def main(argv=None):
    import sys
    args = sys.argv[1:]
    if not args:
        print('Usage: python tools/build_archive_from_day_input.py MMDD [MMDD ...]')
        return 1
    code = 0
    for mmdd in args:
        try:
            build_one(mmdd)
        except SystemExit as e:
            print(e)
            code = 2
    return code


if __name__ == '__main__':
    raise SystemExit(main())

