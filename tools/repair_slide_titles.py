from pathlib import Path
import re
from src.utils.sanitize import sanitize_text

ROOT = Path('presentations/day_slides')

SUSPECT = re.compile(r'[\u7DB5\u7E79\u8B5B\u8B4C\u81B7\uFAE5]|[繝縺譛譌蟷ﾃ]')

FALLBACK_RULES = [
    (re.compile(r'MiniCPM[- ]?V\s*4[\._]5', re.I), 'MiniCPM‑V 4.5: モバイル革命'),
    (re.compile(r'OpenAI\s+Codex', re.I), 'OpenAI Codex アップデート'),
    (re.compile(r'Grok\s+Code\s+Fast\s*1', re.I), 'Grok Code Fast 1'),
    (re.compile(r'AlphaEarth', re.I), 'AlphaEarth Foundations'),
    (re.compile(r'Gemini\s*2\.5.*Flash\s*Image', re.I), 'Google Gemini 2.5 Flash Image'),
    (re.compile(r'Cursor', re.I), 'Cursor最新情報'),
    (re.compile(r'Google\s+MLE[- ]STAR', re.I), 'Google MLE‑STAR'),
    (re.compile(r'NEC\s*AI', re.I), 'NECのAIエージェント'),
    (re.compile(r'Pixel\s*10', re.I), 'Google Pixel 10'),
]

def detect_topic(text: str, raw: str) -> str:
    s = sanitize_text(text)
    if s and not SUSPECT.search(s):
        return s
    for rx, title in FALLBACK_RULES:
        if rx.search(raw):
            return title
    return 'Daily AI News'

def get_date_from_filename(name: str) -> str:
    m = re.match(r'day_slide_(\d{4})_(\d{2})_(\d{2})', name)
    if not m:
        return ''
    y, mm, dd = m.groups()
    return f'{y}年{mm}月{dd}日'

def patch_file(p: Path) -> bool:
    s = p.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'<title>(.*?)</title>', s, re.S)
    title_text = m.group(1) if m else ''
    m1 = re.search(r'<section[^>]*class="[^"]*title-slide[^"]*"[\s\S]*?<h1>([\s\S]*?)</h1>', s)
    if not m1:
        m1 = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', s)
    h1_text = m1.group(1) if m1 else ''
    topic = detect_topic(h1_text or title_text, s).strip()
    date_ja = get_date_from_filename(p.name)
    if not date_ja:
        m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', title_text)
        if m:
            y, mm, dd = m.groups()
            date_ja = f'{y}年{int(mm):02d}月{int(dd):02d}日'
    changed = False
    if date_ja:
        new_title = f'{date_ja} - {topic}'
        s2 = re.sub(r'<title>[\s\S]*?</title>', f'<title>{new_title}</title>', s, count=1)
        if s2 != s:
            s = s2
            changed = True
    if topic:
        def repl_h1(mh: re.Match) -> str:
            before = mh.group(0)
            return re.sub(r'<h1>[\s\S]*?</h1>', f'<h1>{topic}</h1>', before, count=1)
        s2 = re.sub(r'(<section[^>]*class="[^"]*title-slide[^"]*"[\s\S]*?</h1>)', repl_h1, s, count=1)
        if s2 == s and m1:
            s2 = re.sub(r'<h1[^>]*>[\s\S]*?</h1>', f'<h1>{topic}</h1>', s, count=1)
        if s2 != s:
            s = s2
            changed = True
    if changed:
        p.write_text(s, encoding='utf-8')
    return changed

def main():
    files = sorted(ROOT.glob('day_slide_*.html'))
    fixed = 0
    for f in files:
        if patch_file(f):
            fixed += 1
    print(f'Patched titles in {fixed} file(s).')

if __name__ == '__main__':
    main()

