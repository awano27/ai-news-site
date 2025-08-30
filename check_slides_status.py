#!/usr/bin/env python3
"""Check which slides need link fixes"""

from pathlib import Path

def check_slide(file_path):
    """Check if a slide needs fixes"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_source_links = 'class="source-link"' in content
    has_reveal_fix = 'mouseWheel' in content and 'disableLayout' in content
    has_css_fix = 'pointer-events: auto' in content
    
    return has_source_links, has_reveal_fix, has_css_fix

def main():
    slides_dir = Path('presentations/day_slides')
    slide_files = sorted(slides_dir.glob('day_slide_*.html'))
    
    needs_fix = []
    already_fixed = []
    no_links = []
    
    for slide_file in slide_files:
        has_links, has_reveal, has_css = check_slide(slide_file)
        
        if has_links:
            if has_reveal and has_css:
                already_fixed.append(slide_file.name)
            else:
                needs_fix.append(slide_file.name)
        else:
            no_links.append(slide_file.name)
    
    print(f"🔍 Slide Analysis Report")
    print(f"{'='*60}")
    print(f"\n✅ Already Fixed ({len(already_fixed)}):")
    for name in already_fixed:
        print(f"  - {name}")
    
    print(f"\n⚠️  Needs Fix ({len(needs_fix)}):")
    for name in needs_fix:
        print(f"  - {name}")
    
    print(f"\n📄 No Source Links ({len(no_links)}):")
    for name in no_links[:5]:  # Show only first 5
        print(f"  - {name}")
    if len(no_links) > 5:
        print(f"  ... and {len(no_links)-5} more")

if __name__ == '__main__':
    main()