#!/usr/bin/env python3
"""
Recreate all problematic slides from scratch using the working 8/27 template
"""
import os
import re
from pathlib import Path
from datetime import datetime

# List of all problematic files to recreate
PROBLEMATIC_FILES = [
    "day_slide_2025_07_30.html",
    "day_slide_2025_08_01.html", 
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
    "day_slide_2025_08_24.html",  # Already recreated but include for consistency
    "day_slide_2025_08_25.html",
    "day_slide_2025_08_26.html"
]

# Date mapping for input files
DATE_MAPPING = {
    "day_slide_2025_07_30.html": "0730.txt",
    "day_slide_2025_08_01.html": "0801.txt",
    "day_slide_2025_08_02.html": "0802.txt",
    "day_slide_2025_08_03.html": "0803.txt",
    "day_slide_2025_08_04.html": "0804.txt",
    "day_slide_2025_08_05.html": "0805.txt",
    "day_slide_2025_08_06.html": "0806.txt",
    "day_slide_2025_08_08.html": "0808.txt",
    "day_slide_2025_08_09.html": "0809.txt",
    "day_slide_2025_08_10.html": "0810.txt",
    "day_slide_2025_08_11.html": "0811.txt",
    "day_slide_2025_08_12.html": "0812.txt",
    "day_slide_2025_08_13.html": "0813.txt",
    "day_slide_2025_08_14.html": "0814.txt",
    "day_slide_2025_08_15.html": "0815.txt",
    "day_slide_2025_08_16.html": "0816.txt",
    "day_slide_2025_08_17.html": "0817.txt",
    "day_slide_2025_08_18.html": "0818.txt",
    "day_slide_2025_08_21.html": "0821.txt",
    "day_slide_2025_08_24.html": "0824.txt",
    "day_slide_2025_08_25.html": "0825.txt",
    "day_slide_2025_08_26.html": "0826.txt"
}

def load_template():
    """Load the working template from 8/27 slide"""
    template_path = Path("presentations/day_slides/day_slide_2025_08_27.html")
    if not template_path.exists():
        raise FileNotFoundError("Template file day_slide_2025_08_27.html not found")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_content_data(input_file):
    """Load content data from input file"""
    input_path = Path("../input/day") / input_file
    if not input_path.exists():
        print(f"Warning: Input file {input_file} not found, using placeholder content")
        return {
            'title': 'AI News Analysis',
            'date': 'TBD',
            'summary': 'Content to be updated'
        }
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract key information from content
        lines = content.split('\n')
        title_line = next((line for line in lines if line.startswith('### ')), 'AI News Analysis')
        title = title_line.replace('### ', '') if title_line else 'AI News Analysis'
        
        return {
            'title': title,
            'date': extract_date_from_filename(input_file),
            'content': content[:1000] + '...' if len(content) > 1000 else content
        }
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return {
            'title': 'AI News Analysis',
            'date': extract_date_from_filename(input_file),
            'summary': 'Content loading failed'
        }

def extract_date_from_filename(filename):
    """Extract formatted date from filename like 0824.txt -> 2025年8月24日"""
    match = re.search(r'(\d{2})(\d{2})\.txt', filename)
    if match:
        month, day = match.groups()
        return f"2025年{int(month)}月{int(day)}日"
    return "2025年"

def customize_template(template, filename, content_data):
    """Customize template with specific content"""
    # Extract date from filename for proper formatting
    date_match = re.search(r'day_slide_2025_(\d{2})_(\d{2})\.html', filename)
    if date_match:
        month, day = date_match.groups()
        formatted_date = f"2025年{int(month)}月{int(day)}日"
    else:
        formatted_date = content_data['date']
    
    # Customize the template
    customized = template
    
    # Update title
    customized = re.sub(
        r'<title>.*?</title>', 
        f'<title>{formatted_date} - {content_data["title"]}</title>', 
        customized
    )
    
    # Update date badge
    customized = re.sub(
        r'<div class="date-badge">.*?</div>', 
        f'<div class="date-badge">{formatted_date}</div>', 
        customized
    )
    
    # Update main title if needed
    customized = re.sub(
        r'<h1>.*?</h1>', 
        f'<h1>🚀 {content_data["title"][:50]}...</h1>', 
        customized
    )
    
    return customized

def recreate_slide(filename):
    """Recreate a single slide file"""
    try:
        print(f"Recreating {filename}...")
        
        # Load template
        template = load_template()
        
        # Load content data
        input_file = DATE_MAPPING.get(filename, "0827.txt")  # fallback
        content_data = load_content_data(input_file)
        
        # Customize template
        customized_html = customize_template(template, filename, content_data)
        
        # Write the new file
        output_path = Path("presentations/day_slides") / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(customized_html)
        
        print(f"✓ Successfully recreated {filename}")
        return True
        
    except Exception as e:
        print(f"✗ Error recreating {filename}: {e}")
        return False

def main():
    """Main function to recreate all slides"""
    print("=== Recreating ALL problematic slides ===")
    print(f"Files to recreate: {len(PROBLEMATIC_FILES)}")
    
    success_count = 0
    
    for filename in PROBLEMATIC_FILES:
        if recreate_slide(filename):
            success_count += 1
    
    print(f"\n=== Recreation Summary ===")
    print(f"Successfully recreated: {success_count}/{len(PROBLEMATIC_FILES)} files")
    
    if success_count == len(PROBLEMATIC_FILES):
        print("🎉 All slides successfully recreated!")
        return True
    else:
        print(f"⚠️ {len(PROBLEMATIC_FILES) - success_count} files failed to recreate")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)