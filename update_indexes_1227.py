import os

def update_indexes_1227():
    today_str = "2025-12-27"
    date_slash = "2025/12/27"
    title = "LearnLM: すべての学習者に『最高の家庭教師』を — Google AIによる教育革命"
    
    # URL friendly name (matching create_slide_1227.py output)
    slide_filename = f"day_slide_{today_str.replace('-', '_')}.html"
    slide_path = f"day_slides/{slide_filename}"
    
    # 1. Update presentations/day_slides_index.html
    index_path = "presentations/day_slides_index.html"
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if slide_filename not in content:
            new_entry = f"""                        <li><a href="{slide_path}" aria-describedby="slide-{today_str}"><span
                                          class="date">{date_slash}</span><span
                                          class="slide-title">{title}</span></a></li>\n"""
            # Insert after <ul>
            content = content.replace('<ul class="slides">', f'<ul class="slides">\n{new_entry}')
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {index_path}")
        else:
            print(f"Entry already exists in {index_path}")

    # 2. Update presentations/day_slides_list.html
    list_path = "presentations/day_slides_list.html"
    if os.path.exists(list_path):
        with open(list_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if slide_filename not in content:
            list_entry = f"""      <a href="https://awano27.github.io/ai-news-site/presentations/{slide_path}"
        class="slide-card">
        <span class="date-badge">{date_slash}</span>
        <div class="slide-title">{title}</div>
      </a>\n"""
            # Insert after <div class="slides-grid">
            content = content.replace('<div class="slides-grid">', f'<div class="slides-grid">\n{list_entry}')
            with open(list_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {list_path}")
        else:
            print(f"Entry already exists in {list_path}")

if __name__ == "__main__":
    update_indexes_1227()
