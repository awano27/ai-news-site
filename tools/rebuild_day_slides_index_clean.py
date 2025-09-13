#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from html import unescape, escape

ROOT = Path(__file__).resolve().parents[1]
DAY_DIR = ROOT / 'presentations' / 'day_slides'
OUT = ROOT / 'presentations' / 'day_slides_index.html'

# Regex helpers
RE_TITLE = re.compile(r'<title>([\s\S]*?)</title>', re.I)
RE_H1 = re.compile(r'<h1[^>]*>([\s\S]*?)</h1>', re.I)
RE_TAG = re.compile(r'<[^>]+>')
RE_WS = re.compile(r'\s+')
RE_LEADING_DATE = re.compile(r'^(\s*20\d{2}[\-/年]\s*\d{1,2}[\-/月]\s*\d{1,2}(?:日)?\s*[-|—|・|:])\s*')
RE_EMOJI = re.compile(r'[\U0001F300-\U0001FAFF]')
RE_ASCII_WORDS = re.compile(r'[A-Za-z][A-Za-z0-9+_.\-]{2,}')
RE_E_BETWEEN_NONASCII = re.compile(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])')

MOJI_TOKENS = (
    '\uFFFD', '朁E', '譌･', '蟷', '譛', '�', 'E/h', 'Ebr>'
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def clean_text(s: str) -> str:
    if not s:
        return ''
    t = unescape(s)
    t = RE_TAG.sub(' ', t)
    t = RE_EMOJI.sub('', t)
    t = RE_LEADING_DATE.sub('', t)
    t = t.replace('\uFFFD', '')
    t = t.replace('朁E', '月').replace('譌･', '日')
    # Remove broken closers like 'E/a>' 'E/h2>' left as plain text
    t = re.sub(r'E\/[a-z0-9]+>', '', t, flags=re.I)
    # Remove stray ASCII 'E' between multibyte chars
    t = RE_E_BETWEEN_NONASCII.sub('', t)
    t = RE_WS.sub(' ', t).strip().strip('-–—|:')
    return t


def english_fallback(title: str, y: str, m: str, d: str) -> str:
    words = RE_ASCII_WORDS.findall(title or '')
    if words:
        # Keep distinct order
        seen = set()
        uniq = [w for w in words if not (w in seen or seen.add(w))]
        s = ' '.join(uniq[:6])
        return s
    return f"Daily AI News {y}-{m}-{d}"


def pick_title(html: str, y: str, m: str, d: str) -> str:
    # Prefer <h1>, then <title>
    t = ''
    m1 = RE_H1.search(html)
    if m1:
        t = m1.group(1)
    else:
        m2 = RE_TITLE.search(html)
        if m2:
            t = m2.group(1)
    t = clean_text(t)
    # Prefer ASCII keywords if available (always readable)
    ascii_words = RE_ASCII_WORDS.findall(t or '')
    if ascii_words:
        seen = set()
        uniq = [w for w in ascii_words if not (w in seen or seen.add(w))]
        title = ' '.join(uniq[:6])
    else:
        # If mojibake-like tokens remain or empty, use generic English
        if any(tok in t for tok in MOJI_TOKENS) or RE_E_BETWEEN_NONASCII.search(t) or not t:
            title = f"Daily AI News {y}-{m}-{d}"
        else:
            title = t
    # Length guard
    return title if len(title) <= 90 else (title[:90] + '…')


def build():
    files = sorted(DAY_DIR.glob('day_slide_*.html'))
    items = []
    for f in files:
        m = re.match(r'day_slide_(\d{4})_(\d{2})_(\d{2})\.html$', f.name)
        if not m:
            continue
        y, mo, dd = m.groups()
        html = read_text(f)
        title = pick_title(html, y, mo, dd)
        has_sources_id = ("id='sources'" in html)
        items.append((f"{y}-{mo}-{dd}", f"{y}/{mo}/{dd}", f.name, title, has_sources_id))

    items.sort(reverse=True)  # newest first

    head = (
        "<!DOCTYPE html>\n"
        "<html lang=\"ja\">\n<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "  <title>Daily AI News Slides</title>\n"
        "  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap\" rel=\"stylesheet\">\n"
        "  <style>:root{--bg:#f8fafc;--fg:#0f172a;--accent:#3b82f6;--border:#e2e8f0}*{box-sizing:border-box}body{margin:0;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:var(--bg);color:var(--fg)}.wrap{display:grid;grid-template-columns:260px 1fr;min-height:100vh}aside{background:#0f172a;color:#e5e7eb;padding:18px}.brand{font-weight:800;margin:4px 0 14px 0}.nav a{display:block;color:#cbd5e1;text-decoration:none;padding:8px 10px;border-radius:8px}.nav a:hover{background:#1e293b;color:#fff}main{padding:20px}h1{margin:4px 0 16px 0;font-size:24px}.note{background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin:0 0 16px 0}ul.slides{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}ul.slides li a{display:block;background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--fg);font-weight:600}ul.slides li a:hover{border-color:#c7d2fe;box-shadow:0 4px 16px rgba(2,6,23,.06)}.date{display:inline-block;font-size:12px;font-weight:800;color:#fff;background:var(--accent);padding:2px 8px;border-radius:999px;margin-right:8px}</style>\n"
        "</head>\n<body>\n  <div class=\"wrap\">\n    <aside>\n      <div class=\"brand\">AI Intelligence</div>\n      <nav class=\"nav\">\n        <a href=\"index.html\">Home</a>\n        <a href=\"ai_ranking_interactive.html\">Ranking</a>\n        <a href=\"integrated_report.html\">Report</a>\n      </nav>\n    </aside>\n    <main>\n      <h1>Daily Slides</h1>\n      <div class=\"note\">Daily AI news slide index. Titles fall back to English keywords when Japanese text is unavailable.</div>\n      <ul class=\"slides\">\n"
    )

    lis = []
    seen = set()
    for _, date_label, fname, title, has_sources_id in items:
        href = f"day_slides/{fname}"
        if href in seen:
            continue
        seen.add(href)
        if has_sources_id:
            lis.append(
                f"        <li><a href=\"{href}\"><span class=\"date\">{date_label}</span>{escape(title)}</a> "
                f"<a href=\"{href}#sources\" style=\"margin-left:8px;color:#2563eb;text-decoration:underline;font-weight:600;\">Source</a></li>\n"
            )
        else:
            lis.append(f"        <li><a href=\"{href}\"><span class=\"date\">{date_label}</span>{escape(title)}</a></li>\n")

    tail = (
        "      </ul>\n    </main>\n  </div>\n</body>\n</html>\n"
    )

    OUT.write_text(head + ''.join(lis) + tail, encoding='utf-8')
    print(f"wrote {OUT}")


if __name__ == '__main__':
    build()
