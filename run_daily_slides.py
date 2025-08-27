#!/usr/bin/env python3
"""
Quick script to run the daily slide generator
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from generators.daily_slide_generator import DailySlideGenerator

def main():
    logging.basicConfig(level=logging.INFO)
    print("Starting Daily Slide Generator...")
    
    # Initialize generator
    generator = DailySlideGenerator()
    
    # Load data and generate slides
    json_file = Path("C:/Users/yoshitaka/input/直近1か月データ.txt")
    
    if not json_file.exists():
        print(f"Data file not found: {json_file}")
        return
    
    try:
        # Generate all daily slides
        generated_slides = generator.generate_all_daily_slides(json_file)
        print(f"Generated {len(generated_slides)} daily slides")
        
        # Load monthly data for index
        monthly_data = generator.load_monthly_data(json_file)
        
        # Generate slide index
        index_html = generator.generate_slide_index(generated_slides, monthly_data)
        index_path = Path("presentations/daily_slides_index.html")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        print(f"Generated slide index: {index_path}")
        
        # Create link integration data
        links = generator.create_link_integration(generated_slides)
        print("Link integration data:")
        for link in links[:5]:  # Show first 5
            print(f"  {link['formatted_date']}: {link['url']}")
            
        print("\nDaily slides generated successfully!")
        
    except Exception as e:
        print(f"Error generating slides: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()