import re

def update_daily_slides_index():
    """Update daily_slides_index.html with new entry for 0107"""
    index_path = "daily_slides_index.html"

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # New entry HTML
    new_entry = '''        <div class="slide-card">
          <div class="slide-date">2026/01/07</div>
          <div class="slide-title">
            <a href="presentations/day_slides/day_slide_2026_01_07.html">NVIDIA Rubin AIプラットフォーム: AIファクトリーの再定義</a>
          </div>
          <div class="slide-desc">Blackwellの後継としてCES 2026で発表された次世代AIプラットフォームの全貌</div>
        </div>'''

    # Find the grid container and insert after the opening tag
    grid_pattern = r'(<div class="slides-grid">)'

    # Check if entry already exists
    if "day_slide_2026_01_07.html" in content:
        print("Entry for 0107 already exists in daily_slides_index.html")
        return

    # Insert new entry at the beginning of slides-grid
    content = re.sub(
        grid_pattern,
        r'\1\n' + new_entry,
        content,
        count=1
    )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated {index_path}")

def update_main_index():
    """Update main index.html with new day slide link"""
    index_path = "index.html"

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if entry already exists
    if "presentations/day_slides/day_slide_2026_01_07.html" in content:
        print("Entry for 0107 already exists in index.html")
        return

    # Find the day-slides section and add new link
    day_slides_pattern = r'(<div class="day-slides">.*?<h3>.*?</h3>.*?<div class="slide-list">)'

    new_link = '''
          <a href="presentations/day_slides/day_slide_2026_01_07.html" class="slide-link">
            <span class="slide-date-tag">2026/01/07</span>
            <span class="slide-title-text">NVIDIA Rubin AIプラットフォーム</span>
          </a>'''

    content = re.sub(
        day_slides_pattern,
        r'\1' + new_link,
        content,
        count=1,
        flags=re.DOTALL
    )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated {index_path}")

if __name__ == "__main__":
    update_daily_slides_index()
    update_main_index()
    print("Index update complete!")
