#!/usr/bin/env python3
"""Fix dead /ai-news-site/ links from the old GitHub Pages project path.

When the site moved to visionhub.jp, the root is /, but many files still
contain href="/ai-news-site/..." and src="/ai-news-site/..." which 404 on the
custom domain. This replaces the prefix in-place for all HTML files under
public-pages/ and presentations/ (excluding node_modules / .git).
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIRS = ["public-pages", "presentations", "daily-news", "src"]

# Pattern 1: relative /ai-news-site/ in any quoted context (HTML attrs + JS strings)
PATTERN_REL = re.compile(r'(["\'])/ai-news-site/')
# Pattern 2: absolute https://awano27.github.io/ai-news-site/ URLs → visionhub.jp
PATTERN_ABS = re.compile(r'https://awano27\.github\.io/ai-news-site/')

def fix(text):
    text, n1 = PATTERN_REL.subn(r'\1/', text)
    text, n2 = PATTERN_ABS.subn('https://visionhub.jp/', text)
    return text, n1 + n2

fixed_files, total_replacements = [], 0

for d in DIRS:
    for p in (ROOT / d).rglob("*.html"):
        try:
            original = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        updated, count = fix(original)
        if count:
            p.write_text(updated, encoding="utf-8")
            fixed_files.append((str(p.relative_to(ROOT)), count))
            total_replacements += count

fixed_files.sort(key=lambda x: -x[1])
print(f"Fixed {total_replacements} dead links across {len(fixed_files)} files:")
for path, n in fixed_files:
    print(f"  {n:3d}  {path}")
if total_replacements == 0:
    print("Nothing to fix — all clean.")
