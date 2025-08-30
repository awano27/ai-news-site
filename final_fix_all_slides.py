#!/usr/bin/env python3
"""Final comprehensive fix for ALL slides with source links"""

import re
from pathlib import Path

def apply_all_fixes(file_path):
    """Apply comprehensive link fixes to a slide file"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. Fix Reveal.initialize - add the three critical settings
    if 'Reveal.initialize' in content and 'mouseWheel: false' not in content:
        # Find the Reveal.initialize block
        pattern = r'(Reveal\.initialize\(\{[^}]+)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            init_block = match.group(1)
            # Clean up and add new settings
            new_init = init_block.rstrip().rstrip(',')
            new_init += ',\n            mouseWheel: false,\n            hideInactiveCursor: false,\n            disableLayout: true'
            content = content.replace(match.group(0), new_init + '}')
    
    # 2. Fix ALL link CSS patterns (with and without .reveal prefix)
    # Fix .source-link or .reveal .source-link
    if 'source-link' in content and 'pointer-events: auto !important' not in content:
        patterns = [
            r'(\.reveal \.source-link\s*\{[^}]+)',
            r'(\.source-link\s*\{[^}]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                css_block = match.group(1)
                if 'pointer-events' not in css_block:
                    new_css = css_block.rstrip()
                    if 'position: relative' not in css_block:
                        new_css += '\n            position: relative;'
                    if 'z-index' not in css_block:
                        new_css += '\n            z-index: 10;'
                    new_css += '\n            pointer-events: auto !important;\n            cursor: pointer;'
                    content = content.replace(match.group(1), new_css)
                    break
            else:
                continue
            break
    
    # 3. Fix source-links container
    if 'source-links' in content:
        patterns = [
            r'(\.reveal \.source-links\s*\{[^}]+)',
            r'(\.source-links\s*\{[^}]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                css_block = match.group(1)
                if 'z-index: 10' not in css_block and 'z-index' not in css_block:
                    new_css = css_block.rstrip()
                    if 'position: relative' not in css_block:
                        new_css += '\n            position: relative;'
                    new_css += '\n            z-index: 10;'
                    content = content.replace(match.group(1), new_css)
                    break
    
    # 4. Add general link CSS
    if 'pointer-events: auto !important' in content and '.reveal a {' not in content:
        # Find good insertion point after source-link CSS
        insertion_patterns = [
            r'(\.source-link[^}]*\})',
            r'(\.reveal \.source-link[^}]*\})'
        ]
        
        for pattern in insertion_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                insertion_point = match.end()
                new_css = '''
        
        /* Ensure all links are clickable */
        .reveal a {
            pointer-events: auto !important;
            cursor: pointer;
        }'''
                content = content[:insertion_point] + new_css + content[insertion_point:]
                break
    
    # Write back if changed
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    slides_dir = Path('presentations/day_slides')
    
    # List of ALL slides with source links
    target_slides = [
        'day_slide_2025_08_14.html',
        'day_slide_2025_08_15.html',
        'day_slide_2025_08_16.html',
        'day_slide_2025_08_17.html',
        'day_slide_2025_08_18.html',
    ]
    
    print("🔧 Final fix for remaining slides with source links")
    print("=" * 60)
    
    fixed = []
    
    for slide_name in target_slides:
        slide_path = slides_dir / slide_name
        
        if not slide_path.exists():
            print(f"⚠️  {slide_name} not found")
            continue
        
        print(f"Fixing {slide_name}...", end=' ')
        
        if apply_all_fixes(slide_path):
            print("✅ Fixed")
            fixed.append(slide_name)
        else:
            print("⏭️  Already OK")
    
    print("\n" + "=" * 60)
    
    if fixed:
        print(f"\n✨ Fixed {len(fixed)} slides:")
        for name in fixed:
            print(f"  - {name}")
    
    print("\n✅ All slides with source links should now be clickable!")

if __name__ == '__main__':
    main()