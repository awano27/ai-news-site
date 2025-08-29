#!/usr/bin/env python3
"""
Quick script to run the day news slide generator
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from generators.day_news_slide_generator import DayNewsSlideGenerator

def main():
    logging.basicConfig(level=logging.INFO)
    print("Starting Day News Slide Generator...")
    
    # Initialize generator
    generator = DayNewsSlideGenerator()
    
    # Process day folder
    day_folder = Path("C:/Users/yoshitaka/input/day")
    
    if not day_folder.exists():
        print(f"Day folder not found: {day_folder}")
        return
    
    try:
        # Generate all day slides
        generated_slides = generator.process_day_folder(day_folder)
        print(f"Generated {len(generated_slides)} day slides")
        
        # Generate index page
        index_html = generator.generate_index_page(generated_slides)
        index_path = Path("presentations/day_slides_index.html")
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        print(f"Generated index page: {index_path}")
        
        print("\nGenerated slides:")
        for date, info in generated_slides.items():
            print(f"  {info['formatted_date']}: {info['title']} (Impact: {info['impact_score']})")
        
        print(f"\nAll slides saved to: {generator.output_dir}")
        print(f"Index page: {index_path}")
        
    except Exception as e:
        print(f"Error generating slides: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()