#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any

try:
    from ftfy import fix_text  # type: ignore
except Exception:
    def fix_text(s: str) -> str:
        return s

import html as _html
import re as _re

ROOT = Path(__file__).resolve().parents[1]
NEWS_DIR = ROOT / 'public-pages' / 'news'


def clean_text(s: str | None) -> str:
    if not s:
        return ''
    t = fix_text(str(s))
    t = _html.unescape(_html.unescape(t))
    t = _re.sub(r'<[^>]+>', ' ', t)
    t = t.replace('\uFFFD', '')
    t = _re.sub(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])', '', t)
    t = _re.sub(r'[\u00A0\u2000-\u200B\u3000]', ' ', t)
    # remove PUA and common Latin-1 mojibake remnants
    t = _re.sub(r'[\uE000-\uF8FF]', '', t)
    t = _re.sub(r'[ÃãÂ¢€]', '', t)
    # remove common SJIS mojibake tokens seen in this project
    t = _re.sub(r'[郢邵隴陝鬯髫鬩縺繝繧]', '', t)
    t = _re.sub(r'(蟷ｴ|譛|譌|・ｽ|窶ｦ)', '', t)
    t = _re.sub(r'\s+', ' ', t).strip()
    return t


def norm_date(s: str | None) -> str:
    if not s:
        return ''
    m = _re.search(r'(\d{4})[./-]?(\d{1,2})[./-]?(\d{1,2})', s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return s


def normalize_file(path: Path) -> bool:
    try:
        data: Dict[str, Any] = json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"[skip] {path}: {e}")
        return False
    if not isinstance(data, dict):
        # index files and other list-shaped payloads carry no item text
        print('[skip]', path, '(non-dict payload)')
        return False
    changed = False
    items = data.get('items', []) or []
    for it in items:
        for k in ('title', 'summary'):
            new = clean_text(it.get(k, ''))
            if new != it.get(k, ''):
                it[k] = new; changed = True
        it['points'] = [clean_text(p) for p in (it.get('points') or [])]
        nd = norm_date(clean_text(it.get('date', '')))
        if nd != it.get('date', ''):
            it['date'] = nd; changed = True
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print('[fix] ', path)
    else:
        print('[ok ] ', path)
    return changed


def main() -> int:
    if not NEWS_DIR.exists():
        print('news dir not found', NEWS_DIR)
        return 1
    any_changed = False
    skip = {'archive_index.json', 'daily_index.json', 'version.json', 'search_index.json'}
    for p in sorted(NEWS_DIR.glob('*.json')):
        if p.name in skip:
            continue
        any_changed |= normalize_file(p)
    return 0 if not any_changed else 0


if __name__ == '__main__':
    sys.exit(main())
