from pathlib import Path
import sys
sys.path.append('src')
from utils.sanitize import sanitize_html

files = [
    Path('presentations/advanced_intelligence_report_latest.html'),
    Path('presentations/advanced_intelligence_report_20250826.html'),
]

for p in files:
    if not p.exists():
        continue
    raw = p.read_text(encoding='utf-8', errors='ignore')
    fixed = sanitize_html(raw)
    # Additional light fixes specific to this page
    fixed = fixed.replace('E/','</')
    # Normalize some common mojibake fragments in headings
    replacements = {
        'Daily AI News': 'Daily AI News',
        'AI繝九Η繝ｼ繧ｹ': 'AIニュース',
        '隧ｳ邏ｰ': 'レポート',
        '譛': '', '蟷': '', '譌': ''
    }
    for k,v in replacements.items():
        fixed = fixed.replace(k, v)
    p.write_text(fixed, encoding='utf-8')
    print('fixed:', p)
