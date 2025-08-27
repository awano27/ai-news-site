"""
Daily AI News Slide Generator v2.0
Generates individual daily slides from structured JSON data with Reveal.js
Supports linking from main HTML reports to daily slide presentations
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader
import re

class DailySlideGenerator:
    """Generates individual daily slide presentations from JSON data"""
    
    def __init__(self, output_dir: Path = None):
        """Initialize the daily slide generator"""
        self.output_dir = output_dir or Path("presentations/daily_slides")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        template_dir = Path("templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def load_monthly_data(self, json_file: Path) -> Dict[str, Any]:
        """Load and parse the monthly JSON data file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"Loaded monthly data from {json_file}")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load JSON data: {e}")
            raise
    
    def extract_daily_items(self, monthly_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract items grouped by date from monthly data"""
        daily_items = {}
        
        for item in monthly_data.get('items', []):
            # Parse date from item metadata
            date_str = item.get('A', {}).get('date', '')
            if date_str:
                # Extract date part (YYYY-MM-DD format)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
                if date_match:
                    item_date = date_match.group(1)
                    if item_date not in daily_items:
                        daily_items[item_date] = []
                    daily_items[item_date].append(item)
        
        return daily_items
    
    def generate_daily_slide(self, slide_date: str, items: List[Dict[str, Any]], 
                           monthly_context: Dict[str, Any]) -> str:
        """Generate individual daily slide presentation"""
        
        # Process items for slide presentation
        processed_items = []
        for item in items:
            processed_item = {
                'title': item.get('G', {}).get('slide_title', 'AI News Update'),
                'summary': item.get('B', ''),
                'key_points': item.get('C', []),
                'impact_score': item.get('F', {}).get('impact_score', 0),
                'impact_reason': item.get('F', {}).get('reason', ''),
                'tech_links': item.get('D', {}).get('tech_links', []),
                'sources': item.get('H', []),
                'confidence': item.get('confidence', 0),
                'speaker_notes': item.get('G', {}).get('speaker_notes', ''),
                'visual_suggestion': item.get('G', {}).get('visual_suggestion', ''),
                'author': item.get('A', {}).get('author', {}).get('display', 'Unknown'),
                'handle': item.get('A', {}).get('author', {}).get('handle', ''),
                'url': item.get('A', {}).get('url', '')
            }
            processed_items.append(processed_item)
        
        # Sort by impact score (descending)
        processed_items.sort(key=lambda x: x['impact_score'], reverse=True)
        
        # Calculate daily statistics
        total_impact = sum(item['impact_score'] for item in processed_items)
        avg_confidence = sum(item['confidence'] for item in processed_items) / len(processed_items) if processed_items else 0
        
        # Prepare template data
        template_data = {
            'date': slide_date,
            'formatted_date': self._format_date(slide_date),
            'items': processed_items,
            'item_count': len(processed_items),
            'total_impact': total_impact,
            'avg_confidence': round(avg_confidence, 1),
            'top_item': processed_items[0] if processed_items else None,
            'monthly_context': monthly_context.get('narrative', ''),
            'themes': monthly_context.get('themes', []),
            'generated_at': datetime.now().isoformat()
        }
        
        # Generate slide HTML
        template = self.jinja_env.get_template('daily_slide.html')
        return template.render(**template_data)
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%Y年%m月%d日')
        except:
            return date_str
    
    def generate_all_daily_slides(self, json_file: Path) -> Dict[str, str]:
        """Generate all daily slides from monthly data"""
        monthly_data = self.load_monthly_data(json_file)
        daily_items = self.extract_daily_items(monthly_data)
        
        generated_slides = {}
        
        for slide_date, items in daily_items.items():
            slide_html = self.generate_daily_slide(slide_date, items, monthly_data)
            
            # Save slide file
            filename = f"daily_slide_{slide_date.replace('-', '_')}.html"
            output_path = self.output_dir / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(slide_html)
            
            generated_slides[slide_date] = filename
            self.logger.info(f"Generated daily slide: {filename}")
        
        return generated_slides
    
    def generate_slide_index(self, generated_slides: Dict[str, str], 
                           monthly_data: Dict[str, Any]) -> str:
        """Generate navigation index for all daily slides"""
        
        # Sort dates descending
        sorted_dates = sorted(generated_slides.keys(), reverse=True)
        
        slide_entries = []
        for slide_date in sorted_dates:
            filename = generated_slides[slide_date]
            
            # Find corresponding daily_top entry
            daily_entry = None
            for entry in monthly_data.get('daily_top', []):
                if entry.get('date') == slide_date:
                    daily_entry = entry
                    break
            
            slide_entries.append({
                'date': slide_date,
                'formatted_date': self._format_date(slide_date),
                'filename': filename,
                'title': daily_entry.get('title', 'Daily AI News') if daily_entry else 'Daily AI News',
                'url': f"daily_slides/{filename}"
            })
        
        index_data = {
            'slides': slide_entries,
            'total_slides': len(slide_entries),
            'date_range': monthly_data.get('window', {}),
            'themes': monthly_data.get('themes', []),
            'generated_at': datetime.now().isoformat()
        }
        
        template = self.jinja_env.get_template('daily_slide_index.html')
        return template.render(**index_data)
    
    def create_link_integration(self, generated_slides: Dict[str, str]) -> List[Dict[str, str]]:
        """Create link data for integration into existing HTML reports"""
        
        links = []
        for slide_date, filename in generated_slides.items():
            links.append({
                'date': slide_date,
                'formatted_date': self._format_date(slide_date),
                'url': f"daily_slides/{filename}",
                'title': f"{self._format_date(slide_date)}のスライド"
            })
        
        # Sort by date descending
        links.sort(key=lambda x: x['date'], reverse=True)
        return links

def main():
    """Main execution function"""
    logging.basicConfig(level=logging.INFO)
    
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
        
    except Exception as e:
        print(f"Error generating slides: {e}")
        raise

if __name__ == "__main__":
    main()