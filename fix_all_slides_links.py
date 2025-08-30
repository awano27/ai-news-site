#!/usr/bin/env python3
"""Apply link clickability fixes to ALL day slides"""

import re
from pathlib import Path

def fix_reveal_init(content):
    """Fix Reveal.initialize settings"""
    # Find Reveal.initialize block
    pattern = r'(Reveal\.initialize\(\{[^}]+)\}'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        init_block = match.group(1)
        
        # Check if fixes are already present
        if 'mouseWheel' not in init_block:
            # Remove any trailing whitespace/comma and add new settings
            new_init = init_block.rstrip().rstrip(',')
            new_init += ''',
            mouseWheel: false,
            hideInactiveCursor: false,
            disableLayout: true'''
            
            content = content.replace(match.group(0), new_init + '}')
            return content, True
    
    return content, False

def fix_source_link_css(content):
    """Fix source-link CSS for clickability"""
    changed = False
    
    # Fix .reveal .source-link
    pattern = r'(\.reveal \.source-link\s*\{[^}]+)'
    match = re.search(pattern, content)
    
    if match:
        css_block = match.group(1)
        if 'pointer-events: auto' not in css_block:
            new_css = css_block.rstrip()
            # Add new properties if not present
            if 'position: relative' not in css_block:
                new_css += '\n            position: relative;'
            if 'z-index' not in css_block:
                new_css += '\n            z-index: 10;'
            if 'pointer-events' not in css_block:
                new_css += '\n            pointer-events: auto !important;'
            if 'cursor: pointer' not in css_block:
                new_css += '\n            cursor: pointer;'
            
            content = content.replace(match.group(1), new_css)
            changed = True
    
    # Fix .reveal .source-links
    pattern = r'(\.reveal \.source-links\s*\{[^}]+)'
    match = re.search(pattern, content)
    
    if match:
        css_block = match.group(1)
        if 'position: relative' not in css_block:
            new_css = css_block.rstrip()
            new_css += '\n            position: relative;\n            z-index: 10;'
            content = content.replace(match.group(1), new_css)
            changed = True
    
    # Add general link fix if not present
    if '.reveal a {' not in content and 'pointer-events: auto !important' not in content:
        # Find a good insertion point
        insertion_patterns = [
            r'(\.reveal \.source-links\s*\{[^}]+\})',
            r'(\.reveal \.source-link:hover\s*\{[^}]+\})',
            r'(</style>)'
        ]
        
        for pattern in insertion_patterns:
            match = re.search(pattern, content)
            if match:
                insertion_point = match.start()
                new_css = '''
        
        /* Ensure all links are clickable */
        .reveal a {
            pointer-events: auto !important;
            cursor: pointer;
        }
        
'''
                content = content[:insertion_point] + new_css + content[insertion_point:]
                changed = True
                break
    
    return content, changed

def fix_slide_file(file_path):
    """Apply all fixes to a single slide file"""
    print(f"Processing {file_path.name}...", end=' ')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content, reveal_fixed = fix_reveal_init(content)
        content, css_fixed = fix_source_link_css(content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            fixes = []
            if reveal_fixed:
                fixes.append("Reveal.js")
            if css_fixed:
                fixes.append("CSS")
            
            print(f"✅ Fixed ({', '.join(fixes)})")
            return True
        else:
            print("⏭️  Already OK")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Fix all day slides"""
    slides_dir = Path('presentations/day_slides')
    
    if not slides_dir.exists():
        print(f"Error: {slides_dir} directory not found")
        return
    
    # Get all slide files
    slide_files = sorted(slides_dir.glob('day_slide_*.html'))
    print(f"Found {len(slide_files)} slide files\n")
    
    fixed_files = []
    
    for slide_file in slide_files:
        if fix_slide_file(slide_file):
            fixed_files.append(slide_file.name)
    
    print(f"\n{'='*60}")
    print(f"✨ Fixed {len(fixed_files)} slides:")
    
    if fixed_files:
        for name in fixed_files:
            print(f"  - {name}")
        print("\n🔗 All source links should now be clickable!")
        print("\n📝 To commit these changes, run:")
        print("   git add presentations/day_slides/*.html")
        print('   git commit -m "fix: Ensure all slide source links are clickable"')
        print("   git push origin main")
    else:
        print("All slides were already properly configured!")

if __name__ == '__main__':
    main()