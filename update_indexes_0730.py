import re
from pathlib import Path

def update_indexes_0730():
    today_str = "2025-07-30"
    date_slash = "2025/07/30"
    title = "Google DeepMind: AlphaEarth Foundations"
    
    # 1. Update day_slides_index.html
    index_path = Path("presentations/day_slides_index.html")
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_li = f'                        <li><a href="day_slides/day_slide_{today_str.replace("-", "_")}.html" aria-describedby="slide-{today_str}"><span class="date">{date_slash}</span><span class="slide-title">{title}</span></a></li>'
        
        if f'day_slide_{today_str.replace("-", "_")}.html' not in content:
            # Insert after the start of the list or before the first item
            content = re.sub(r'(<ul class="slides">\s*)', f'\\1{new_li}\n', content)
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
      <a href="https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_{today_str.replace("-", "_")}.html" class="slide-card">
        <span class="date-badge">{date_slash}</span>
        <div class="slide-title">{title}</div>
      </a>'''

        if f'day_slide_{today_str.replace("-", "_")}.html' not in content:
            # Check for "7月分" comment, if not exists, create it
            if '<!-- 7月分 -->' in content:
                 content = content.replace('<!-- 7月分 -->', f'<!-- 7月分 -->{new_card}')
            else:
                # If 7月分 doesn't exist, append to the end of the grid (simplification)
                # Ideally we should find the right place, but appending to the top of the grid is safer for visibility
                content = content.replace('<div class="slides-grid">', f'<div class="slides-grid">\n      <!-- 7月分 -->{new_card}')
            
            with open(list_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {list_path}")
        else:
             print(f"Entry already exists in {list_path}")

if __name__ == "__main__":
    update_indexes_0730()
