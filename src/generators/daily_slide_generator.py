"""
Daily AI News Slide Generator v2.1 (safe)
Generates individual daily slides from structured JSON with Reveal.js
Now uses sanitize_text/sanitize_html and correct JA date format.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader
from src.utils.sanitize import sanitize_html, sanitize_text
import re


class DailySlideGenerator:
    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path("presentations/daily_slides")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        template_dir = Path("templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)
        self.logger = logging.getLogger(__name__)

    def load_monthly_data(self, json_file: Path) -> Dict[str, Any]:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.logger.info("Loaded monthly data from %s", json_file)
        return data

    def extract_daily_items(self, monthly_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        daily: Dict[str, List[Dict[str, Any]]] = {}
        for item in monthly_data.get('items', []):
            date_str = item.get('A', {}).get('date', '')
            if not date_str:
                continue
            m = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
            if not m:
                continue
            key = m.group(1)
            daily.setdefault(key, []).append(item)
        return daily

    def generate_daily_slide(self, slide_date: str, items: List[Dict[str, Any]], monthly_context: Dict[str, Any]) -> str:
        processed: List[Dict[str, Any]] = []
        for it in items:
            processed.append({
                'title': sanitize_text(it.get('G', {}).get('slide_title', 'AI News Update')),
                'summary': sanitize_text(it.get('B', '')),
                'key_points': it.get('C', []),
                'impact_score': it.get('F', {}).get('impact_score', 0),
                'impact_reason': sanitize_text(it.get('F', {}).get('reason', '')),
                'tech_links': it.get('D', {}).get('tech_links', []),
                'sources': it.get('H', []),
                'confidence': it.get('confidence', 0),
                'speaker_notes': sanitize_text(it.get('G', {}).get('speaker_notes', '')),
                'visual_suggestion': sanitize_text(it.get('G', {}).get('visual_suggestion', '')),
                'author': sanitize_text(it.get('A', {}).get('author', {}).get('display', 'Unknown')),
                'handle': sanitize_text(it.get('A', {}).get('author', {}).get('handle', '')),
                'url': it.get('A', {}).get('url', '')
            })
        processed.sort(key=lambda x: x['impact_score'], reverse=True)

        total_impact = sum(x['impact_score'] for x in processed)
        avg_conf = (sum(x['confidence'] for x in processed) / len(processed)) if processed else 0

        template_data = {
            'date': slide_date,
            'formatted_date': self._format_date(slide_date),
            'items': processed,
            'item_count': len(processed),
            'total_impact': total_impact,
            'avg_confidence': round(avg_conf, 1),
            'top_item': processed[0] if processed else None,
            'monthly_context': sanitize_text(monthly_context.get('narrative', '')),
            'themes': monthly_context.get('themes', []),
            'generated_at': datetime.now().isoformat()
        }
        html = self.jinja_env.get_template('daily_slide.html').render(**template_data)
        return sanitize_html(html)

    def _format_date(self, date_str: str) -> str:
        try:
            d = datetime.strptime(date_str, '%Y-%m-%d')
            return d.strftime('%Y年%m月%d日')
        except Exception:
            return date_str

    def generate_all_daily_slides(self, json_file: Path) -> Dict[str, str]:
        monthly = self.load_monthly_data(json_file)
        daily = self.extract_daily_items(monthly)
        generated: Dict[str, str] = {}
        for dt, items in daily.items():
            slide_html = self.generate_daily_slide(dt, items, monthly)
            fname = f"daily_slide_{dt.replace('-', '_')}.html"
            out = self.output_dir / fname
            with open(out, 'w', encoding='utf-8') as f:
                f.write(slide_html)
            generated[dt] = fname
            self.logger.info("Generated daily slide: %s", fname)
        return generated

    def generate_slide_index(self, generated_slides: Dict[str, str], monthly_data: Dict[str, Any]) -> str:
        sorted_dates = sorted(generated_slides.keys(), reverse=True)
        slide_entries = []
        for dt in sorted_dates:
            fname = generated_slides[dt]
            daily_entry = None
            for entry in monthly_data.get('daily_top', []):
                if entry.get('date') == dt:
                    daily_entry = entry
                    break
            title = sanitize_text(daily_entry.get('title', 'Daily AI News')) if daily_entry else 'Daily AI News'
            slide_entries.append({
                'date': dt,
                'formatted_date': self._format_date(dt),
                'filename': fname,
                'title': title,
                'url': f"daily_slides/{fname}"
            })
        index_data = {
            'slides': slide_entries,
            'total_slides': len(slide_entries),
            'date_range': monthly_data.get('window', {}),
            'themes': monthly_data.get('themes', []),
            'generated_at': datetime.now().isoformat()
        }
        tpl = self.jinja_env.get_template('daily_slide_index.html')
        return sanitize_html(tpl.render(**index_data))

    def create_link_integration(self, generated_slides: Dict[str, str]):
        links = []
        for dt, fname in generated_slides.items():
            links.append({
                'date': dt,
                'formatted_date': self._format_date(dt),
                'url': f"daily_slides/{fname}",
                'title': f"{self._format_date(dt)}のスライド"
            })
        links.sort(key=lambda x: x['date'], reverse=True)
        return links

def main():
    logging.basicConfig(level=logging.INFO)
    gen = DailySlideGenerator()
    json_file = Path("C:/Users/yoshitaka/input/monthly_data.json")
    if not json_file.exists():
        print(f"Data file not found: {json_file}")
        return
    generated = gen.generate_all_daily_slides(json_file)
    print(f"Generated {len(generated)} daily slides")
    monthly = gen.load_monthly_data(json_file)
    index_html = gen.generate_slide_index(generated, monthly)
    Path("presentations/day_slides_index.html").write_text(index_html, encoding='utf-8')
    print("Updated index")

if __name__ == '__main__':
    main()

