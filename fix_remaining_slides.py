#!/usr/bin/env python3
"""Fix link clickability for all remaining slides with source links"""

import re
from pathlib import Path

# All slides that have source-link class (from grep results)
SLIDES_WITH_LINKS = [
    'day_slide_2025_08_01.html',
    'day_slide_2025_08_03.html',  # Already done
    'day_slide_2025_08_04.html',
    'day_slide_2025_08_10.html',  # Already done
    'day_slide_2025_08_14.html',
    'day_slide_2025_08_15.html',
    'day_slide_2025_08_16.html',
    'day_slide_2025_08_17.html',
    'day_slide_2025_08_18.html',
    'day_slide_2025_08_19.html',  # Already done
    'day_slide_2025_08_20.html',  # Already done
    'day_slide_2025_08_28.html',  # Already done
]

def fix_slide(file_path):
    """Apply all link clickability fixes to a slide"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    fixes_applied = []
    
    # 1. Fix Reveal.initialize if not already fixed
    if 'mouseWheel: false' not in content:
        pattern = r'(Reveal\.initialize\(\{[^}]+)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            init_block = match.group(1)
            # Remove trailing stuff and add new settings
            new_init = init_block.rstrip().rstrip(',')
            new_init += ',\n            mouseWheel: false,\n            hideInactiveCursor: false,\n            disableLayout: true'
            content = content.replace(match.group(0), new_init + '}')
            fixes_applied.append('Reveal.js')
    
    # 2. Fix source-link CSS if needed
    if 'pointer-events: auto !important' not in content and 'source-link' in content:
        # Try both .reveal .source-link and just .source-link
        patterns = [
            r'(\.reveal \.source-link\s*\{[^}]+)',
            r'(\.source-link\s*\{[^}]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                css_block = match.group(1)
                if 'pointer-events' not in css_block:
                    new_css = css_block.rstrip()
                    new_css += '''\n            position: relative;
            z-index: 10;
            pointer-events: auto !important;
            cursor: pointer;'''
                    content = content.replace(match.group(1), new_css)
                    fixes_applied.append('source-link CSS')
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
                if 'z-index: 10' not in css_block:
                    new_css = css_block.rstrip()
                    new_css += '\n            position: relative;\n            z-index: 10;'
                    content = content.replace(match.group(1), new_css)
                    fixes_applied.append('source-links CSS')
                    break
    
    # 4. Add general link CSS if not present
    if '.reveal a {' not in content and 'a {' not in content.replace('.reveal a', '') and 'source-link' in content:
        # Find insertion point
        patterns = [
            r'(\.source-link:hover\s*\{[^}]+\})',
            r'(\.source-links\s*\{[^}]+\})',
            r'(\.source-link\s*\{[^}]+\})'
        ]
        
        for pattern in patterns:
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
                fixes_applied.append('general link CSS')
                break
    
    # Write back if changed
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return fixes_applied
    
    return None

def main():
    slides_dir = Path('presentations/day_slides')
    
    print("🔧 Fixing link clickability for all slides with source links")
    print("=" * 60)
    
    fixed_files = []
    already_ok = []
    
    for slide_name in SLIDES_WITH_LINKS:
        slide_path = slides_dir / slide_name
        
        if not slide_path.exists():
            print(f"⚠️  {slide_name} not found")
            continue
        
        print(f"Processing {slide_name}...", end=' ')
        
        fixes = fix_slide(slide_path)
        if fixes:
            print(f"✅ Fixed ({', '.join(fixes)})")
            fixed_files.append(slide_name)
        else:
            print("⏭️  Already OK")
            already_ok.append(slide_name)
    
    print("\n" + "=" * 60)
    print(f"\n📊 Summary:")
    print(f"  ✅ Fixed: {len(fixed_files)} files")
    print(f"  ⏭️  Already OK: {len(already_ok)} files")
    
    if fixed_files:
        print(f"\n🔧 Fixed files:")
        for name in fixed_files:
            print(f"  - {name}")
        
        print("\n📝 To commit all fixes, run:")
        print("   git add presentations/day_slides/*.html")
        print('   git commit -m "fix: Ensure ALL slide source links are clickable"')
        print("   git push origin main")
    else:
        print("\n✨ All slides were already properly configured!")

if __name__ == '__main__':
    main()