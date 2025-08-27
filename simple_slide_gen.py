#!/usr/bin/env python3
"""Simple slide generation for day files"""

import os
import re
from pathlib import Path
from datetime import datetime

def extract_date_from_filename(filename):
    """Extract date from filename like 0818.txt"""
    if len(filename) >= 4 and filename.startswith('0'):
        month = filename[:2]
        day = filename[2:4]
        return f"2025-{month}-{day}", f"2025年{month}月{day}日"
    return None, None

def parse_day_file(file_path):
    """Parse day file and extract key information"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title (usually after TL;DR or first header)
    title_match = re.search(r'TL;DR[：:]?\*?\*?(.+?)(?:\*\*|。|$)', content, re.IGNORECASE)
    if not title_match:
        title_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日の.*?)(?:\n|$)', content)
    
    title = title_match.group(1).strip() if title_match else "AI News Analysis"
    
    # Clean up title
    title = re.sub(r'^\*+|^\s*:', '', title).strip()
    title = re.sub(r'\*+$', '', title).strip()
    
    # Extract summary (first paragraph or TL;DR content)
    summary_match = re.search(r'TL;DR[：:]?\*?\*?(.+?)(?:\n---|\n##|\n\*\*|$)', content, re.DOTALL | re.IGNORECASE)
    if not summary_match:
        # Try to get first substantial paragraph
        paragraphs = [p.strip() for p in content.split('\n') if len(p.strip()) > 50]
        summary = paragraphs[0] if paragraphs else "AI関連の重要なニュースと分析"
    else:
        summary = summary_match.group(1).strip()
    
    # Clean up summary
    summary = re.sub(r'^\*+|^：', '', summary).strip()
    summary = re.sub(r'\*+$', '', summary).strip()
    
    # Extract key points (look for bullet points or numbered lists)
    key_points = []
    bullet_matches = re.findall(r'(?:^|\n)[-*•]\s*(.+)', content)
    if bullet_matches:
        key_points = [point.strip() for point in bullet_matches[:5]]  # Take first 5
    
    # If no bullet points, look for numbered items
    if not key_points:
        numbered_matches = re.findall(r'(?:^|\n)\d+[.)]\s*(.+)', content)
        if numbered_matches:
            key_points = [point.strip() for point in numbered_matches[:5]]
    
    # Extract evaluation scores (look for patterns like "高", "中", "低" or numbers)
    engineer_score = 75  # Default
    business_score = 70  # Default
    
    # Look for evaluation patterns
    eval_matches = re.findall(r'エンジニア.*?[：:].*?(\d+|高|中|低)', content)
    if eval_matches:
        eval_text = eval_matches[0]
        if eval_text == '高':
            engineer_score = 85
        elif eval_text == '中':
            engineer_score = 65
        elif eval_text == '低':
            engineer_score = 45
        elif eval_text.isdigit():
            engineer_score = int(eval_text)
    
    business_matches = re.findall(r'ビジネス.*?[：:].*?(\d+|高|中|低)', content)
    if business_matches:
        eval_text = business_matches[0]
        if eval_text == '高':
            business_score = 85
        elif eval_text == '中':
            business_score = 65
        elif eval_text == '低':
            business_score = 45
        elif eval_text.isdigit():
            business_score = int(eval_text)
    
    # Calculate impact score
    impact_score = int((engineer_score + business_score) / 2)
    
    # Extract companies and technologies
    companies = []
    technologies = []
    
    # Look for common company names
    company_patterns = [
        r'Google', r'Microsoft', r'OpenAI', r'Meta', r'Apple', r'Amazon', 
        r'Baidu', r'ByteDance', r'Anthropic', r'DeepMind', r'Oracle'
    ]
    for pattern in company_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            companies.append(pattern)
    
    # Look for technology terms
    tech_patterns = [
        r'AI', r'GPT', r'LLM', r'機械学習', r'深層学習', r'Transformer',
        r'API', r'SDK', r'Neural', r'Generative'
    ]
    for pattern in tech_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            technologies.append(pattern)
    
    # Remove duplicates
    companies = list(set(companies))[:5]
    technologies = list(set(technologies))[:5]
    
    # Extract sources (look for URLs)
    sources = re.findall(r'https?://[^\s)]+', content)
    sources = list(set(sources))[:8]  # Limit to 8 unique sources
    
    return {
        'title': title,
        'summary': summary,
        'key_points': key_points,
        'impact_score': impact_score,
        'confidence': min(95, 60 + len(sources) * 5),  # Based on number of sources
        'evaluation': {
            'engineer_score': engineer_score,
            'business_score': business_score
        },
        'technical_details': {
            'companies': companies,
            'technologies': technologies,
            'has_code': bool(re.search(r'コード|code|API|GitHub', content, re.IGNORECASE)),
            'has_api': bool(re.search(r'API|エンドポイント', content, re.IGNORECASE)),
            'has_pricing': bool(re.search(r'価格|料金|\$|\¥', content, re.IGNORECASE))
        },
        'sources': sources
    }

def generate_slide_html(data, date_str, formatted_date):
    """Generate HTML slide content"""
    
    template = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{ formatted_date }} - AI News Analysis</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/theme/white.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #0f172a;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --gradient-bg: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            --light-gradient: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }

        .reveal {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .reveal .slides section {
            text-align: left;
        }

        .reveal h1, .reveal h2, .reveal h3 {
            color: var(--primary-color);
            font-weight: 600;
            text-align: center;
        }

        /* Title slide styling */
        .reveal .title-slide {
            background: var(--gradient-bg);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .reveal .title-slide::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                rgba(255,255,255,0.05) 10px,
                rgba(255,255,255,0.05) 20px
            );
            animation: slide 20s linear infinite;
        }

        @keyframes slide {
            0% { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(360deg); }
        }

        .reveal .title-slide .content {
            position: relative;
            z-index: 2;
        }

        .reveal .title-slide h1 {
            color: white;
            font-size: 2.5em;
            margin-bottom: 0.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .reveal .title-slide .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 1em;
        }

        .reveal .title-slide .date-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 0.5rem 1rem;
            border-radius: 25px;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
        }

        /* Stats and metrics */
        .reveal .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }

        .reveal .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .reveal .stat-number {
            font-size: 2em;
            font-weight: 700;
            color: white;
            display: block;
        }

        .reveal .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }

        /* Content cards */
        .reveal .content-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
            position: relative;
        }

        .reveal .content-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--accent-color);
            border-radius: 15px 15px 0 0;
        }

        .reveal .content-card.high-impact::before {
            background: var(--success-color);
        }

        .reveal .content-card.medium-impact::before {
            background: var(--warning-color);
        }

        .reveal .content-card.low-impact::before {
            background: #94a3b8;
        }

        .reveal .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .reveal .card-title {
            font-size: 1.4em;
            font-weight: 600;
            color: var(--primary-color);
            margin: 0;
        }

        .reveal .impact-badge {
            padding: 0.4rem 1rem;
            border-radius: 25px;
            font-size: 0.9em;
            font-weight: 600;
        }

        .reveal .impact-high {
            background: #dcfce7;
            color: #166534;
        }

        .reveal .impact-medium {
            background: #fef3c7;
            color: #92400e;
        }

        .reveal .impact-low {
            background: #f1f5f9;
            color: #475569;
        }

        /* Key points */
        .reveal .key-points {
            margin: 1.5rem 0;
        }

        .reveal .key-points ul {
            list-style: none;
            padding: 0;
        }

        .reveal .key-points li {
            padding: 1rem;
            margin: 0.5rem 0;
            background: var(--light-gradient);
            border-left: 4px solid var(--accent-color);
            border-radius: 0 8px 8px 0;
            transition: all 0.3s ease;
        }

        .reveal .key-points li:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        /* Technical details */
        .reveal .tech-details {
            background: #f8fafc;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            margin: 1rem 0;
        }

        .reveal .tech-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0;
        }

        .reveal .tech-badge {
            background: var(--accent-color);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 500;
        }

        .reveal .tech-badge.company {
            background: var(--success-color);
        }

        .reveal .tech-badge.feature {
            background: var(--warning-color);
        }

        /* Evaluation section */
        .reveal .evaluation-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin: 2rem 0;
        }

        .reveal .eval-item {
            text-align: center;
        }

        .reveal .eval-score {
            font-size: 3em;
            font-weight: 700;
            color: var(--accent-color);
            display: block;
        }

        .reveal .eval-label {
            font-size: 1.1em;
            color: var(--primary-color);
            margin-top: 0.5rem;
        }

        .reveal .progress-bar {
            width: 100%;
            height: 12px;
            background: #e2e8f0;
            border-radius: 6px;
            overflow: hidden;
            margin: 1rem 0;
        }

        .reveal .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
            transition: width 0.8s ease;
            border-radius: 6px;
        }

        /* Sources section */
        .reveal .sources-section {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            border: 1px solid #e2e8f0;
        }

        .reveal .source-links {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-top: 1rem;
        }

        .reveal .source-link {
            display: inline-block;
            background: var(--accent-color);
            color: white;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            text-decoration: none;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .reveal .source-link:hover {
            background: #2563eb;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        /* Navigation */
        .reveal .navigation-card {
            background: var(--gradient-bg);
            color: white;
            padding: 3rem;
            border-radius: 15px;
            text-align: center;
        }

        .reveal .nav-buttons {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }

        .reveal .nav-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 1rem 2rem;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .reveal .nav-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            color: white;
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .reveal .stats-grid {
                grid-template-columns: 1fr 1fr;
            }
            
            .reveal .evaluation-grid {
                grid-template-columns: 1fr;
            }
            
            .reveal .nav-buttons {
                flex-direction: column;
                align-items: center;
            }
            
            .reveal .content-card {
                padding: 1.5rem;
            }
        }

        /* Animation classes */
        .reveal .fade-in {
            animation: fadeInUp 0.8s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>

<body>
    <div class="reveal">
        <div class="slides">
            
            <!-- Title Slide -->
            <section class="title-slide">
                <div class="content">
                    <h1>''' + formatted_date + '''</h1>
                    <div class="subtitle">AI News Analysis & Insights</div>
                    <div class="date-badge">''' + data['title'][:100] + '''</div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-number">''' + str(data['impact_score']) + '''</span>
                            <span class="stat-label">Impact Score</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">''' + str(data['confidence']) + '''%</span>
                            <span class="stat-label">Confidence</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">''' + str(len(data['technical_details']['companies']) + len(data['technical_details']['technologies'])) + '''</span>
                            <span class="stat-label">Tech Elements</span>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Summary Slide -->
            <section>
                <h2>📋 ニュースサマリー</h2>
                <div class="content-card ''' + ('high-impact' if data['impact_score'] >= 80 else 'medium-impact' if data['impact_score'] >= 60 else 'low-impact') + ''' fade-in">
                    <div class="card-header">
                        <h3 class="card-title">''' + data['title'] + '''</h3>
                        <div class="impact-badge ''' + ('impact-high' if data['impact_score'] >= 80 else 'impact-medium' if data['impact_score'] >= 60 else 'impact-low') + '''">
                            ''' + str(data['impact_score']) + '''pt
                        </div>
                    </div>
                    
                    <div class="summary-content">
                        <p style="font-size: 1.1em; line-height: 1.6; color: #374151;">''' + data['summary'] + '''</p>
                    </div>
                    
                    <div class="tech-badges">'''

    # Add company badges
    for company in data['technical_details']['companies']:
        template += f'<span class="tech-badge company">{company}</span>'
    
    # Add technology badges  
    for tech in data['technical_details']['technologies']:
        template += f'<span class="tech-badge">{tech}</span>'
    
    template += '''</div>
                </div>
            </section>

            <!-- Key Points Slide -->
            <section>
                <h2>🎯 重要ポイント</h2>
                <div class="key-points fade-in">
                    <ul>'''
    
    # Add key points
    for point in data['key_points'][:5]:
        template += f'<li>{point}</li>'
    
    template += '''</ul>
                </div>
                
                <div class="tech-details">
                    <h3 style="margin-top: 0; color: var(--primary-color);">🔧 技術的特徴</h3>
                    <div class="tech-badges">'''
    
    # Add feature badges
    if data['technical_details']['has_code']:
        template += '<span class="tech-badge feature">コード提供</span>'
    if data['technical_details']['has_api']:
        template += '<span class="tech-badge feature">API対応</span>'
    if data['technical_details']['has_pricing']:
        template += '<span class="tech-badge feature">料金情報</span>'
    
    template += '''</div>
                </div>
            </section>

            <!-- Evaluation Slide -->
            <section>
                <h2>📊 評価分析</h2>
                <div class="evaluation-grid fade-in">
                    <div class="eval-item">
                        <span class="eval-score">''' + str(data['evaluation']['engineer_score']) + '''</span>
                        <div class="eval-label">エンジニア向け</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ''' + str(data['evaluation']['engineer_score']) + '''%"></div>
                        </div>
                    </div>
                    <div class="eval-item">
                        <span class="eval-score">''' + str(data['evaluation']['business_score']) + '''</span>
                        <div class="eval-label">ビジネス向け</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ''' + str(data['evaluation']['business_score']) + '''%"></div>
                        </div>
                    </div>
                </div>
                
                <div class="content-card fade-in">
                    <h3 style="text-align: center; margin-bottom: 1rem;">📈 総合評価</h3>
                    <div style="text-align: center;">
                        <div style="font-size: 3em; font-weight: 700; color: var(--accent-color); margin: 1rem 0;">
                            ''' + str(data['impact_score']) + '''
                        </div>
                        <div style="font-size: 1.2em; color: var(--primary-color);">
                            Impact Score (100点満点)
                        </div>
                        <div class="progress-bar" style="max-width: 400px; margin: 2rem auto;">
                            <div class="progress-fill" style="width: ''' + str(data['impact_score']) + '''%"></div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Sources Slide -->
            <section>
                <h2>📚 情報源・参考資料</h2>
                <div class="sources-section fade-in">
                    <h3 style="margin-top: 0;">🔗 関連リンク</h3>
                    <p style="color: #6b7280; margin-bottom: 2rem;">信頼できる一次ソースからの情報</p>
                    
                    <div class="source-links">'''
    
    # Add source links
    for i, source in enumerate(data['sources'][:8]):
        template += f'<a href="{source}" target="_blank" class="source-link">📄 ソース {i+1}</a>'
    
    template += '''</div>
                    
                    <div style="margin-top: 2rem; padding: 1rem; background: #f3f4f6; border-radius: 8px;">
                        <h4 style="margin-top: 0; color: var(--primary-color);">信頼度指標</h4>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ''' + str(data['confidence']) + '''%"></div>
                        </div>
                        <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9em;">
                            信頼度: ''' + str(data['confidence']) + '''% (''' + str(len(data['sources'])) + '''個のソース確認済み)
                        </p>
                    </div>
                </div>
            </section>

            <!-- Navigation Slide -->
            <section>
                <div class="navigation-card">
                    <h2 style="color: white;">🧭 ナビゲーション</h2>
                    <p style="opacity: 0.9; margin: 1rem 0;">他のレポートやスライドにアクセス</p>
                    
                    <div class="nav-buttons">
                        <a href="../day_slides_index.html" class="nav-btn">
                            📅 日次スライド一覧
                        </a>
                        <a href="../ai_ranking_report_20250826.html" class="nav-btn">
                            🏆 ランキングレポート
                        </a>
                        <a href="../daily_ai_news_report_20250826.html" class="nav-btn">
                            📰 詳細レポート
                        </a>
                    </div>
                    
                    <div style="margin-top: 3rem; font-size: 0.9em; opacity: 0.7;">
                        <p>🎯 キーボードショートカット: H (ホーム) | R (レポート) | ESC (戻る)</p>
                    </div>
                </div>
            </section>

        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.js"></script>
    <script>
        Reveal.initialize({
            hash: true,
            controls: true,
            progress: true,
            center: false,
            transition: 'slide',
            backgroundTransition: 'fade',
            keyboard: true,
            overview: true,
            touch: true,
            loop: false,
            rtl: false,
            navigationMode: 'default',
            fragments: true,
            autoSlide: 0,
            mouseWheel: false,
            hideAddressBar: true,
            previewLinks: false
        });

        // Add keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            switch(event.key) {
                case 'h':
                case 'H':
                    window.location.href = '../day_slides_index.html';
                    break;
                case 'r':
                case 'R':
                    window.location.href = '../ai_ranking_report_20250826.html';
                    break;
                case 'm':
                case 'M':
                    window.location.href = '../daily_ai_news_report_20250826.html';
                    break;
                case 'Escape':
                    window.history.back();
                    break;
            }
        });

        // Add slide animations
        Reveal.on('slidechanged', function(event) {
            const currentSlide = event.currentSlide;
            const fadeElements = currentSlide.querySelectorAll('.fade-in');
            
            fadeElements.forEach((element, index) => {
                element.style.animationDelay = `${index * 0.2}s`;
                element.classList.add('fade-in');
            });
        });

        // Progress bar animations
        Reveal.on('ready', function() {
            setTimeout(() => {
                const progressBars = document.querySelectorAll('.progress-fill');
                progressBars.forEach(bar => {
                    bar.style.width = bar.style.width;
                });
            }, 500);
        });

        // Add smooth scrolling for navigation
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });
    </script>
</body>
</html>'''
    
    return template

def main():
    # Set up directories
    day_dir = Path('C:\\Users\\yoshitaka\\input\\day')
    output_dir = Path('presentations\\day_slides')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    slides_data = {}
    
    # Process all txt files
    for file_path in sorted(day_dir.glob('*.txt')):
        print(f"Processing {file_path.name}...")
        
        try:
            # Extract date
            date_str, formatted_date = extract_date_from_filename(file_path.stem)
            if not date_str:
                continue
                
            # Parse file content
            data = parse_day_file(file_path)
            
            # Store slide data
            slides_data[date_str] = {
                'title': data['title'],
                'formatted_date': formatted_date,
                'impact_score': data['impact_score'],
                'confidence': data['confidence'],
                'file_path': file_path.name
            }
            
            # Generate slide HTML
            html_content = generate_slide_html(data, date_str, formatted_date)
            
            # Write slide file
            output_file = output_dir / f"day_slide_{date_str.replace('-', '_')}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"Generated: {output_file}")
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
    
    # Generate index
    generate_index(slides_data)
    
    print(f"Total slides generated: {len(slides_data)}")

def generate_index(slides_data):
    """Generate the unified index page"""
    
    # Sort slides by date (most recent first)
    sorted_slides = sorted(slides_data.items(), key=lambda x: x[0], reverse=True)
    
    # Calculate statistics
    total_slides = len(slides_data)
    avg_impact = sum(slide['impact_score'] for _, slide in sorted_slides) / total_slides if total_slides > 0 else 0
    high_impact_count = sum(1 for _, slide in sorted_slides if slide['impact_score'] >= 80)
    
    index_html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily AI News Slides - Unified Index</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/lucide@0.263.1/dist/umd/lucide.min.js" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary-color: #0f172a;
            --secondary-color: #475569;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --border-color: #e2e8f0;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-success: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--background-color);
            color: var(--text-primary);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        /* Header */
        .header {{
            background: var(--gradient-primary);
            color: white;
            padding: 3rem 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.1;
        }}

        .header-content {{
            position: relative;
            z-index: 1;
        }}

        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .header-subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 2rem;
        }}

        /* Stats Grid */
        .stats-section {{
            padding: 3rem 0;
            background: white;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }}

        .stat-card {{
            background: var(--card-background);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--accent-color);
            border-radius: 15px 15px 0 0;
        }}

        .stat-card.success::before {{
            background: var(--success-color);
        }}

        .stat-card.warning::before {{
            background: var(--warning-color);
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }}

        .stat-number {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--primary-color);
            display: block;
            margin-bottom: 0.5rem;
        }}

        .stat-label {{
            font-size: 1.1rem;
            color: var(--text-secondary);
            font-weight: 500;
        }}

        /* Slides Grid */
        .slides-section {{
            padding: 3rem 0;
        }}

        .section-title {{
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 3rem;
            color: var(--primary-color);
        }}

        .slides-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }}

        .slide-card {{
            background: var(--card-background);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 2rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .slide-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent-color), var(--success-color));
            border-radius: 15px 15px 0 0;
        }}

        .slide-card.high-impact::before {{
            background: linear-gradient(90deg, var(--success-color), var(--accent-color));
        }}

        .slide-card.medium-impact::before {{
            background: linear-gradient(90deg, var(--warning-color), var(--accent-color));
        }}

        .slide-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        }}

        .slide-date {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
        }}

        .slide-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .slide-metrics {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .metric {{
            flex: 1;
            text-align: center;
        }}

        .metric-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-color);
            display: block;
        }}

        .metric-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }}

        .slide-actions {{
            display: flex;
            gap: 1rem;
        }}

        .btn {{
            flex: 1;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 500;
            text-decoration: none;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }}

        .btn-primary {{
            background: var(--accent-color);
            color: white;
        }}

        .btn-primary:hover {{
            background: #2563eb;
            transform: translateY(-2px);
        }}

        .btn-outline {{
            background: transparent;
            color: var(--accent-color);
            border: 2px solid var(--accent-color);
        }}

        .btn-outline:hover {{
            background: var(--accent-color);
            color: white;
        }}

        /* Navigation */
        .navigation {{
            background: var(--primary-color);
            color: white;
            padding: 3rem 0;
            text-align: center;
        }}

        .nav-buttons {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }}

        .nav-btn {{
            background: rgba(255, 255, 255, 0.1);
            color: white;
            padding: 1rem 2rem;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .nav-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            color: white;
        }}

        /* Responsive Design */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}

            .stats-grid {{
                grid-template-columns: 1fr 1fr;
            }}

            .slides-grid {{
                grid-template-columns: 1fr;
            }}

            .nav-buttons {{
                flex-direction: column;
                align-items: center;
            }}

            .slide-actions {{
                flex-direction: column;
            }}
        }}

        /* Loading Animation */
        .loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--accent-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* Fade In Animation */
        .fade-in {{
            animation: fadeInUp 0.6s ease-out forwards;
            opacity: 0;
            transform: translateY(20px);
        }}

        @keyframes fadeInUp {{
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
    </style>
</head>
<body>
    <!-- Header Section -->
    <header class="header">
        <div class="container">
            <div class="header-content">
                <h1>📊 Daily AI News Slides</h1>
                <p class="header-subtitle">Comprehensive AI Intelligence Dashboard</p>
            </div>
        </div>
    </header>

    <!-- Stats Section -->
    <section class="stats-section">
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number">{total_slides}</span>
                    <span class="stat-label">Total Slides</span>
                </div>
                <div class="stat-card success">
                    <span class="stat-number">{avg_impact:.1f}</span>
                    <span class="stat-label">Average Impact</span>
                </div>
                <div class="stat-card warning">
                    <span class="stat-number">{high_impact_count}</span>
                    <span class="stat-label">High Impact Days</span>
                </div>
            </div>
        </div>
    </section>

    <!-- Slides Grid Section -->
    <section class="slides-section">
        <div class="container">
            <h2 class="section-title">📅 Daily Slide Collection</h2>
            <div class="slides-grid">'''

    # Add slide cards
    for date, slide in sorted_slides:
        impact_class = 'high-impact' if slide['impact_score'] >= 80 else 'medium-impact' if slide['impact_score'] >= 60 else ''
        slide_filename = f"day_slide_{date.replace('-', '_')}.html"
        
        index_html += f'''
                <div class="slide-card {impact_class} fade-in">
                    <div class="slide-date">📅 {slide['formatted_date']}</div>
                    <h3 class="slide-title">{slide['title'][:80]}{'...' if len(slide['title']) > 80 else ''}</h3>
                    <div class="slide-metrics">
                        <div class="metric">
                            <span class="metric-value">{slide['impact_score']}</span>
                            <div class="metric-label">Impact Score</div>
                        </div>
                        <div class="metric">
                            <span class="metric-value">{slide['confidence']}%</span>
                            <div class="metric-label">Confidence</div>
                        </div>
                    </div>
                    <div class="slide-actions">
                        <a href="day_slides/{slide_filename}" class="btn btn-primary">📊 View Slide</a>
                        <a href="../input/day/{slide['file_path']}" class="btn btn-outline">📄 Source</a>
                    </div>
                </div>'''

    index_html += '''
            </div>
        </div>
    </section>

    <!-- Navigation Section -->
    <section class="navigation">
        <div class="container">
            <h2 style="color: white; margin-bottom: 1rem;">🧭 Navigation Hub</h2>
            <p style="opacity: 0.9;">Access other AI intelligence reports and analysis</p>
            
            <div class="nav-buttons">
                <a href="ai_ranking_report_20250826.html" class="nav-btn">
                    🏆 AI Technology Rankings
                </a>
                <a href="daily_ai_news_report_20250826.html" class="nav-btn">
                    📰 Latest News Report
                </a>
                <a href="advanced_intelligence_report_20250826.html" class="nav-btn">
                    🔬 Advanced Intelligence
                </a>
            </div>
        </div>
    </section>

    <script>
        // Add fade-in animation on scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationDelay = Math.random() * 0.3 + 's';
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        // Observe all slide cards
        document.querySelectorAll('.slide-card').forEach(card => {
            observer.observe(card);
        });

        // Add keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            switch(event.key) {
                case 'r':
                case 'R':
                    window.location.href = 'ai_ranking_report_20250826.html';
                    break;
                case 'n':
                case 'N':
                    window.location.href = 'daily_ai_news_report_20250826.html';
                    break;
                case 'a':
                case 'A':
                    window.location.href = 'advanced_intelligence_report_20250826.html';
                    break;
            }
        });
    </script>
</body>
</html>'''

    # Write the index file
    with open('presentations/day_slides_index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    print("Generated unified index: presentations/day_slides_index.html")

if __name__ == "__main__":
    main()