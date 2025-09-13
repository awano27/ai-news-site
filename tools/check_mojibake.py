from pathlib import Path
import re
import sys

ROOTS = [Path('presentations')]

PATTERNS = [
    re.compile(r'[\uE000-\uF8FF]'),  # Private Use Area (e.g., \uE05E)
    re.compile(r'(E\/(?:h[1-6]|div|span|p|button|section)>)'),
    re.compile(r'[蟷譛譌繝縺螟遒閭蜿雋髱逅螳蝠雜蠢]'),  # common SJIS-misread CJK cluster
    re.compile(r'�'),  # replacement char
]

def file_has_mojibake(text: str) -> bool:
    return any(rx.search(text) for rx in PATTERNS)

def main() -> int:
    offenders = []
    for root in ROOTS:
        for p in root.rglob('*.html'):
            try:
                s = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if file_has_mojibake(s):
                offenders.append(str(p))
    if offenders:
        print('Found possible mojibake in:')
        for f in sorted(offenders):
            print('  ', f)
        return 1
    print('No mojibake patterns detected.')
    return 0

if __name__ == '__main__':
    sys.exit(main())

