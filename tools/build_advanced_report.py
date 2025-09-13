#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

import sys\nfrom pathlib import Path as _P\nsys.path.append(str(_P(__file__).resolve().parents[1]))\nfrom tools.mojibake_guard import load_rules, sanitize_and_enforce

ARCHIVE_DIR = Path('public-pages/news')
OUT = Path('presentations/advanced_intelligence_report_latest.html')


def load_archive_items(max_days: int = 7) -> List[Dict]:
    idx_path = ARCHIVE_DIR / 'archive_index.json'
    if not idx_path.exists():
        return []
    idx = json.loads(idx_path.read_text(encoding='utf-8'))
    items: List[Dict] = []
    for entry in idx[:max_days]:
        data = json.loads((ARCHIVE_DIR / entry['file']).read_text(encoding='utf-8'))
        for it in data.get('items', []):
            items.append(it)
    return items


def sanitize_text(s: str) -> str:
    if not s:
        return ''
    # strip residual tags
    import re
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def build_html(items: List[Dict]) -> str:
    # pick top 10 by score
    items2 = sorted(items, key=lambda x: (x.get('score', 0), -x.get('rank', 9999)), reverse=True)[:10]
    now = datetime.now().strftime('%Y/%m/%d %H:%M')
    cards = []
    for it in items2:
        title = sanitize_text(it.get('title', ''))
        summary = sanitize_text(it.get('summary', ''))
        url = it.get('url', '')
        score = it.get('score', '')
        date = sanitize_text(it.get('date', ''))
        pts = ''.join(f'<li>{sanitize_text(p)}</li>' for p in (it.get('points') or [])[:3])
        links = ' '.join(f'<a href="{l.get("href","#")}" target="_blank" rel="noopener">{sanitize_text(l.get("text") or l.get("href"))}</a>' for l in (it.get('links') or [])[:3])
        cards.append(f'''
        <article class="card">
          <div class="score">{score}</div>
          <h3 class="title">{title}</h3>
          <div class="meta"><span>{date}</span></div>
          {f'<p class="summary">{summary}</p>' if summary else ''}
          {f'<ul class="points">{pts}</ul>' if pts else ''}
          <div class="actions">{f'<a class="btn" href="{url}" target="_blank" rel="noopener">記事を開く</a>' if url else ''} {links}</div>
        </article>
        ''')
    cards_html = '\n'.join(cards) if cards else '<div class="empty">該当データがありません。</div>'
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIニュース詳細レポート（最新）</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    :root{{--bg:#0b0f14;--surface:#10161d;--text:#e6edf3;--muted:#8aa0b2;--border:#1b2530;--accent:#67e8f9}}
    *{{box-sizing:border-box}}
    body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans JP',sans-serif}}
    header{{position:sticky;top:0;background:linear-gradient(180deg,#0b0f14 0%,#0a0e13 100%);border-bottom:1px solid var(--border);padding:12px 16px;z-index:10}}
    .wrap{{max-width:1100px;margin:0 auto;padding:0 16px 28px}}
    h1{{margin:12px 0 6px;font-size:24px;font-weight:900}}
    .meta{{color:var(--muted);font-size:13px;margin-bottom:12px}}
    .grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:16px}}
    @media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
    .card{{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;box-shadow:0 6px 18px rgba(0,0,0,.25)}}
    .title{{font-size:18px;font-weight:900;margin:4px 0 6px}}
    .score{{position:absolute;top:12px;right:12px;background:var(--accent);color:#0b0f14;font-weight:900;border-radius:9999px;padding:6px 10px}}
    .points li{{margin-left:1em}}
    .btn{{appearance:none;border:1px solid var(--border);background:var(--surface);padding:8px 10px;border-radius:10px;color:var(--accent);font-weight:800;text-decoration:none;display:inline-flex;align-items:center;gap:6px}}
    .actions a{{margin-right:8px}}
  </style>
</head>
<body>
  <header><div class="wrap"><strong>AIニュース詳細レポート（最新）</strong></div></header>
  <main class="wrap">
    <div class="meta">生成時刻: {now}</div>
    <section class="grid">{cards_html}</section>
  </main>
</body>
</html>'''
    return html


def main():
    items = load_archive_items(max_days=7)
    html = build_html(items)
    rules = load_rules()
    fixed, info = sanitize_and_enforce(html, rules)
    OUT.write_text(fixed, encoding='utf-8')
    print('WROTE', OUT, 'mojibake?', info['has_mojibake'])

if __name__ == '__main__':
    main()

