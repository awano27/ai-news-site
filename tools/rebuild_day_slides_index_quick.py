from pathlib import Path
import re
from html import escape

root = Path('presentations/day_slides')
files = sorted(root.glob('day_slide_*.html'))
DATE_RE = re.compile(r'^20\d{2}/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])$')

MOJIBAKE_TOKENS = ('繝','繧','縺','蜻','譛','蟷','譌','鬮','鬩','髱','驥','豈','螟','｡','･','・')
ASCII_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_+#\-\/:., ]{6,}')

def clean_title(raw: str) -> str:
    if not raw:
        return ''
    # Strip any HTML tags (like <br>) embedded in title
    s = re.sub(r'<[^>]+>', ' ', raw)
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s

items = []
for f in files:
    m = re.search(r'day_slide_(\d{4})_(\d{2})_(\d{2})\.html$', f.name)
    if not m:
        continue
    y, mo, d = m.groups()
    date_disp = f"{y}/{mo}/{d}"
    href = f"day_slides/{f.name}"
    # read title
    try:
        s = f.read_text(encoding='utf-8', errors='ignore')
        mt = re.search(r'<title>(.*?)</title>', s, re.DOTALL|re.IGNORECASE)
        title_raw = mt.group(1) if mt else f"Daily Slide {date_disp}"
    except Exception:
        title_raw = f"Daily Slide {date_disp}"

    t = clean_title(title_raw)
    # detect mojibake
    has_moji = any(tok in t for tok in MOJIBAKE_TOKENS)
    if has_moji:
        m2 = ASCII_RE.findall(t)
        t_clean = (' '.join(m2).strip()) if m2 else '日次AIニュースダイジェスト'
    else:
        t_clean = t

    if not DATE_RE.match(date_disp):
        continue
    items.append((f"{y}-{mo}-{d}", date_disp, href, t_clean))

# sort descending by date
items.sort(key=lambda x: x[0], reverse=True)

html = ['''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>日次AIニューススライド</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    :root { --bg:#f8fafc; --fg:#0f172a; --accent:#3b82f6; --border:#e2e8f0; }
    *{box-sizing:border-box}
    body{margin:0;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:var(--bg);color:var(--fg)}
    .wrap{display:grid;grid-template-columns:260px 1fr;min-height:100vh}
    aside{background:#0f172a;color:#e5e7eb;padding:18px}
    .brand{font-weight:800;margin:4px 0 14px 0}
    .nav a{display:block;color:#cbd5e1;text-decoration:none;padding:8px 10px;border-radius:8px}
    .nav a:hover{background:#1e293b;color:#fff}
    main{padding:20px}
    h1{margin:4px 0 16px 0;font-size:24px}
    .note{background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin:0 0 16px 0}
    ul.slides{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}
    ul.slides li a{display:block;background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--fg);font-weight:600}
    ul.slides li a:hover{border-color:#c7d2fe;box-shadow:0 4px 16px rgba(2,6,23,.06)}
    .date{display:inline-block;font-size:12px;font-weight:800;color:#fff;background:var(--accent);padding:2px 8px;border-radius:999px;margin-right:8px}
  </style>
</head>
<body>
  <div class="wrap">
    <aside>
      <div class="brand">AI Intelligence</div>
      <nav class="nav">
        <a href="index.html">Home</a>
        <a href="ai_ranking_interactive.html">Ranking</a>
        <a href="integrated_report.html">Report</a>
      </nav>
    </aside>
    <main>
      <h1>日次AIニューススライド</h1>
      <div class="note">最新の日次スライドへのリンク一覧です。</div>
      <ul class="slides">''']

seen=set()
for _, date_disp, href, title in items:
    if href in seen: continue
    seen.add(href)
    html.append(f'        <li><a href="{href}"><span class="date">{date_disp}</span>{escape(title)}</a></li>')

html.append('''      </ul>
    </main>
  </div>
</body>
</html>
''')

Path('presentations/day_slides_index.html').write_text('\n'.join(html), encoding='utf-8')
print('REBUILT_INDEX_V3', len(items))
