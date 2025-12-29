from pathlib import Path
import re

def update_indexes_1228():
    # 1. Update presentations/day_slides_index.html
    index_path = Path("presentations/day_slides_index.html")
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        
        # 新しいリストアイテムを作成
        new_item = """
        <li>
            <a href="day_slides/day_slide_2025_12_28.html" class="slide-link">
                <span class="date">2025.12.28</span>
                <span class="title">Code Is Written While You Sleep</span>
            </a>
        </li>"""
        
        # <ul class="slides">の直後に挿入（先頭に追加）
        if '<ul class="slides">' in content:
            # 既存のリストの先頭に追加するために、<ul class="slides"> の直後を置換
            content = content.replace('<ul class="slides">', '<ul class="slides">' + new_item)
            index_path.write_text(content, encoding="utf-8")
            print(f"Updated {index_path}")
        else:
            print(f"Warning: <ul class='slides'> not found in {index_path}")
    else:
        print(f"Error: {index_path} not found")

    # 2. Update public-pages/daily_slides_index.html (if exists)
    public_index_path = Path("public-pages/daily_slides_index.html")
    if public_index_path.exists():
        content = public_index_path.read_text(encoding="utf-8")
        
        new_item_public = """
        <li>
            <a href="https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_12_28.html" class="slide-link">
                <span class="date">2025.12.28</span>
                <span class="title">Code Is Written While You Sleep</span>
            </a>
        </li>"""
        
        if '<ul class="slides">' in content:
            content = content.replace('<ul class="slides">', '<ul class="slides">' + new_item_public)
            public_index_path.write_text(content, encoding="utf-8")
            print(f"Updated {public_index_path}")
        elif '<ul class="slide-list">' in content:
             content = content.replace('<ul class="slide-list">', '<ul class="slide-list">' + new_item_public)
             public_index_path.write_text(content, encoding="utf-8")
             print(f"Updated {public_index_path} (using slide-list)")

if __name__ == "__main__":
    update_indexes_1228()
