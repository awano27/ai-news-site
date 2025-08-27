#!/usr/bin/env python3
"""Simple wrapper to run slide generation"""

import os
import sys
from pathlib import Path

# Set working directory
os.chdir('C:\\Users\\yoshitaka\\ai-news-site')

# Import and run the slide generator
sys.path.insert(0, str(Path.cwd()))

# Import the generator class
from generate_all_day_slides import ComprehensiveDaySlideGenerator

# Create and run the generator
print("Starting comprehensive day slide generation...")
generator = ComprehensiveDaySlideGenerator()

# Process all day files
day_dir = Path('C:\\Users\\yoshitaka\\input\\day')
slides_data = {}

for file_path in sorted(day_dir.glob('*.txt')):
    print(f"Processing {file_path.name}...")
    try:
        slide_data = generator.parse_day_file(file_path)
        if slide_data:
            slides_data[slide_data['date']] = slide_data
            # Generate individual slide
            html_content = generator.generate_slide(slide_data)
            output_file = generator.output_dir / f"day_slide_{slide_data['date'].replace('-', '_')}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Generated: {output_file}")
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")

# Create unified index
print("Creating unified index...")
index_content = generator.create_ranking_style_index(slides_data)
index_file = Path('presentations/day_slides_index.html')
with open(index_file, 'w', encoding='utf-8') as f:
    f.write(index_content)

print(f"Generated unified index: {index_file}")
print(f"Total slides generated: {len(slides_data)}")
print("Done!")