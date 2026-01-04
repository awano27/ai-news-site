import json
import os
from pathlib import Path

def update_indexes():
    """Update day_slides_index.html with new slide entry"""
    
    # Define the new slide entry
    new_entry = {
        "date": "2026/01/03",
        "date_jp": "2026年1月3日",
        "title": "AI Orchestrator Playbook",
        "subtitle": "Claude Codeの生みの親が実践する「AI開発パートナー」戦略",
        "url": "day_slides/day_slide_2026_01_03.html",
        "impact_score": 95,
        "confidence": 90
    }
    
    # Read the current index file
    index_path = "presentations/day_slides_index.html"
    
    if not os.path.exists(index_path):
        print(f"Error: {index_path} not found")
        return
    
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the slides data section
    # Look for the pattern where slides are listed
    import re
    
    # Create the new slide HTML entry
    new_slide_html = f'''
        <div class="slide-card" data-date="2026-01-03" data-impact="{new_entry['impact_score']}">
          <div class="slide-header">
            <span class="slide-date">{new_entry['date_jp']}</span>
            <span class="slide-badge">Impact: {new_entry['impact_score']}</span>
          </div>
          <h3 class="slide-title">{new_entry['title']}</h3>
          <p class="slide-subtitle">{new_entry['subtitle']}</p>
          <a href="{new_entry['url']}" class="slide-link">スライドを見る →</a>
        </div>
'''
    
    # Find the slides container and add the new entry at the beginning
    # Look for the pattern: <div class="slides-grid">
    slides_grid_pattern = r'(<div class="slides-grid">)'
    
    if re.search(slides_grid_pattern, content):
        # Insert the new slide right after the opening div
        content = re.sub(
            slides_grid_pattern,
            r'\1' + new_slide_html,
            content,
            count=1
        )
        
        # Write back to file
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Successfully updated {index_path}")
        print(f"Added entry for {new_entry['date_jp']}: {new_entry['title']}")
    else:
        print("Error: Could not find slides-grid container in index file")

if __name__ == "__main__":
    update_indexes()
