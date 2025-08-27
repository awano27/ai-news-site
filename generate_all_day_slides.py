#!/usr/bin/env python3
"""
Generate all day slides from input files
Creates comprehensive slide system matching ranking report design
"""

import sys
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

class ComprehensiveDaySlideGenerator:
    """Generate comprehensive day slides system"""
    
    def __init__(self):
        self.output_dir = Path("presentations/day_slides")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.template_dir = Path("templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def parse_day_file(self, file_path: Path) -> dict:
        """Parse individual day file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract date from filename
            filename = file_path.stem
            if len(filename) >= 4 and filename.startswith('0'):
                month = filename[:2]
                day = filename[2:4]
                date_str = f"2025-{month}-{day}"
                formatted_date = f"2025年{month}月{day}日"
            elif len(filename) == 3:  # 807.txt format
                month = '08'
                day = f"0{filename[2]}"
                date_str = f"2025-{month}-{day}"
                formatted_date = f"2025年{month}月{day}日"
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')
                formatted_date = datetime.now().strftime('%Y年%m月%d日')
            
            # Extract title
            title = self._extract_title(content)
            
            # Extract summary
            summary = self._extract_summary(content)
            
            # Extract key points
            key_points = self._extract_key_points(content)
            
            # Extract evaluation scores
            evaluation = self._extract_evaluation(content)
            
            # Extract technical details
            tech_details = self._extract_tech_details(content)
            
            return {
                'date': date_str,
                'formatted_date': formatted_date,
                'filename': file_path.name,
                'title': title,
                'summary': summary,
                'key_points': key_points,
                'evaluation': evaluation,
                'tech_details': tech_details,
                'impact_score': evaluation.get('impact_score', 75),
                'confidence': evaluation.get('confidence', 85)
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return self._create_fallback_data(file_path)
    
    def _extract_title(self, content: str) -> str:
        """Extract main title from content"""
        patterns = [
            r'### (.+?)(?:\n|$)',
            r'## (.+?)(?:\n|$)', 
            r'# (.+?)(?:\n|$)',
            r'\*\*ニュースの概要\*\*[：:]\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)
                if len(title) > 10:
                    return title[:80] + "..." if len(title) > 80 else title
        
        # If no specific pattern, extract from first substantial line
        lines = content.split('\n')
        for line in lines:
            clean_line = line.strip()
            if clean_line and len(clean_line) > 20 and not clean_line.startswith('---'):
                clean_line = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_line)
                return clean_line[:80] + "..." if len(clean_line) > 80 else clean_line
        
        return "AIニュース分析"
    
    def _extract_summary(self, content: str) -> str:
        """Extract summary from content"""
        # Look for summary patterns
        patterns = [
            r'\*\*ニュースの概要\*\*[：:]\s*([^#\*]+?)(?:\n-|\n\*\*|\n###|\n##|$)',
            r'- \*\*ニュースの概要\*\*[：:]\s*([^-\*]+?)(?:\n-|\n\*\*|$)',
            r'概要[：:]?\s*([^#\*\n]+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                summary = match.group(1).strip()
                summary = re.sub(r'\*\*(.+?)\*\*', r'\1', summary)
                summary = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', summary)
                return summary[:400] + "..." if len(summary) > 400 else summary
        
        # Fallback: get first substantial paragraph
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            clean_para = para.strip()
            if len(clean_para) > 50 and not clean_para.startswith('#'):
                clean_para = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_para)
                clean_para = re.sub(r'\n', ' ', clean_para)
                return clean_para[:400] + "..." if len(clean_para) > 400 else clean_para
        
        return "AIニュースの詳細分析を提供"
    
    def _extract_key_points(self, content: str) -> list:
        """Extract key points from content"""
        key_points = []
        
        # Look for bullet points
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^[-*•]\s+(.+)', line):
                point = re.sub(r'^[-*•]\s+', '', line)
                point = re.sub(r'\*\*(.+?)\*\*', r'\1', point)
                if len(point) > 10:
                    key_points.append(point[:150] + "..." if len(point) > 150 else point)
                    if len(key_points) >= 5:
                        break
        
        # Look for numbered points
        if len(key_points) < 3:
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\.\s+(.+)', line):
                    point = re.sub(r'^\d+\.\s+', '', line)
                    point = re.sub(r'\*\*(.+?)\*\*', r'\1', point)
                    if len(point) > 10:
                        key_points.append(point[:150] + "..." if len(point) > 150 else point)
                        if len(key_points) >= 5:
                            break
        
        # If still not enough, extract from structure
        if len(key_points) < 3:
            section_patterns = [
                r'####\s+(.+?)(?:\n|$)',
                r'###\s+(.+?)(?:\n|$)',
            ]
            for pattern in section_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    clean_match = re.sub(r'\*\*(.+?)\*\*', r'\1', match.strip())
                    if len(clean_match) > 10:
                        key_points.append(clean_match)
                        if len(key_points) >= 5:
                            break
                if len(key_points) >= 5:
                    break
        
        return key_points[:5]
    
    def _extract_evaluation(self, content: str) -> dict:
        """Extract evaluation scores"""
        evaluation = {
            'engineer_score': 70,
            'business_score': 65,
            'impact_score': 75,
            'confidence': 85
        }
        
        # Look for specific score patterns
        score_patterns = [
            (r'エンジニア.*?(\d+)', 'engineer_score'),
            (r'ビジネス.*?(\d+)', 'business_score'),
            (r'評価.*?(\d+)', 'impact_score'),
            (r'スコア.*?(\d+)', 'impact_score'),
        ]
        
        for pattern, key in score_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    score = int(matches[0])
                    if score <= 10:  # Convert 1-10 scale to percentage
                        score *= 10
                    evaluation[key] = min(score, 100)
                except ValueError:
                    continue
        
        # Analyze content for impact indicators
        high_impact_words = ['画期的', '革新', '発表', 'リリース', '重要', '注目']
        medium_impact_words = ['改善', '更新', '機能', '対応']
        
        high_count = sum(1 for word in high_impact_words if word in content)
        medium_count = sum(1 for word in medium_impact_words if word in content)
        
        if high_count >= 3:
            evaluation['impact_score'] = min(evaluation['impact_score'] + 15, 95)
        elif high_count >= 1:
            evaluation['impact_score'] = min(evaluation['impact_score'] + 10, 90)
        elif medium_count >= 2:
            evaluation['impact_score'] = min(evaluation['impact_score'] + 5, 85)
        
        return evaluation
    
    def _extract_tech_details(self, content: str) -> dict:
        """Extract technical details"""
        details = {
            'companies': [],
            'technologies': [],
            'has_code': 'コード' in content or '```' in content,
            'has_api': 'API' in content,
            'has_pricing': '価格' in content or '料金' in content or '$' in content
        }
        
        # Extract companies
        company_patterns = [
            r'(Google|Microsoft|OpenAI|Meta|Apple|Amazon|Adobe|Baidu|Anthropic|DeepMind)',
            r'(Tesla|NVIDIA|Intel|IBM|Samsung|Huawei)'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            details['companies'].extend(list(set(matches)))
        
        # Extract technologies
        tech_patterns = [
            r'(AI|LLM|GPT|Gemini|Claude|ChatGPT|API|SDK)',
            r'(機械学習|深層学習|自然言語処理|画像生成)'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            details['technologies'].extend(list(set(matches)))
        
        # Remove duplicates
        details['companies'] = list(set(details['companies']))[:5]
        details['technologies'] = list(set(details['technologies']))[:8]
        
        return details
    
    def _create_fallback_data(self, file_path: Path) -> dict:
        """Create fallback data"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return {
            'date': date_str,
            'formatted_date': datetime.now().strftime('%Y年%m月%d日'),
            'filename': file_path.name,
            'title': f"AIニュース - {file_path.stem}",
            'summary': "AIニュースの分析が含まれています。",
            'key_points': ["技術動向の分析", "市場インパクト評価", "実用性検討"],
            'evaluation': {'engineer_score': 70, 'business_score': 65, 'impact_score': 75, 'confidence': 80},
            'tech_details': {'companies': [], 'technologies': [], 'has_code': False, 'has_api': False},
            'impact_score': 75,
            'confidence': 80
        }
    
    def generate_slide_html(self, slide_data: dict) -> str:
        """Generate individual slide HTML"""
        template = self.jinja_env.get_template('day_news_slide.html')
        slide_data['generated_at'] = datetime.now().isoformat()
        return template.render(**slide_data)
    
    def process_all_files(self) -> dict:
        """Process all files in day folder"""
        day_folder = Path("C:/Users/yoshitaka/input/day")
        
        if not day_folder.exists():
            self.logger.error(f"Day folder not found: {day_folder}")
            return {}
        
        slides_data = {}
        txt_files = sorted(day_folder.glob('*.txt'))
        
        self.logger.info(f"Processing {len(txt_files)} files...")
        
        for txt_file in txt_files:
            try:
                # Parse file
                slide_data = self.parse_day_file(txt_file)
                
                # Generate slide HTML
                slide_html = self.generate_slide_html(slide_data)
                
                # Save slide
                slide_filename = f"day_slide_{slide_data['date'].replace('-', '_')}.html"
                slide_path = self.output_dir / slide_filename
                
                with open(slide_path, 'w', encoding='utf-8') as f:
                    f.write(slide_html)
                
                slides_data[slide_data['date']] = {
                    'filename': slide_filename,
                    'title': slide_data['title'],
                    'date': slide_data['date'],
                    'formatted_date': slide_data['formatted_date'],
                    'impact_score': slide_data['impact_score'],
                    'confidence': slide_data['confidence'],
                    'companies': slide_data['tech_details']['companies'],
                    'technologies': slide_data['tech_details']['technologies']
                }
                
                self.logger.info(f"Generated: {slide_filename}")
                
            except Exception as e:
                self.logger.error(f"Failed to process {txt_file}: {e}")
                continue
        
        return slides_data
    
    def create_ranking_style_index(self, slides_data: dict) -> str:
        """Create unified index page matching ranking report design"""
        
        # Sort slides by date (descending)
        sorted_slides = sorted(
            slides_data.items(),
            key=lambda x: x[0],
            reverse=True
        )
        
        # Calculate statistics
        total_slides = len(slides_data)
        avg_impact = sum(slide['impact_score'] for _, slide in sorted_slides) / total_slides if total_slides > 0 else 0
        avg_confidence = sum(slide['confidence'] for _, slide in sorted_slides) / total_slides if total_slides > 0 else 0
        high_impact_count = sum(1 for _, slide in sorted_slides if slide['impact_score'] >= 80)
        
        index_data = {
            'slides': [slide_info for date, slide_info in sorted_slides],
            'total_slides': total_slides,
            'avg_impact': round(avg_impact, 1),
            'avg_confidence': round(avg_confidence, 1),
            'high_impact_count': high_impact_count,
            'generated_at': datetime.now().isoformat(),
            'date_range': {
                'start': sorted_slides[-1][0] if sorted_slides else None,
                'end': sorted_slides[0][0] if sorted_slides else None
            }
        }
        
        template_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily AI News Slides - Intelligence Report</title>
    <style>
        :root {
            --primary: #0f172a;
            --accent: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --research: #8b5cf6;
            --dark: #020617;
            --light: #f8fafc;
            --border: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--light);
        }

        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100vh;
            background: var(--primary);
            padding: 24px 16px;
            overflow-y: auto;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
            z-index: 1000;
        }

        .sidebar h1 {
            color: white;
            font-size: 1.2rem;
            margin-bottom: 24px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
            padding-bottom: 16px;
        }

        .nav-item {
            color: #94a3b8;
            display: block;
            padding: 8px 12px;
            border-radius: 6px;
            text-decoration: none;
            margin-bottom: 4px;
            transition: all 0.2s;
        }

        .nav-item:hover {
            background: rgba(255,255,255,0.08);
            color: white;
        }

        .nav-item.active {
            background: var(--accent);
            color: white;
        }

        .main-content {
            margin-left: 260px;
            padding: 32px 48px;
            max-width: 1600px;
            background: white;
            min-height: 100vh;
        }

        h1 { font-size: 2.2rem; color: var(--primary); }
        h2 { font-size: 1.5rem; margin: 32px 0 16px; color: var(--primary); }
        h3 { font-size: 1.1rem; margin: 24px 0 12px; color: var(--primary); }

        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            margin-bottom: 16px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }

        .stats-card {
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .stats-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 8px;
        }

        .slide-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 24px;
            margin: 24px 0;
        }

        .slide-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }

        .slide-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.12);
        }

        .slide-card.high-impact {
            border-left: 4px solid var(--success);
        }

        .slide-card.medium-impact {
            border-left: 4px solid var(--warning);
        }

        .slide-card.low-impact {
            border-left: 4px solid var(--text-muted);
        }

        .slide-header {
            display: flex;
            justify-content: between;
            align-items: flex-start;
            margin-bottom: 12px;
        }

        .slide-date {
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 500;
        }

        .slide-metrics {
            display: flex;
            gap: 8px;
            margin-left: auto;
        }

        .metric-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .impact-high { background: #dcfce7; color: #166534; }
        .impact-medium { background: #fef3c7; color: #92400e; }
        .impact-low { background: #f1f5f9; color: #475569; }

        .slide-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--primary);
            line-height: 1.4;
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .slide-actions {
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }

        .btn {
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
            border: none;
            cursor: pointer;
        }

        .btn-primary {
            background: var(--accent);
            color: white;
        }

        .btn-primary:hover {
            background: #2563eb;
        }

        .btn-secondary {
            background: var(--light);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background: var(--border);
        }

        .tech-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin: 8px 0;
        }

        .tech-badge {
            background: var(--accent);
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.7rem;
        }

        .tech-badge.company {
            background: var(--success);
        }

        .feature-card {
            border-left: 4px solid var(--accent);
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }

        .filter-bar {
            display: flex;
            gap: 12px;
            margin: 20px 0;
            flex-wrap: wrap;
        }

        .filter-btn {
            padding: 8px 16px;
            border: 1px solid var(--border);
            border-radius: 20px;
            background: white;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-btn:hover,
        .filter-btn.active {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h1>📅 Daily AI News Slides</h1>
        <a href="#overview" class="nav-item active">📊 概要</a>
        <a href="#slides" class="nav-item">🎯 スライド一覧</a>
        <a href="#analytics" class="nav-item">📈 分析</a>
        <a href="#navigation" class="nav-item">🧭 ナビゲーション</a>
        <div style="border-top: 1px solid rgba(255,255,255,0.1); margin: 16px 0; padding-top: 16px;">
            <a href="ai_ranking_report_20250826.html" class="nav-item">🏆 ランキングレポート</a>
            <a href="daily_ai_news_report_20250826.html" class="nav-item">📰 詳細レポート</a>
        </div>
    </div>

    <div class="main-content">
        <section id="overview">
            <h1>Daily AI News Intelligence Slides</h1>
            <p class="text-secondary">{{ date_range.start }} ～ {{ date_range.end }}</p>
            
            <div class="stats-grid">
                <div class="card stats-card">
                    <div class="stats-value">{{ total_slides }}</div>
                    <div>総スライド数</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ high_impact_count }}</div>
                    <div>高インパクト分析</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ avg_impact }}</div>
                    <div>平均インパクト</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ avg_confidence }}%</div>
                    <div>平均信頼度</div>
                </div>
            </div>

            <div class="card feature-card">
                <h3>📋 システム概要</h3>
                <p>日々のAIニュースを詳細分析し、エンジニアとビジネス専門家向けに最適化されたプレゼンテーション形式で提供。各スライドは技術評価、市場インパクト、信頼度分析を含みます。</p>
                <p><strong>生成日時:</strong> {{ generated_at.split('T')[0] }}</p>
            </div>
        </section>

        <section id="slides">
            <h2>🎯 日次スライド一覧</h2>
            
            <div class="filter-bar">
                <button class="filter-btn active" onclick="filterSlides('all')">すべて</button>
                <button class="filter-btn" onclick="filterSlides('high')">高インパクト (80+)</button>
                <button class="filter-btn" onclick="filterSlides('medium')">中インパクト (60-79)</button>
                <button class="filter-btn" onclick="filterSlides('recent')">最近1週間</button>
            </div>

            <div class="slide-grid">
                {% for slide in slides %}
                <div class="slide-card {% if slide.impact_score >= 80 %}high-impact{% elif slide.impact_score >= 60 %}medium-impact{% else %}low-impact{% endif %}" 
                     data-impact="{{ slide.impact_score }}" data-date="{{ slide.date }}">
                    
                    <div class="slide-header">
                        <div class="slide-date">{{ slide.formatted_date }}</div>
                        <div class="slide-metrics">
                            <span class="metric-badge {% if slide.impact_score >= 80 %}impact-high{% elif slide.impact_score >= 60 %}impact-medium{% else %}impact-low{% endif %}">
                                {{ slide.impact_score }}pt
                            </span>
                        </div>
                    </div>
                    
                    <div class="slide-title">{{ slide.title }}</div>
                    
                    {% if slide.companies or slide.technologies %}
                    <div class="tech-badges">
                        {% for company in slide.companies %}
                        <span class="tech-badge company">{{ company }}</span>
                        {% endfor %}
                        {% for tech in slide.technologies %}
                        <span class="tech-badge">{{ tech }}</span>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    <div class="slide-actions">
                        <a href="day_slides/{{ slide.filename }}" class="btn btn-primary">🎯 スライドを開く</a>
                        <button class="btn btn-secondary" onclick="copyLink('day_slides/{{ slide.filename }}')">🔗 リンク</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>

        <section id="navigation">
            <h2>🧭 関連リンク</h2>
            <div class="card">
                <p>他のレポートやシステムにアクセス</p>
                <div style="margin-top: 16px;">
                    <a href="ai_ranking_report_20250826.html" class="btn btn-primary">🏆 AIランキングレポート</a>
                    <a href="daily_ai_news_report_20250826.html" class="btn btn-primary">📰 詳細ニュースレポート</a>
                    <a href="advanced_intelligence_report_20250826.html" class="btn btn-primary">🧠 高度分析レポート</a>
                </div>
            </div>
        </section>
    </div>

    <script>
        function filterSlides(filter) {
            const cards = document.querySelectorAll('.slide-card');
            const buttons = document.querySelectorAll('.filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            cards.forEach(card => {
                const impact = parseInt(card.dataset.impact);
                const date = new Date(card.dataset.date);
                const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
                
                let show = true;
                
                switch(filter) {
                    case 'high':
                        show = impact >= 80;
                        break;
                    case 'medium':
                        show = impact >= 60 && impact < 80;
                        break;
                    case 'recent':
                        show = date >= weekAgo;
                        break;
                }
                
                card.style.display = show ? 'block' : 'none';
            });
        }

        function copyLink(path) {
            const fullUrl = window.location.origin + window.location.pathname.replace('/day_slides_index.html', '/') + path;
            navigator.clipboard.writeText(fullUrl).then(() => {
                alert('リンクをコピーしました');
            });
        }

        // Smooth scrolling for navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', function(e) {
                if (this.getAttribute('href').startsWith('#')) {
                    e.preventDefault();
                    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                    this.classList.add('active');
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            });
        });
    </script>
</body>
</html>"""
        
        template = self.jinja_env.from_string(template_content)
        return template.render(**index_data)

def main():
    """Main execution"""
    print("🚀 Starting comprehensive day slides generation...")
    
    generator = ComprehensiveDaySlideGenerator()
    
    try:
        # Process all files
        slides_data = generator.process_all_files()
        print(f"✅ Generated {len(slides_data)} slides")
        
        # Create unified index
        index_html = generator.create_ranking_style_index(slides_data)
        index_path = Path("presentations/day_slides_index.html")
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print(f"✅ Created unified index: {index_path}")
        print(f"📊 Statistics: {len(slides_data)} total slides")
        print(f"🎯 High impact: {sum(1 for s in slides_data.values() if s['impact_score'] >= 80)} slides")
        
        # Show summary
        print("\n📅 Generated Slides:")
        for date, info in sorted(slides_data.items(), reverse=True):
            print(f"  {info['formatted_date']}: {info['title'][:50]}... (Impact: {info['impact_score']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()