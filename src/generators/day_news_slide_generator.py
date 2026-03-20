"""
Day News Slide Generator
Generates individual slides from day-specific AI news files
Compatible with ranking report integration
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader
from src.utils.sanitize import sanitize_html
import json

class DayNewsSlideGenerator:
    """Generates slide presentations from day-specific AI news files"""
    
    def __init__(self, output_dir: Path = None):
        """Initialize the day news slide generator"""
        self.output_dir = output_dir or Path("presentations/day_slides")
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
        
    def parse_day_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a day news file and extract structured information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract date from filename
            filename = file_path.stem
            # Attempt to parse date from filename (e.g., 0826 or 20250826)
            year = "2025"
            month = "01"
            day = "01"
            
            if len(filename) >= 4:
                if len(filename) == 4: # 0826
                    month = filename[0:2]
                    day = filename[2:4]
                elif len(filename) == 8: # 20250826
                    year = filename[0:4]
                    month = filename[4:6]
                    day = filename[6:8]
                date_str = f"{year}-{month}-{day}"
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            formatted_date = datetime.now().strftime('%Y年%m月%d日')
            try:
                formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y年%m月%d日')
            except Exception:
                pass

            # Parse the content structure
            parsed_data = self._parse_news_content(content, date_str, formatted_date)
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Failed to parse file {file_path}: {e}")
            return self._create_fallback_data(file_path)
    
    def _parse_news_content(self, content: str, date_str: str, formatted_date: str) -> Dict[str, Any]:
        """Parse the news content and extract key information"""
        
        # Extract title/main topic (first major heading or TL;DR)
        title_patterns = [
            r'### (.+?)(?:\n|$)',  # ### heading
            r'\*\*TL;DR\*\*[・・]\s*(.+?)(?:\n|$)',  # TL;DR content
            r'# (.+?)(?:\n|$)',  # # heading
            r'## (.+?)(?:\n|$)',  # ## heading
        ]
        
        title = "AIニュースハイライト"
        for pattern in title_patterns:
            match = re.search(pattern, content)
            if match:
                title = match.group(1).strip()
                # Clean up markdown formatting
                title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)
                title = re.sub(r'\*(.+?)\*', r'\1', title)
                break
        
        # Extract summary/TL;DR content
        summary = self._extract_summary(content)
        
        # Extract key points
        key_points = self._extract_key_points(content)
        
        # Extract evaluation scores if available
        evaluation = self._extract_evaluation(content)
        
        # Extract technical details
        technical_details = self._extract_technical_details(content)
        
        # Extract sources/links
        sources = self._extract_sources(content)
        
        return {
            'date': date_str,
            'formatted_date': formatted_date,
            'title': title,
            'summary': summary,
            'key_points': key_points,
            'evaluation': evaluation,
            'technical_details': technical_details,
            'sources': sources,
            'raw_content': content[:2000] + "..." if len(content) > 2000 else content,
            'confidence': evaluation.get('overall_confidence', 85),
            'impact_score': evaluation.get('impact_score', 75)
        }
    
    def _extract_summary(self, content: str) -> str:
        """Extract main summary from content"""
        # Look for TL;DR content
        tldr_pattern = r'\*\*TL;DR\*\*[・・]\s*([^#\n]+?)(?:\n\n|\n---|\n##|$)'
        match = re.search(tldr_pattern, content, re.DOTALL)
        if match:
            summary = match.group(1).strip()
            # Clean markdown
            summary = re.sub(r'\*\*(.+?)\*\*', r'\1', summary)
            summary = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', summary)  # Remove links
            return summary[:500] + "..." if len(summary) > 500 else summary
        
        # Look for first paragraph after title
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#') and not line.startswith('---'):
                if len(line) > 50:  # Substantial content
                    summary = line.strip()
                    summary = re.sub(r'\*\*(.+?)\*\*', r'\1', summary)
                    return summary[:500] + "..." if len(summary) > 500 else summary
        
        return "AIニュースの詳細な分析と評価を提供しています。"
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        key_points = []
        
        # Look for bullet points
        bullet_patterns = [
            r'^[-*]\s+(.+?)$',  # - or * bullets
            r'^\d+\.\s+(.+?)$',  # numbered lists
        ]
        
        lines = content.split('\n')
        for line in lines:
            for pattern in bullet_patterns:
                match = re.search(pattern, line.strip())
                if match:
                    point = match.group(1).strip()
                    # Clean markdown
                    point = re.sub(r'\*\*(.+?)\*\*', r'\1', point)
                    point = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', point)
                    if len(point) > 10:  # Filter out short entries
                        key_points.append(point)
                    if len(key_points) >= 5:  # Limit to 5 key points
                        break
            if len(key_points) >= 5:
                break
        
        # If no bullets found, extract from structured sections
        if not key_points:
            section_patterns = [
                r'#### (.+?)(?:\n|$)',
                r'### (.+?)(?:\n|$)',
            ]
            
            for pattern in section_patterns:
                matches = re.findall(pattern, content)
                for match in matches[:5]:
                    clean_match = re.sub(r'\*\*(.+?)\*\*', r'\1', match.strip())
                    if len(clean_match) > 10:
                        key_points.append(clean_match)
        
        return key_points[:5]  # Return max 5 points
    
    def _extract_evaluation(self, content: str) -> Dict[str, Any]:
        """Extract evaluation scores from content"""
        evaluation = {
            'engineer_score': 50,
            'business_score': 50,
            'overall_confidence': 85,
            'impact_score': 75
        }
        
        # Look for score patterns
        score_patterns = [
            r'エンジニア.*?(\d+)/10',
            r'ビジネス.*?(\d+)/10',
            r'スコア.*?(\d+)',
            r'評価.*?(\d+)',
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    score = int(matches[0]) * 10  # Convert to 100 scale
                    if 'エンジニア' in pattern:
                        evaluation['engineer_score'] = min(score, 100)
                    elif 'ビジネス' in pattern:
                        evaluation['business_score'] = min(score, 100)
                except ValueError:
                    continue
        
        # Calculate overall impact based on content indicators
        impact_indicators = [
            ('革新', 20),
            ('画期的', 25),
            ('重要', 15),
            ('注目', 10),
            ('発表', 10),
            ('リリース', 15),
        ]
        
        for indicator, points in impact_indicators:
            if indicator in content:
                evaluation['impact_score'] = min(evaluation['impact_score'] + points, 100)
        
        return evaluation
    
    def _extract_technical_details(self, content: str) -> Dict[str, Any]:
        """Extract technical details from content"""
        details = {
            'has_code': False,
            'has_api': False,
            'has_pricing': False,
            'companies': [],
            'technologies': []
        }
        
        # Check for API mentions
        api_terms = ['API', 'SDK', 'エンドポイント']
        if any(term in content for term in api_terms):
            details['has_api'] = True
        
        # Check for pricing
        pricing_terms = ['価格', '料金', '$', '円', '無料']
        if any(term in content for term in pricing_terms):
            details['has_pricing'] = True
        
        # Extract company names
        companies = ['Google', 'Microsoft', 'OpenAI', 'Adobe', 'Apple', 'Amazon', 'Meta', 'DeepMind', 'Anthropic']
        for company in companies:
            if company in content:
                details['companies'].append(company)
        
        # Extract technologies
        tech_terms = ['AI', 'LLM', 'GPT', 'Gemini', 'Claude', 'Excel', 'API', 'SDK']
        for tech in tech_terms:
            if tech in content:
                details['technologies'].append(tech)
        
        return details
    
    def _extract_sources(self, content: str) -> List[str]:
        """Extract source URLs from content"""
        sources = []
        
        # Extract markdown links
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        matches = re.findall(link_pattern, content)
        
        for title, url in matches:
            if url.startswith('http'):
                sources.append(url)
        
        # Extract direct URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        direct_urls = re.findall(url_pattern, content)
        sources.extend(direct_urls)
        
        # Remove duplicates and limit
        unique_sources = list(dict.fromkeys(sources))[:10]
        return unique_sources
    
    def _create_fallback_data(self, file_path: Path) -> Dict[str, Any]:
        """Create fallback data for unparseable files"""
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'formatted_date': datetime.now().strftime('%Y年%m月%d日'),
            'title': f"AIニュース - {file_path.stem}",
            'summary': "AIニュースの詳細な分析が含まれています。",
            'key_points': ["詳細な分析", "技術的評価", "ビジネス影響評価"],
            'evaluation': {'engineer_score': 50, 'business_score': 50, 'impact_score': 70, 'overall_confidence': 80},
            'technical_details': {'has_code': False, 'has_api': False, 'companies': [], 'technologies': []},
            'sources': [],
            'raw_content': "ファイルの解析に問題が発生しました。",
            'confidence': 80,
            'impact_score': 70
        }
    
    def generate_slide(self, day_data: Dict[str, Any]) -> str:
        """Generate slide HTML from day data"""
        template_data = {
            **day_data,
            'generated_at': datetime.now().isoformat(),
            'slide_id': day_data['date'].replace('-', '_')
        }
        
        template = self.jinja_env.get_template('day_news_slide.html')
        return template.render(**template_data)
    
    def process_day_folder(self, day_folder: Path) -> Dict[str, str]:
        """Process all files in day folder and generate slides"""
        generated_slides = {}
        
        if not day_folder.exists():
            self.logger.error(f"Day folder not found: {day_folder}")
            return generated_slides
        
        # Get all .txt files
        txt_files = list(day_folder.glob('*.txt'))
        self.logger.info(f"Found {len(txt_files)} files to process")
        
        for txt_file in txt_files:
            try:
                # Parse the file
                day_data = self.parse_day_file(txt_file)
                
                # Generate slide
                slide_html = self.generate_slide(day_data)
                
                # Save slide
                filename = f"day_slide_{day_data['date'].replace('-', '_')}.html"
                output_path = self.output_dir / filename
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(sanitize_html(slide_html))
                
                generated_slides[day_data['date']] = {
                    'filename': filename,
                    'title': day_data['title'],
                    'date': day_data['date'],
                    'formatted_date': day_data['formatted_date'],
                    'impact_score': day_data['impact_score'],
                    'confidence': day_data['confidence']
                }
                
                self.logger.info(f"Generated slide: {filename}")
                
            except Exception as e:
                self.logger.error(f"Failed to process {txt_file}: {e}")
                continue
        
        return generated_slides
    
    def generate_index_page(self, generated_slides: Dict[str, Dict]) -> str:
        """Generate index page for all day slides"""
        
        # Sort slides by date (descending)
        sorted_slides = sorted(
            generated_slides.items(),
            key=lambda x: x[0],
            reverse=True
        )
        
        index_data = {
            'slides': [slide_info for _, slide_info in sorted_slides],
            'total_slides': len(generated_slides),
            'generated_at': datetime.now().isoformat(),
            'date_range': {
                'start': min(generated_slides.keys()) if generated_slides else None,
                'end': max(generated_slides.keys()) if generated_slides else None
            }
        }
        
        template = self.jinja_env.get_template('day_slides_index.html')
        return template.render(**index_data)

def main():
    """Main execution function"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize generator
    generator = DayNewsSlideGenerator()
    
    # Process day folder
    day_folder = Path("input/day")
    
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
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(sanitize_html(index_html))
        print(f"Generated index page: {index_path}")
        
        print("\nGenerated slides:")
        for date, info in generated_slides.items():
            print(f"  {info['formatted_date']}: {info['title']} (Impact: {info['impact_score']})")
        
    except Exception as e:
        print(f"Error generating slides: {e}")
        raise

if __name__ == "__main__":
    main()
