#!/usr/bin/env python3
"""
Archive Daily AI News from remote page and save per-day HTML + JSON.

Primary source (remote): https://awano27.github.io/daily-ai-news-pages/
Fallback source (local): presentations/daily_ai_news_report_latest.html

Outputs:
- public-pages/news/YYYY-MM-DD.html  (raw snapshot)
- public-pages/news/YYYY-MM-DD.json  (parsed items)
- public-pages/news/archive_index.json  (list of dates and counts)

Usage:
  python tools/archive_daily_ai_news.py               # archive today
  python tools/archive_daily_ai_news.py 2025-09-06    # specific date
"""
from __future__ import annotations

import sys
import json
import datetime as dt
import re
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'public-pages' / 'news'
OUT_DIR.mkdir(parents=True, exist_ok=True)

REMOTE_CANDIDATES = [
    'https://awano27.github.io/daily-ai-news-pages/latest.html',
    'https://awano27.github.io/daily-ai-news-pages/index.html',
]

LOCAL_FALLBACK = ROOT / 'presentations' / 'daily_ai_news_report_latest.html'


def _clean_text(s: str) -> str:
    """Fix common mojibake, decode entities, strip tags and collapse whitespace."""
    try:
        from ftfy import fix_text  # type: ignore
    except Exception:
        def fix_text(x: str) -> str:  # type: ignore
            return x
    import html as _html
    import re as _re
    if not s:
        return ''
    t = fix_text(str(s))
    # decode entities (twice for cases like &amp;#12354;)
    t = _html.unescape(_html.unescape(t))
    # strip tags
    t = _re.sub(r'<[^>]+>', ' ', t)
    # remove stray replacement chars / ASCII 'E' between multibyte chars
    t = t.replace('\uFFFD', '')
    t = _re.sub(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])', '', t)
    # collapse whitespace
    t = _re.sub(r'[\u00A0\u2000-\u200B\u3000]', ' ', t)
    t = _re.sub(r'\s+', ' ', t).strip()
    return t


def _normalize_date(s: str) -> str:
    """Try to extract an ISO-like date from messy strings."""
    import re as _re
    if not s:
        return ''
    m = _re.search(r'(\d{4})[./-]?(\d{1,2})[./-]?(\d{1,2})', s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return f"{y:04d}-{mo:02d}-{d:02d}"
        except Exception:
            return s
    return s


def fetch_remote() -> tuple[str, str]:
    headers = {'User-Agent': 'ai-news-archiver/1.0'}
    for url in REMOTE_CANDIDATES:
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as r:
                html = r.read().decode('utf-8', errors='ignore')
            if '<html' in html.lower():
                return html, url
        except (URLError, HTTPError):
            continue
    if LOCAL_FALLBACK.exists():
        return LOCAL_FALLBACK.read_text(encoding='utf-8', errors='ignore'), str(LOCAL_FALLBACK)
    raise SystemExit('No source available')


def parse_items(html: str) -> list[dict]:
    # Light-weight parsing using regex over expected structure
    # Split blocks by .news-item
    blocks = re.split(r'<div class=\"news-item\"|<div class="news-item">', html, flags=re.IGNORECASE)
    items: list[dict] = []
    for idx, blk in enumerate(blocks[1:], start=1):
        # Consider only up to end of this item
        blk = blk.split('</div>', 1)[-1] if blk else blk
        def _find(pat, default=''):
            m = re.search(pat, blk, re.IGNORECASE | re.DOTALL)
            return (m.group(1).strip() if m else default)
        title = _find(r'<div class=\"news-title\">(.*?)</div>|<div class="news-title">(.*?)</div>')
        if not title:
            title = _find(r'<h3[^>]*>(.*?)</h3>')
        score = _find(r'<div class=\"news-score\">(\d+)</div>|<div class="news-score">(\d+)</div>')
        rank = _find(r'<div class=\"news-rank\">(\d+)</div>|<div class="news-rank">(\d+)</div>') or str(idx)
        meta = _find(r'<div class=\"news-meta\">(.*?)</div>|<div class="news-meta">(.*?)</div>')
        url = ''
        m = re.search(r'URL\s*=\s*([^,\s<]+)', meta)
        if m:
            url = m.group(1)
        date = ''
        md = re.search(r'(?:投稿日|Date|日付|謚慕ｨｿ日)\s*=\s*([^,<>]+)', meta)
        if md:
            date = md.group(1).strip()
        p = _find(r'<p>(.*?)</p>')
        # Strip tags from p
        summary = re.sub(r'<[^>]+>', '', p).strip() if p else ''
        # points
        pts = re.findall(r'<li>(.*?)</li>', blk, re.IGNORECASE | re.DOTALL)
        points = [re.sub(r'<[^>]+>', '', t).strip() for t in pts][:5]
        # links inside item
        links = re.findall(r'<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>|<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', blk, re.IGNORECASE | re.DOTALL)
        link_list = []
        for a in links:
            href = a[0] or a[2]
            text = (a[1] or a[3] or '').strip()
            if href and href.startswith('http'):
                link_list.append({'href': href, 'text': text})
        try:
            score_i = int(score) if score else 0
        except ValueError:
            score_i = 0
        items.append({
            'title': title,
            'score': score_i,
            'rank': int(rank) if rank.isdigit() else idx,
            'url': url,
            'date': date,
            'summary': summary,
            'points': points,
            'links': link_list,
        })
    # Sort by score desc then rank asc
    items.sort(key=lambda x: (-x['score'], x['rank']))
    return items


def parse_items_clean(html: str) -> list[dict]:
    """Cleaned parser with mojibake fixes and normalization."""
    blocks = re.split(r'<div class=\"news-item\"|<div class="news-item">', html, flags=re.IGNORECASE)
    items: list[dict] = []
    for idx, blk in enumerate(blocks[1:], start=1):
        blk = blk.split('</div>', 1)[-1] if blk else blk
        def _find(pat, default=''):
            m = re.search(pat, blk, re.IGNORECASE | re.DOTALL)
            return (m.group(1).strip() if m else default)
        raw_title = _find(r'<div class=\"news-title\">(.*?)</div>|<div class="news-title">(.*?)</div>')
        if not raw_title:
            raw_title = _find(r'<h3[^>]*>(.*?)</h3>')
        title = _clean_text(raw_title)
        score = _find(r'<div class=\"news-score\">(\d+)</div>|<div class="news-score">(\d+)</div>')
        rank = _find(r'<div class=\"news-rank\">(\d+)</div>|<div class="news-rank">(\d+)</div>') or str(idx)
        meta = _find(r'<div class=\"news-meta\">(.*?)</div>|<div class="news-meta">(.*?)</div>')
        url = ''
        m = re.search(r'URL\s*=\s*([^,\s<]+)', meta)
        if m:
            url = m.group(1)
        date = ''
        md = re.search(r'(?:Date|投稿日|謚慕ｨｿ譌･|譌･莉・隰壽・・ｨ・ｿ譌･)\s*=\s*([^,<>]+)', meta)
        if md:
            date = _normalize_date(_clean_text(md.group(1)))
        p = _find(r'<p>(.*?)</p>')
        summary = _clean_text(p)
        pts = re.findall(r'<li>(.*?)</li>', blk, re.IGNORECASE | re.DOTALL)
        points = [_clean_text(t) for t in pts][:5]
        links = re.findall(r'<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>|<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', blk, re.IGNORECASE | re.DOTALL)
        link_list = []
        for a in links:
            href = a[0] or a[2]
            text = _clean_text(a[1] or a[3] or '')
            if href and href.startswith('http'):
                link_list.append({'href': href, 'text': text})
        try:
            score_i = int(score) if score else 0
        except ValueError:
            score_i = 0
        items.append({
            'title': title,
            'score': score_i,
            'rank': int(rank) if rank.isdigit() else idx,
            'url': url,
            'date': date,
            'summary': summary,
            'points': points,
            'links': link_list,
        })
    items.sort(key=lambda x: (-x['score'], x['rank']))
    return items

# Override to use cleaned parser
parse_items = parse_items_clean

def main():
    if len(sys.argv) > 1:
        try:
            day = dt.datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        except ValueError:
            print('Usage: python tools/archive_daily_ai_news.py [YYYY-MM-DD]')
            return 2
    else:
        # Use JST date for day naming
        jst = dt.timezone(dt.timedelta(hours=9))
        day = dt.datetime.now(tz=jst).date()

    html, source_url = fetch_remote()
    items = parse_items(html)
    # Fallback to local file if remote parsing yields no items
    if len(items) == 0 and LOCAL_FALLBACK.exists():
        html = LOCAL_FALLBACK.read_text(encoding='utf-8', errors='ignore')
        items = parse_items(html)
        source_url = str(LOCAL_FALLBACK)

    date_str = day.isoformat()
    # Write snapshot HTML and JSON
    (OUT_DIR / f'{date_str}.html').write_text(html, encoding='utf-8')
    (OUT_DIR / f'{date_str}.json').write_text(json.dumps({
        'date': date_str,
        'source': source_url,
        'count': len(items),
        'items': items,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    # Update archive index
    idx_path = OUT_DIR / 'archive_index.json'
    index = []
    if idx_path.exists():
        try:
            index = json.loads(idx_path.read_text(encoding='utf-8'))
        except Exception:
            index = []
    # remove existing date if present
    index = [x for x in index if x.get('date') != date_str]
    index.append({'date': date_str, 'file': f'{date_str}.json', 'count': len(items)})
    index.sort(key=lambda x: x['date'], reverse=True)
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Archived {len(items)} items for {date_str} from {source_url}')

if __name__ == '__main__':
    sys.exit(main() or 0)

