#!/usr/bin/env python3
"""Batch fix link clickability for specific slides with source links"""

import re
from pathlib import Path

# List of slides that need fixing (those with source-link class)
SLIDES_TO_FIX = [
    'day_slide_2025_08_03.html',
    'day_slide_2025_08_04.html', 
    'day_slide_2025_08_14.html',
    'day_slide_2025_08_15.html',
    'day_slide_2025_08_16.html',
    'day_slide_2025_08_17.html',
    'day_slide_2025_08_18.html',
    'day_slide_2025_08_19.html',
    'day_slide_2025_08_20.html',
    # 08_01, 08_10, 08_28 already fixed
]

def apply_fixes(file_path):
    """Apply all link clickability fixes"""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. Fix Reveal.initialize
    pattern = r'(Reveal\.initialize\(\{[^}]+)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        init_block = match.group(1)
        if 'mouseWheel' not in init_block:
            # Remove trailing whitespace/comma and add settings
            new_init = init_block.rstrip().rstrip(',')
            # Handle comments
            new_init = re.sub(r'\s*//[^\n]*', '', new_init)  # Remove inline comments
            new_init += ',\n            mouseWheel: false,\n            hideInactiveCursor: false,\n            disableLayout: true'
            content = content.replace(match.group(0), new_init + '}')
    
    # 2. Add pointer-events to source-link
    pattern = r'(\.reveal \.source-link\s*\{[^}]+)'
    match = re.search(pattern, content)
    if match:
        css_block = match.group(1)
        if 'pointer-events' not in css_block:
            new_css = css_block.rstrip() + '''
            position: relative;
            z-index: 10;
            pointer-events: auto !important;
            cursor: pointer;'''
            content = content.replace(match.group(1), new_css)
    
    # 3. Add general link CSS
    if '.reveal a {' not in content and 'source-link' in content:
        # Insert after source-link CSS
        pattern = r'(\.reveal \.source-link[^}]+\})'
        match = re.search(pattern, content)
        if match:
            insertion_point = match.end()
            new_css = '''

        /* Ensure all links are clickable */
        .reveal a {
            pointer-events: auto !important;
            cursor: pointer;
        }'''
            content = content[:insertion_point] + new_css + content[insertion_point:]
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed {file_path.name}")
        return True
    else:
        print(f"  ⏭️  {file_path.name} already OK")
        return False

def main():
    slides_dir = Path('presentations/day_slides')
    fixed_count = 0
    
    print("🔧 Fixing link clickability in slides with source links...")
    print("="*60)
    
    for slide_name in SLIDES_TO_FIX:
        slide_path = slides_dir / slide_name
        if slide_path.exists():
            if apply_fixes(slide_path):
                fixed_count += 1
        else:
            print(f"  ⚠️  {slide_name} not found")
    
    print("="*60)
    print(f"✨ Fixed {fixed_count} slides")
    
    if fixed_count > 0:
        print("\n📝 To commit, run:")
        print("   git add presentations/day_slides/*.html")
        print('   git commit -m "fix: Ensure all slide source links are clickable"')
        print("   git push origin main")

if __name__ == '__main__':
    main()