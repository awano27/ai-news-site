#!/usr/bin/env python3
import re
from pathlib import Path
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
DAY_DIR = ROOT / 'presentations' / 'day_slides'
INDEX = ROOT / 'presentations' / 'day_slides_index.html'

def simple_title_from_html(html: str) -> str:
    s = unescape(html or '')
    # Try <title>
    m = re.search(r'<title>([\s\S]*?)</title>', s, re.I)
    if m:
        t = m.group(1).strip()
    else:
        # Try first h1/h2
        m = re.search(r'<h[12][^>]*>([\s\S]*?)</h[12]>', s, re.I)
        t = m.group(1).strip() if m else ''
    # Remove tags/emojis and leading date
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    # Remove date prefix like 2025年.. or 2025/.. until dash/pipe
    t = re.sub(r'^\s*\d{4}[^\-|｜]*[-｜]\s*', '', t)
    # Replace mojibake fragments
    t = t.replace('朁E', '月')
    t = t.replace('\uFFFD', '')
    # Strip common emojis to keep it simple
    t = re.sub(r'[\U0001F300-\U0001FAFF]', '', t)
    t = t.strip(' -–—|')
    # Fallback
    if not t or '?' in t:
        t = 'Daily Slide'
    # Keep it short
    return (t[:60] + '…') if len(t) > 60 else t

def main():
    if not DAY_DIR.exists():
        print('day_slides folder not found')
        return
    items = []
    for p in sorted(DAY_DIR.glob('day_slide_*.html')):
        m = re.match(r'day_slide_(\d{4})_(\d{2})_(\d{2})', p.stem)
        if not m: 
            continue
        y, mm, dd = m.groups()
        date_label = f"{y}/{mm}/{dd}"
        try:
            html = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            html = ''
        title = simple_title_from_html(html)
        items.append((f"{y}-{mm}-{dd}", date_label, p.name, title))
    items.sort(reverse=True)

    # Build index HTML (keep existing simple layout/styles)
    head = (
        "<!DOCTYPE html>\n"
        "<html lang=\"ja\">\n<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "  <title>Daily Slides Index</title>\n"
        "  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap\" rel=\"stylesheet\">\n"
        "  <style>:root{--bg:#f8fafc;--fg:#0f172a;--accent:#3b82f6;--border:#e2e8f0}*{box-sizing:border-box}body{margin:0;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:var(--bg);color:var(--fg)}.wrap{display:grid;grid-template-columns:260px 1fr;min-height:100vh}aside{background:#0f172a;color:#e5e7eb;padding:18px}.brand{font-weight:800;margin:4px 0 14px 0}.nav a{display:block;color:#cbd5e1;text-decoration:none;padding:8px 10px;border-radius:8px}.nav a:hover{background:#1e293b;color:#fff}main{padding:20px}h1{margin:4px 0 16px 0;font-size:24px}.note{background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin:0 0 16px 0}ul.slides{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}ul.slides li a{display:block;background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--fg);font-weight:600}ul.slides li a:hover{border-color:#c7d2fe;box-shadow:0 4px 16px rgba(2,6,23,.06)}.date{display:inline-block;font-size:12px;font-weight:800;color:#fff;background:var(--accent);padding:2px 8px;border-radius:999px;margin-right:8px}</style>\n"
        "</head>\n<body>\n  <div class=\"wrap\">\n    <aside>\n      <div class=\"brand\">AI Intelligence</div>\n      <nav class=\"nav\">\n        <a href=\"index.html\">Home</a>\n        <a href=\"ai_ranking_interactive.html\">Ranking</a>\n        <a href=\"integrated_report.html\">Report</a>\n      </nav>\n    </aside>\n    <main>\n      <h1>Daily Slides</h1>\n      <div class=\"note\">日次AIニュース・レポートのスライド一覧です。</div>\n      <ul class=\"slides\">\n"
    )
    li_lines = []
    for _, date_label, fname, title in items:
        text = f"        <li><a href=\"day_slides/{fname}\"><span class=\"date\">{date_label}</span>{date_label} - {title}</a></li>\n"
        li_lines.append(text)
    tail = (
        "      </ul>\n    </main>\n  </div>\n</body>\n</html>\n"
    )
    INDEX.write_text(head + ''.join(li_lines) + tail, encoding='utf-8')
    print(f"wrote {INDEX}")

if __name__ == '__main__':
    main()

