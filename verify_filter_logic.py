#!/usr/bin/env python3
"""
Simulate the JavaScript filtering logic to verify it will work correctly
"""

import re
from pathlib import Path
from collections import defaultdict

html_path = Path(r'c:\develop\ai-news-site\presentations\recommended_tools.html')

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract filter buttons
filter_buttons = re.findall(r'data-filter="([^"]+)"', content)
unique_filters = sorted(set(filter_buttons))

print("Available filters:")
for f in unique_filters:
    print(f"  - {f}")

print("\n" + "="*60)
print("FILTER SIMULATION")
print("="*60)

# Extract all tool cards with their classes
tool_cards = re.findall(r'<div class="tool-card([^"]*)"[^>]*>.*?<h3>([^<]+)', content, re.DOTALL)

print(f"\nTotal tool cards: {len(tool_cards)}")

# Simulate filtering for each category
for filter_name in ['all', 'meeting', 'docs', 'pm', 'automation', 'ai', 'dev', 'ph', 'other']:
    matching_tools = []

    for classes, title in tool_cards:
        if filter_name == 'all':
            matching_tools.append(title.strip())
        elif filter_name in classes:
            matching_tools.append(title.strip())

    print(f"\n{filter_name.upper()}: {len(matching_tools)} tools")

    if len(matching_tools) == 0:
        print("  [!] WARNING: No tools found! Will show 'No tools found message'")
    else:
        print(f"  [OK] Sample: {matching_tools[0]}")
        if len(matching_tools) > 1:
            print(f"           {matching_tools[1]}")

print("\n" + "="*60)
print("RESULT")
print("="*60)

# Check for problematic filters
problematic = []
for filter_name in ['meeting', 'docs', 'pm', 'automation', 'ai', 'dev', 'ph', 'other']:
    count = sum(1 for classes, _ in tool_cards if filter_name in classes)
    if count == 0:
        problematic.append(filter_name)

if problematic:
    print(f"\n[!] ISSUE: These filters will show 'no results': {', '.join(problematic)}")
else:
    print("\n[SUCCESS] All filters have at least one matching tool")
    print("[SUCCESS] The 'Product Hunt' (ph) filter will work correctly")
