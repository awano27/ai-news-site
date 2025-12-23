import os

def update_indexes():
    index_path = "presentations/day_slides_index.html"
    list_path = "presentations/day_slides_list.html"
    
    date_slash = "2025/12/23"
    date_id = "2025-12-23"
    file_name = "day_slide_2025_12_23.html"
    title = "プロンプトはもう古い？AIの真価を引き出す「スキル」という新常識"

    # Update day_slides_index.html
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_item = f'        <li><a href="day_slides/{file_name}" aria-describedby="slide-{date_id}"><span\n              class="date">{date_slash}</span><span class="slide-title">{title}</span></a></li>\n'
        
        if file_name not in content:
            # Insert after <ul class="slides">
            content = content.replace('<ul class="slides">', f'<ul class="slides">\n{new_item}')
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {index_path}")
        else:
            print(f"Already exists in {index_path}")

    # Update day_slides_list.html
    if os.path.exists(list_path):
        with open(list_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_card = f'      <a href="https://awano27.github.io/ai-news-site/presentations/day_slides/{file_name}"\n        class="slide-card">\n        <span class="date-badge">{date_slash}</span>\n        <div class="slide-title">{title}</div>\n      </a>\n'
        
        if file_name not in content:
            # Insert after <!-- 12月分 -->
            content = content.replace('<!-- 12月分 -->', f'<!-- 12月分 -->\n{new_card}')
            with open(list_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {list_path}")
        else:
            print(f"Already exists in {list_path}")

if __name__ == "__main__":
    update_indexes()
