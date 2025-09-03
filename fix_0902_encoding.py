#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Fix encoding for 9/2 slide"""

import os
import sys

def fix_slide_encoding():
    """Fix UTF-8 encoding issues in the 9/2 slide"""
    
    slide_path = r"C:\Users\yoshitaka\ai-news-site\presentations\day_slides\day_slide_2025_09_02.html"
    
    # Read the file with proper encoding detection
    content = None
    try:
        # Try UTF-8 first
        with open(slide_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            # Try with cp932 (Shift-JIS)
            with open(slide_path, 'r', encoding='cp932') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            with open(slide_path, 'r', encoding='latin-1') as f:
                content = f.read()
    
    if content:
        # Fix common encoding issues
        content = content.replace('2025蟷ｴ09譛・2譌･', '2025年09月02日')
        content = content.replace('導 MiniCPM-V 4.5 繝｢繝舌う繝ｫAI髱ｩ蜻ｽ', '📱 MiniCPM-V 4.5 モバイルAI革命')
        content = content.replace('繝｢繝舌う繝ｫ', 'モバイル')
        content = content.replace('髱ｩ蜻ｽ', '革命')
        content = content.replace('蟄ｦ遲・', '学習')
        content = content.replace('繝代Λ繝｡', 'パラメ')
        content = content.replace('繧ｪ繝ｼ繝励Φ繧ｽ繝ｼ繧ｹ', 'オープンソース')
        
        # Write back with UTF-8 BOM to ensure proper encoding
        with open(slide_path, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        
        print("✅ Encoding fixed successfully!")
        print(f"File: {slide_path}")
        
        # Verify the fix
        with open(slide_path, 'r', encoding='utf-8') as f:
            first_lines = f.readlines()[:10]
            for i, line in enumerate(first_lines, 1):
                if 'title' in line.lower():
                    print(f"Line {i}: {line.strip()}")
                    
    else:
        print("❌ Could not read the file")

if __name__ == "__main__":
    fix_slide_encoding()