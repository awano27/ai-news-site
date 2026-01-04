#!/usr/bin/env python3
"""
Verify that category classes were properly added to all tool-cards
"""

import re
from pathlib import Path

html_path = Path(r'c:\develop\ai-news-site\presentations\recommended_tools.html')

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all tool-card divs
tool_cards = re.findall(r'<div class="tool-card([^"]*)"', content)

print(f"Total tool cards found: {len(tool_cards)}")

# Count by category
categories_count = {
    'meeting': 0,
    'docs': 0,
    'pm': 0,
    'automation': 0,
    'ai': 0,
    'dev': 0,
    'ph': 0,
    'other': 0
}

cards_without_categories = 0

for card_classes in tool_cards:
    classes = card_classes.strip().split()

    if not classes:
        cards_without_categories += 1
        print(f"WARNING: Found card without categories: {card_classes}")

    for cat in classes:
        if cat in categories_count:
            categories_count[cat] += 1

print("\nCategory distribution:")
for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cat}: {count} tools")

print(f"\nCards without any category: {cards_without_categories}")

# Verify 'ph' category has tools
if categories_count['ph'] > 0:
    print(f"\n[OK] Product Hunt (ph) filter has {categories_count['ph']} tools")
else:
    print("\n[ERROR] No tools found with 'ph' category!")

# Sample a few 'ph' tools
ph_tools = re.findall(r'<div class="tool-card[^"]*ph[^"]*"[^>]*>.*?<h3>([^<]+)', content, re.DOTALL)
print(f"\nSample tools with 'ph' category (first 10):")
for i, title in enumerate(ph_tools[:10], 1):
    print(f"  {i}. {title.strip()}")
