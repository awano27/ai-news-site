import json
import os
from pathlib import Path

def update_indexes():
    """Update day_slides_index.html with new slide entry for 01/04"""
    
    # Read the current index file
    index_path = "presentations/day_slides_index.html"
    
    if not os.path.exists(index_path):
        print(f"Error: {index_path} not found")
        return
    
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Create the new slide HTML entry for 01/04
    new_slide_html = '''                        <li>
                              <a href="day_slides/day_slide_2026_01_04.html" class="slide-link">
                                    <span class="date">2026/01/04</span>
                                    <span class="slide-title">DeepTutor: 次世代パーソナル学習アシスタント</span>
                              </a>
                        </li>
'''
    
    # Find the position right after <ul class="slides"> and insert the new entry
    import re
    
    # Pattern to find the opening of the slides list
    pattern = r'(<ul class="slides">)\s*'
    
    if re.search(pattern, content):
        # Insert the new slide right after the opening ul tag
        content = re.sub(
            pattern,
            r'\1\n' + new_slide_html,
            content,
            count=1
        )
        
        # Write back to file
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Successfully updated {index_path}")
        print(f"Added entry for 2026/01/04: DeepTutor")
    else:
        print("Error: Could not find slides list container in index file")

if __name__ == "__main__":
    update_indexes()
