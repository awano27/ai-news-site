#!/usr/bin/env python3
"""Fix link clickability issues in all day slides by updating reveal.js settings and CSS"""

import re
from pathlib import Path

def fix_slide_links(file_path):
    """Fix link clickability in a single slide file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Update Reveal.initialize to include mouseWheel, hideInactiveCursor, and disableLayout
    reveal_pattern = r'(Reveal\.initialize\(\{[^}]+)'
    reveal_match = re.search(reveal_pattern, content, re.DOTALL)
    
    if reveal_match:
        init_block = reveal_match.group(1)
        
        # Check if these settings are already present
        if 'mouseWheel' not in init_block:
            # Add the new settings before the closing
            content = content.replace(
                init_block,
                init_block.rstrip() + ',\n            mouseWheel: false,\n            hideInactiveCursor: false,\n            disableLayout: true'
            )
    
    # 2. Add pointer-events CSS if not present
    if 'pointer-events: auto !important' not in content:
        # Find .reveal .source-link CSS block
        source_link_pattern = r'(\.reveal \.source-link\s*\{[^}]+)'
        source_link_match = re.search(source_link_pattern, content)
        
        if source_link_match:
            css_block = source_link_match.group(1)
            
            # Add pointer-events and z-index if not present
            if 'pointer-events' not in css_block:
                new_css_block = css_block.rstrip() + '''
            position: relative;
            z-index: 10;
            pointer-events: auto !important;
            cursor: pointer;'''
                content = content.replace(css_block, new_css_block)
    
    # 3. Add general link clickability CSS if not present
    if '.reveal a {' not in content and 'pointer-events: auto !important' not in content:
        # Find a good place to insert the CSS (after .reveal .source-links)
        source_links_pattern = r'(\.reveal \.source-links\s*\{[^}]+\})'
        source_links_match = re.search(source_links_pattern, content)
        
        if source_links_match:
            insertion_point = source_links_match.end()
            new_css = '''
        
        /* Ensure all links are clickable */
        .reveal a {
            pointer-events: auto !important;
            cursor: pointer;
        }'''
            content = content[:insertion_point] + new_css + content[insertion_point:]
    
    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Apply link clickability fixes to all day slides"""
    slides_dir = Path('presentations/day_slides')
    
    if not slides_dir.exists():
        print(f"Error: {slides_dir} directory not found")
        return
    
    slide_files = list(slides_dir.glob('day_slide_*.html'))
    print(f"Found {len(slide_files)} slide files")
    
    fixed_count = 0
    for slide_file in slide_files:
        print(f"Processing {slide_file.name}...", end=' ')
        if fix_slide_links(slide_file):
            print("✅ Fixed")
            fixed_count += 1
        else:
            print("⏭️  Already OK")
    
    print(f"\n✨ Fixed {fixed_count} slides")
    print("🔗 All source links should now be clickable!")

if __name__ == '__main__':
    main()