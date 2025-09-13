#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / 'public-pages' / 'news'


def main() -> int:
    idx_path = DIR / 'archive_index.json'
    if not idx_path.exists():
        print('archive_index.json not found')
        return 1
    idx = json.loads(idx_path.read_text(encoding='utf-8'))
    seen = set()
    rdate = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    ok = True
    for en in idx:
        d = en.get('date','')
        if not rdate.match(d):
            print('[date-format] invalid:', d)
            ok = False
        if d in seen:
            print('[duplicate] date duplicated in index:', d)
            ok = False
        seen.add(d)
        jf = DIR / en.get('file','')
        if not jf.exists():
            print('[missing] file missing:', jf)
            ok = False
            continue
        data = json.loads(jf.read_text(encoding='utf-8'))
        if data.get('date') != d:
            print('[mismatch] top-level date mismatch:', jf, data.get('date'), '!=', d)
            ok = False
        for it in data.get('items', []):
            s = it.get('date','')
            if s and not rdate.match(s):
                print('[item-date] suspicious date in', jf.name, ':', s)
                ok = False
            t = str(it.get('title',''))
            if any(tok in t for tok in ('郢','邵','隴','陷','蟷ｴ','譌')):
                print('[mojibake] title contains mojibake-like tokens in', jf.name)
                ok = False
    if not ok:
        print('Validation failed.')
        return 2
    print('Validation OK.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

