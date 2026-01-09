#!/usr/bin/env python3
"""Add 0106 entry to day_slides_index.html"""

index_file = "D:/ai-news-site-main/presentations/day_slides_index.html"

with open(index_file, 'r', encoding='utf-8') as f:
    content = f.read()

# New entry for 0106
new_entry = '''                        <li>
                              <a href="day_slides/day_slide_2026_01_06.html" class="slide-link">
                                    <span class="date">2026/01/06</span>
                                    <span class="slide-title">AIエージェント・ハーネス：信頼性を支える次世代OS</span>
                              </a>
                        </li>
'''

# Find the position to insert (after <ul class="slides">)
target = '<ul class="slides">\n'
pos = content.find(target)

if pos != -1:
    # Insert after the <ul> tag
    insert_pos = pos + len(target)
    content = content[:insert_pos] + new_entry + content[insert_pos:]

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Added 0106 entry to {index_file}")
else:
    print("Error: Could not find insertion point")
