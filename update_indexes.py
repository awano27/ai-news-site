import re
from pathlib import Path
import json

def update_indexes():
    today_str = "2025-12-09"
    date_slash = "2025/12/09"
    json_path = Path(f"public-pages/news/{today_str}.json")
    
    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get title
    title = data['items'][0]['title']
    if len(title) > 50:
         match = re.match(r'(.*?)(?:は、|が、|で、)', title)
         if match:
             title = match.group(1)
         else:
             title = title[:50] + "..."

    # 1. Update day_slides_index.html
    index_path = Path("presentations/day_slides_index.html")
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_li = f'        <li><a href="day_slides/day_slide_{today_str.replace("-", "_")}.html" aria-describedby="slide-{today_str}"><span class="date">{date_slash}</span><span class="slide-title">{title}</span></a></li>'
    
    # Check if already exists
    if f'day_slide_{today_str.replace("-", "_")}.html' not in content:
        # Insert after <ul class="slides" role="list">
        content = re.sub(r'(<ul class="slides" role="list">\s*)', f'\1{new_li}\n', content)
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {index_path}")
    else:
        print(f"Entry already exists in {index_path}")

    # 2. Update day_slides_list.html
    list_path = Path("presentations/day_slides_list.html")
    with open(list_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_card = f'''
      <a href="https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_{today_str.replace("-", "_")}.html" class="slide-card">
        <span class="date-badge">{date_slash}</span>
        <div class="slide-title">{title}</div>
      </a>'''

    if f'day_slide_{today_str.replace("-", "_")}.html' not in content:
        # Check if "12月分" comment exists
        if '<!-- 12月分 -->' in content:
            content = content.replace('<!-- 12月分 -->', f'<!-- 12月分 -->{new_card}')
        elif '<div class="slides-grid">' in content:
             # Add 12月分 comment and card
             content = content.replace('<div class="slides-grid">', f'<div class="slides-grid">\n      <!-- 12月分 -->{new_card}')
        
        with open(list_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {list_path}")
    else:
         print(f"Entry already exists in {list_path}")

if __name__ == "__main__":
    update_indexes()
