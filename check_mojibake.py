#!/usr/bin/env python3
"""Check all day slides for mojibake (文字化け) encoding issues"""

import re
from pathlib import Path

# Common mojibake patterns in Japanese text
MOJIBAKE_PATTERNS = [
    r'[^\x00-\x7F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u002D\u0020-\u007E]',  # Invalid chars
    r'�',  # Replacement character
    r'縺[ァ-ッ]',  # Common Shift_JIS to UTF-8 corruption  
    r'鬆[い-ん]',  # More corruption patterns
    r'讀[懊-懐]',  # Another pattern
    r'莠[コ-ッ]',  # Yet another pattern
    r'縲[愛-移]',  # More patterns
    r'縺[い-ん]',  # Hiragana corruption
    r'縺[ェ-ョ]',  # Katakana corruption
    r'縺[ｧ-ｯ]',   # Half-width corruption
]

def check_slide_for_mojibake(file_path):
    """Check a single slide for mojibake issues"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        line_num = 1
        
        for line in content.split('\n'):
            for pattern in MOJIBAKE_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    issues.append({
                        'line': line_num,
                        'pattern': pattern,
                        'text': match.group(),
                        'context': line.strip()[:100]  # First 100 chars of line
                    })
            line_num += 1
        
        return issues
        
    except UnicodeDecodeError:
        return [{'line': 0, 'pattern': 'ENCODING_ERROR', 'text': 'File encoding issue', 'context': 'Cannot read file with UTF-8'}]
    except Exception as e:
        return [{'line': 0, 'pattern': 'READ_ERROR', 'text': str(e), 'context': 'Error reading file'}]

def main():
    """Check all day slides for mojibake"""
    slides_dir = Path('presentations/day_slides')
    
    if not slides_dir.exists():
        print(f"Error: {slides_dir} directory not found")
        return
    
    slide_files = sorted(slides_dir.glob('day_slide_*.html'))
    print(f"🔍 Checking {len(slide_files)} slide files for mojibake (文字化け)")
    print("=" * 70)
    
    problematic_files = []
    total_issues = 0
    
    for slide_file in slide_files:
        print(f"\nChecking {slide_file.name}...", end=' ')
        
        issues = check_slide_for_mojibake(slide_file)
        
        if issues:
            print(f"❌ Found {len(issues)} issue(s)")
            problematic_files.append((slide_file, issues))
            total_issues += len(issues)
            
            # Show first few issues as examples
            for issue in issues[:3]:  # Show max 3 examples
                print(f"  Line {issue['line']}: {issue['text']} in '{issue['context']}'")
            
            if len(issues) > 3:
                print(f"  ... and {len(issues) - 3} more issues")
        else:
            print("✅ Clean")
    
    print("\n" + "=" * 70)
    
    if problematic_files:
        print(f"\n❌ SUMMARY: Found mojibake in {len(problematic_files)} files ({total_issues} total issues)")
        print("\nProblematic files:")
        
        for file_path, issues in problematic_files:
            print(f"  - {file_path.name}: {len(issues)} issues")
        
        print(f"\n🔧 These files need encoding repair:")
        for file_path, issues in problematic_files:
            print(f"  - {file_path.name}")
            
        return problematic_files
    else:
        print("\n✅ All slides are clean - no mojibake found!")
        return []

if __name__ == '__main__':
    main()