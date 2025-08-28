#!/usr/bin/env python3
"""
Fix all problematic slides - Python version for better reliability
"""
import os
import re
from pathlib import Path

# List of problematic files from the analysis
PROBLEMATIC_FILES = [
    "day_slide_2025_07_30.html",  # Already fixed
    "day_slide_2025_08_01.html",  # Already fixed  
    "day_slide_2025_08_02.html", 
    "day_slide_2025_08_03.html",
    "day_slide_2025_08_04.html",
    "day_slide_2025_08_05.html",
    "day_slide_2025_08_06.html",
    "day_slide_2025_08_08.html",
    "day_slide_2025_08_09.html",
    "day_slide_2025_08_10.html",
    "day_slide_2025_08_11.html",
    "day_slide_2025_08_12.html",
    "day_slide_2025_08_13.html",
    "day_slide_2025_08_14.html",
    "day_slide_2025_08_15.html",
    "day_slide_2025_08_16.html",
    "day_slide_2025_08_17.html",
    "day_slide_2025_08_18.html",
    "day_slide_2025_08_21.html",
    "day_slide_2025_08_24.html",
    "day_slide_2025_08_25.html",
    "day_slide_2025_08_26.html"
]

def fix_slide_file(filepath):
    """Fix a single slide file"""
    if not os.path.exists(filepath):
        print(f"✗ File not found: {filepath}")
        return False
        
    try:
        # Read with UTF-8 encoding
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Fixing {os.path.basename(filepath)}...")
        
        # 1. Update reveal.js to 4.4.0
        content = re.sub(r'reveal\.js@4\.3\.1', 'reveal.js@4.4.0', content)
        
        # 2. Remove navigation slide sections
        content = re.sub(r'(?s)<!-- Navigation Slide -->.*?</section>', '', content)
        content = re.sub(r'(?s)<section>\s*<div class="navigation-card">.*?</section>', '', content)
        
        # 3. Remove navigation CSS
        content = re.sub(r'(?s)\.reveal \.navigation-card[^}]*}', '', content)
        content = re.sub(r'(?s)\.reveal \.nav-buttons[^}]*}', '', content)  
        content = re.sub(r'(?s)\.reveal \.nav-btn[^}]*}', '', content)
        content = re.sub(r'(?s)\.reveal \.nav-btn:hover[^}]*}', '', content)
        
        # 4. Ensure proper reveal.js controls config
        if 'controlsLayout' not in content:
            content = re.sub(
                r'(controls:\s*true[^,]*),',
                r'\1,\n            controlsLayout: \'edges\',\n            controlsBackArrows: \'faded\',',
                content
            )
        
        # 5. Write back with clean UTF-8 encoding
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✓ Fixed {os.path.basename(filepath)}")
        return True
        
    except Exception as e:
        print(f"✗ Error fixing {os.path.basename(filepath)}: {e}")
        return False

def main():
    """Main function"""
    print("=== Fixing ALL problematic slides ===")
    
    slides_dir = Path("presentations/day_slides")
    fixed_count = 0
    
    for filename in PROBLEMATIC_FILES:
        filepath = slides_dir / filename
        if fix_slide_file(filepath):
            fixed_count += 1
    
    print(f"\n=== Fixed {fixed_count} out of {len(PROBLEMATIC_FILES)} files ===")
    
    # Add and commit the changes
    print("\n=== Staging files for commit ===")
    os.system("git add presentations/day_slides/day_slide_*.html")
    
    return fixed_count

if __name__ == "__main__":
    main()