from pathlib import Path
import re, html

SLIDES_DIR = Path('presentations/day_slides')
OUT_FILE = Path('presentations/day_slides_index.html')

def pick_latest(slides_dir: Path):
    files = sorted(slides_dir.glob('day_slide_*.html'))
    by_date = {}
    for p in files:
        m = re.match(r'day_slide_(\d{4})_(\d{2})_(\d{2})(?:_detailed)?\.html$', p.name)
        if not m:
            continue
        y, mn, d = m.groups()
        key = f"{y}/{mn}/{d}"
        detailed = p.name.endswith('_detailed.html')
        if key in by_date:
            if detailed: by_date[key] = p
        else:
            by_date[key] = p
    return dict(sorted(by_date.items(), key=lambda kv: kv[0], reverse=True))

def extract_title(path: Path) -> str:
    s = path.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'<title>(.*?)</title>', s, re.S)
    t = m.group(1) if m else ''
    if not t:
        m = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
        t = m.group(1) if m else ''
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('朁E','月').strip()
    t = re.sub(r'^\d{4}年\d{2}月\d{2}日\s*-\s*', '', t)
    return html.escape(t or 'Daily Slide')

def update_index(items: dict):
    content = OUT_FILE.read_text(encoding='utf-8')
    lis = [f'        <li><a href="day_slides/{p.name}"><span class="date">{key}</span> {extract_title(p)}</a></li>'
           for key, p in items.items()]
    new = re.sub(r'(?s)<ul class="slides">.*?</ul>', '<ul class="slides">\n' + "\n".join(lis) + '\n      </ul>', content)
    OUT_FILE.write_text(new, encoding='utf-8')

def main():
    items = pick_latest(SLIDES_DIR)
    update_index(items)
    print(f"Updated index with {len(items)} entries")

if __name__ == '__main__':
    main()

