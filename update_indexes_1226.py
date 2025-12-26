import re
import os
from pathlib import Path

def update_indexes_1226():
    today_str = "2025-12-26"
    date_slash = "2025/12/26"
    title = "AIプロジェクト管理の革命：指示するAIから、自律するオーナーへ (AIPO)"
    
    # URL friendly name (matching create_slide_1226.py output)
    slide_filename = f"day_slide_{today_str.replace('-', '_')}.html"

    # 1. Update day_slides_index.html
    index_path = Path("presentations/day_slides_index.html")
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_li = f'        <li><a href="day_slides/{slide_filename}" aria-describedby="slide-{today_str}"><span class="date">{date_slash}</span><span class="slide-title">{title}</span></a></li>'
        
        if slide_filename not in content:
            # SKILL WORKFLOW: Insert at the top of the list
            content = re.sub(r'(<ul class="slides">\s*)', f'\\1{new_li}\\n', content)
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {index_path}")
        else:
            print(f"Entry already exists in {index_path}")

    # 2. Update day_slides_list.html
    list_path = Path("presentations/day_slides_list.html")
    if list_path.exists():
        with open(list_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_card = f'''
      <a href="https://awano27.github.io/ai-news-site/presentations/day_slides/{slide_filename}" class="slide-card">
        <span class="date-badge">{date_slash}</span>
        <div class="slide-title">{title}</div>
      </a>'''

        if slide_filename not in content:
            # SKILL WORKFLOW: Add to '12月分' card section
            if '<!-- 12月分 -->' in content:
                content = content.replace('<!-- 12月分 -->', f'<!-- 12月分 -->{new_card}')
            elif '<div class="slides-grid">' in content:
                 content = content.replace('<div class="slides-grid">', f'<div class="slides-grid">\n      <!-- 12月分 -->{new_card}')
            
            with open(list_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {list_path}")
        else:
             print(f"Entry already exists in {list_path}")

if __name__ == "__main__":
    update_indexes_1226()
