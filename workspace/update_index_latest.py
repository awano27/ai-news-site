#!/usr/bin/env python3
"""Update latest slide link in index.html"""

index_file = "D:/ai-news-site-main/index.html"

with open(index_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Update the latest slide link
content = content.replace(
    'href="presentations/day_slides/day_slide_2026_01_02.html" id="latestSlideHeroBtn"',
    'href="presentations/day_slides/day_slide_2026_01_06.html" id="latestSlideHeroBtn"'
)

with open(index_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated latest slide link in index.html to 2026_01_06")
