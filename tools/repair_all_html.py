from pathlib import Path
from src.utils.sanitize import sanitize_html

ROOT = Path('presentations')

def main():
    files = sorted(ROOT.rglob('*.html'))
    fixed = 0
    for p in files:
        try:
            s = p.read_text(encoding='utf-8', errors='ignore')
            out = sanitize_html(s)
            if out != s:
                p.write_text(out, encoding='utf-8')
                fixed += 1
        except Exception as e:
            print('Skip', p, e)
    print(f'Fixed {fixed} html file(s).')

if __name__ == '__main__':
    main()

