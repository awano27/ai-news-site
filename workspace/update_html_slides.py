#!/usr/bin/env python3
"""Update HTML with all 14 slide images"""

html_file = "D:/ai-news-site-main/presentations/day_slides/day_slide_2026_01_06.html"

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace slide count
content = content.replace('全5ページ', '全14ページ')

# Build new slides HTML
slides_html = []
for i in range(1, 15):
    slides_html.append(f'<img src="../../input/day/0106_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')

new_slides = ''.join(slides_html)

# Find and replace the slides container content
import re
pattern = r'(<div class="slides-container">)(.*?)(</div>)'
replacement = r'\1\n          ' + new_slides + r'\n        \3'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {html_file} with 14 slides")
