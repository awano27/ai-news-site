#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a daily ranking page from public-pages/news/daily-*.json
- Pick latest daily JSON (or a given date via CLI arg)
- Score each item heuristically (domain + keywords)
- Output HTML to presentations/ai_ranking_from_daily_latest.html
"""
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import sys

NEWS_DIR = Path('public-pages/news')
OUT_LATEST = Path('presentations/ai_ranking_from_daily_latest.html')

DOMAIN_W = {
    # Official / research
    'openai.com': 96,
    'ai.google.dev': 94,
    'developers.googleblog.com': 90,
    'deepmind.com': 90,
    'anthropic.com': 88,
    'meta.com': 86,
    'research.facebook.com': 86,
    'arxiv.org': 85,
    'nature.com': 84,
    'science.org': 84,
    # Major news / vendor blogs
    'theverge.com': 72,
    'techcrunch.com': 70,
    'aws.amazon.com': 70,
    'azure.microsoft.com': 70,
    'developer.nvidia.com': 70,
    'blog.google': 70,
    'blog.langchain.com': 66,
    'marktechpost.com': 60,
    'towardsdatascience.com': 56,
    # Social
    'reddit.com': 45,
    'www.reddit.com': 45,
    'x.com': 48,
    'twitter.com': 48,
}

KEY_PATTERNS = [
    (re.compile(r'open\s*source|オープンソース|GitHub', re.I), 12),
    (re.compile(r'launch|release|introduc|announce|公開|発表|提供開始', re.I), 10),
    (re.compile(r'arxiv|論文|paper|preprint', re.I), 10),
    (re.compile(r'API|SDK|CLI', re.I), 8),
    (re.compile(r'funding|raises|調達|買収|acquire|M&A', re.I), 12),
    (re.compile(r'benchmark|SOTA|state[-\s]*of[-\s]*the[-\s]*art|ベンチマーク', re.I), 8),
    (re.compile(r'opinion|まとめ|meme|雑談', re.I), -6),
]


def domain_weight(url: str) -> int:
    try:
        host = urlparse(url).netloc.lower()
        # strip subsubdomains
        for k,v in DOMAIN_W.items():
            if host.endswith(k):
                return v
        return 60  # default medium
    except Exception:
        return 50


def text_bonus(title: str, summary: str) -> int:
    text = f"{title}\n{summary}"[:4000]
    total = 0
    for pat, pts in KEY_PATTERNS:
        if pat.search(text):
            total += pts
    return total


def clamp(x: int, lo=0, hi=100) -> int:
    return max(lo, min(hi, x))


def load_latest_daily(path: Path) -> Path | None:
    files = sorted(path.glob('daily-*.json'))
    if not files:
        return None
    # sort by date segment
    def key(p: Path):
        m = re.search(r'daily-(\d{4}-\d{2}-\d{2})', p.name)
        return m.group(1) if m else p.name
    files.sort(key=key, reverse=True)
    return files[0]


def build_html(date_str: str, items: list[dict]) -> str:
    now = datetime.now().strftime('%Y/%m/%d %H:%M')
    rows = []
    for i,it in enumerate(items, start=1):
        title = it.get('title') or '(no title)'
        url = it.get('url') or '#'
        host = urlparse(url).netloc
        score = it.get('score')
        rows.append(f'<div class="item"><div><span class="rank">{i}</span> <a href="{url}" target="_blank" rel="noopener">{title}</a><span class="host">{host}</span></div><div class="val">{score}</div></div>')
    cards = '\n'.join(rows) if rows else '<div class="empty">アイテムがありません。</div>'
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>日次ページ由来 ランキング（最新）</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    :root{{--bg:#ffffff;--fg:#0f172a;--muted:#64748b;--border:#e2e8f0;--accent:#3b82f6}}
    *{{box-sizing:border-box}}
    body{{margin:0;background:var(--bg);color:var(--fg);font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif}}
    .wrap{{max-width:960px;margin:0 auto;padding:20px}}
    h1{{font-size:22px;margin:0 0 6px 0}}
    .note{{color:var(--muted);margin:0 0 12px 0}}
    .list{{background:#fff;border:1px solid var(--border);border-radius:12px;padding:10px 12px}}
    .item{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);padding:8px 0;gap:10px}}
    .item:last-child{{border-bottom:none}}
    .rank{{display:inline-block;background:var(--accent);color:#fff;font-weight:800;font-size:12px;border-radius:999px;padding:2px 8px;margin-right:8px}}
    .host{{color:var(--muted);font-size:12px;margin-left:8px}}
    .val{{font-weight:800}}
    a{{color:var(--accent);text-decoration:none}}
    a:hover{{text-decoration:underline}}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>日次ページ由来 ランキング（{date_str}）</h1>
    <p class="note">生成: {now} / データ: public-pages/news/daily-{date_str}.json / ルール: ドメイン既定値 + キーワード加点</p>
    <div class="list">
      {cards}
    </div>
  </div>
</body>
</html>'''


def score_and_sort(data: dict) -> list[dict]:
    out = []
    for it in data.get('items', []):
        title = (it.get('title') or '').strip()
        summary = (it.get('summary') or '').strip()
        url = it.get('url') or ''
        base = domain_weight(url)
        bonus = text_bonus(title, summary)
        score = clamp(int(base + bonus))
        it2 = dict(it)
        it2['score'] = score
        out.append(it2)
    out.sort(key=lambda x: (x.get('score') or 0), reverse=True)
    return out


def main():
    # optional arg: YYYY-MM-DD
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if date_arg:
        p = NEWS_DIR / f'daily-{date_arg}.json'
        if not p.exists():
            print('ERROR: not found', p, file=sys.stderr)
            sys.exit(1)
    else:
        p = load_latest_daily(NEWS_DIR)
        if not p:
            print('ERROR: no daily json. run tools/archive_daily_pages.py first', file=sys.stderr)
            sys.exit(2)
    data = json.loads(p.read_text(encoding='utf-8'))
    date_str = data.get('date') or re.search(r'(\d{4}-\d{2}-\d{2})', p.name).group(1)
    ranked = score_and_sort(data)
    html = build_html(date_str, ranked[:50])
    OUT_LATEST.write_text(html, encoding='utf-8')
    print('WROTE', OUT_LATEST, 'from', p.name, 'items', len(ranked))

if __name__ == '__main__':
    main()
