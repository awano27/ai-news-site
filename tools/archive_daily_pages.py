#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch daily AI news page from awano27.github.io/daily-ai-news-pages,
store HTML snapshot and parsed JSON into public-pages, and update archive_index.json.
"""
import re
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
except Exception:
    print('ERROR: requests is required')
    sys.exit(1)

BASE_URL = 'https://awano27.github.io/daily-ai-news-pages/'
OUT_HTML_DIR = Path('public-pages/daily')
OUT_JSON_DIR = Path('public-pages/news')
IDX_PATH = OUT_JSON_DIR / 'archive_index.json'

HTML_RE = re.compile(r'<article class="card">(.*?)</article>', re.S)
TITLE_RE = re.compile(r'<a[^>]*class="card-title"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
SUM_RE = re.compile(r'<p[^>]*class="card-summary"[^>]*>(.*?)</p>', re.S)
UPDATED_RE = re.compile(r'最新|更新|Updated[^<]*:\s*([0-9\-: ]+)', re.I)
DATE_RE = re.compile(r'(20\d{2})[-/\.](\d{1,2})[-/\.](\d{1,2})')


def clean_html_text(s: str) -> str:
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&quot;|&#39;', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # remove stray 'E' between multibyte (simple heuristic)
    s = re.sub(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])', '', s)
    return s


def fetch_html(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    # trust UTF-8; fallback
    r.encoding = 'utf-8'
    return r.text


def parse_items(html: str):
    items = []
    for m in HTML_RE.finditer(html):
        block = m.group(1)
        mt = TITLE_RE.search(block)
        if not mt:
            continue
        href = mt.group(1).strip()
        title = clean_html_text(mt.group(2))
        ms = SUM_RE.search(block)
        summary = clean_html_text(ms.group(1)) if ms else ''
        items.append({
            'title': title,
            'url': href,
            'summary': summary,
            'rank': None,
            'score': None,
            'date': None,
        })
    return items


def guess_date(html: str) -> str:
    # Try to find YYYY-MM-DD in page
    m = DATE_RE.search(html)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return datetime.now().strftime('%Y-%m-%d')


def write_snapshot(date_str: str, html: str):
    OUT_HTML_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_HTML_DIR / f"{date_str}.html"
    p.write_text(html, encoding='utf-8')
    return p


def write_json(date_str: str, items):
    OUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    name = f"daily-{date_str}.json"
    data = {
        'date': date_str,
        'source': BASE_URL,
        'count': len(items),
        'items': [
            {
                'title': it['title'],
                'score': it.get('score'),
                'rank': it.get('rank'),
                'url': it['url'],
                'date': date_str,
                'summary': it.get('summary', ''),
                'points': [],
                'links': [{'href': it['url'], 'text': ''}] if it.get('url') else [],
            } for it in items
        ]
    }
    (OUT_JSON_DIR / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return name, data


def update_index(entry):
    entries = []
    if IDX_PATH.exists():
        try:
            entries = json.loads(IDX_PATH.read_text(encoding='utf-8'))
        except Exception:
            entries = []
    # de-dup by file
    existing_files = {e.get('file') for e in entries}
    if entry['file'] not in existing_files:
        entries.insert(0, entry)
    else:
        # replace
        entries = [entry if e.get('file') == entry['file'] else e for e in entries]
    IDX_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    html = fetch_html(BASE_URL)
    date_str = guess_date(html)
    items = parse_items(html)
    write_snapshot(date_str, html)
    fname, data = write_json(date_str, items)
    update_index({'date': f"{date_str} (daily)", 'file': fname, 'count': data['count']})
    print(f"ARCHIVED {data['count']} items for {date_str} -> {fname}")

if __name__ == '__main__':
    main()
