#!/usr/bin/env python3
"""Generate slides for ALL day files"""

import os
import re
from pathlib import Path
from datetime import datetime

def extract_date_from_filename(filename):
    """Extract date from filename like 0818.txt"""
    if filename.startswith('07'):
        month = '07'
        day = filename[2:4]
        return f"2025-{month}-{day}", f"2025年{month}月{day}日"
    elif filename.startswith('08'):
        month = '08' 
        day = filename[2:4]
        return f"2025-{month}-{day}", f"2025年{month}月{day}日"
    return None, None

def parse_day_file(file_path):
    """Parse day file and extract key information"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title
        title_match = re.search(r'(?:TL;DR|一番)[：:]?\*?\*?(.+?)(?:\*\*|。|\n)', content, re.IGNORECASE)
        if not title_match:
            lines = content.split('\n')
            for line in lines[:10]:
                if 'AI' in line or 'Google' in line or 'Meta' in line or 'Microsoft' in line:
                    title = line.strip()[:100]
                    break
            else:
                title = "AI News Analysis"
        else:
            title = title_match.group(1).strip()
        
        # Clean title
        title = re.sub(r'^\*+|^[：:]', '', title).strip()
        title = re.sub(r'\*+$', '', title).strip()
        
        # Extract summary
        summary_match = re.search(r'(?:概要|summary|TL;DR)[：:]?\*?\*?(.+?)(?:\n\n|\n-|\n\*)', content, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()[:500]
        else:
            # Get first substantial paragraph
            paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
            summary = paragraphs[0][:500] if paragraphs else "重要なAIニュースと分析"
        
        # Clean summary
        summary = re.sub(r'^\*+|^[：:]', '', summary).strip()
        
        # Extract key points
        key_points = []
        bullet_matches = re.findall(r'(?:^|\n)[-*•]\s*(.+)', content)
        if bullet_matches:
            key_points = [point.strip() for point in bullet_matches[:5]]
        
        # Extract evaluation scores
        engineer_score = 75
        business_score = 70
        
        # Look for evaluation patterns
        if re.search(r'エンジニア.*?(?:高|High)', content, re.IGNORECASE):
            engineer_score = 85
        elif re.search(r'エンジニア.*?(?:中|Medium)', content, re.IGNORECASE):
            engineer_score = 65
        elif re.search(r'エンジニア.*?(?:低|Low)', content, re.IGNORECASE):
            engineer_score = 45
        
        if re.search(r'ビジネス.*?(?:高|High)', content, re.IGNORECASE):
            business_score = 85
        elif re.search(r'ビジネス.*?(?:中|Medium)', content, re.IGNORECASE):
            business_score = 65
        elif re.search(r'ビジネス.*?(?:低|Low)', content, re.IGNORECASE):
            business_score = 45
        
        # Calculate impact score
        impact_score = int((engineer_score + business_score) / 2)
        
        # Extract companies
        companies = []
        company_patterns = [
            'Google', 'Microsoft', 'OpenAI', 'Meta', 'Apple', 'Amazon',
            'Baidu', 'ByteDance', 'Anthropic', 'DeepMind', 'Oracle', 'NVIDIA',
            'GitHub', 'Adobe', 'IBM', 'Tesla', 'xAI', 'Stability AI'
        ]
        for pattern in company_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                companies.append(pattern)
        companies = list(set(companies))[:5]
        
        # Extract technologies
        technologies = []
        tech_patterns = [
            'GPT', 'LLM', 'Transformer', 'API', 'SDK', 'Neural',
            'Gemini', 'Claude', 'DALL-E', 'Copilot', 'Agent', 'Vision'
        ]
        for pattern in tech_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                technologies.append(pattern)
        technologies = list(set(technologies))[:5]
        
        # Extract sources
        sources = re.findall(r'https?://[^\s)]+', content)
        sources = list(set(sources))[:6]
        
        return {
            'title': title[:100],
            'summary': summary,
            'key_points': key_points[:5] if key_points else ['AI技術の進化', '業界動向', '実装可能性'],
            'impact_score': impact_score,
            'confidence': min(95, 70 + len(sources) * 5),
            'evaluation': {
                'engineer_score': engineer_score,
                'business_score': business_score
            },
            'technical_details': {
                'companies': companies,
                'technologies': technologies,
                'has_code': bool(re.search(r'code|API|GitHub|実装|コード', content, re.IGNORECASE)),
                'has_api': bool(re.search(r'API|エンドポイント|endpoint', content, re.IGNORECASE)),
                'has_pricing': bool(re.search(r'価格|料金|\$|円|無料|Free', content, re.IGNORECASE))
            },
            'sources': sources if sources else ['#']
        }
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None

def generate_slide_html(data, date_str, formatted_date, filename):
    """Generate HTML slide content"""
    
    # Determine impact class
    impact_class = 'high-impact' if data['impact_score'] >= 80 else 'medium-impact' if data['impact_score'] >= 60 else ''
    impact_badge_class = 'impact-high' if data['impact_score'] >= 80 else 'impact-medium' if data['impact_score'] >= 60 else 'impact-low'
    
    # Build tech badges HTML
    company_badges = ''.join([f'<span class="tech-badge company">{c}</span>' for c in data['technical_details']['companies']])
    tech_badges = ''.join([f'<span class="tech-badge">{t}</span>' for t in data['technical_details']['technologies']])
    
    # Build key points HTML
    key_points_html = ''.join([f'<li>{point}</li>' for point in data['key_points']])
    
    # Build feature badges
    feature_badges = ''
    if data['technical_details']['has_code']:
        feature_badges += '<span class="tech-badge feature">コード提供</span>'
    if data['technical_details']['has_api']:
        feature_badges += '<span class="tech-badge feature">API対応</span>'
    if data['technical_details']['has_pricing']:
        feature_badges += '<span class="tech-badge feature">料金情報</span>'
    
    # Build source links
    source_links = ''
    for i, source in enumerate(data['sources'][:6]):
        if source != '#':
            domain = source.split('/')[2] if len(source.split('/')) > 2 else 'Link'
            source_links += f'<a href="{source}" target="_blank" class="source-link">📄 {domain}</a>'
    
    template = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{formatted_date} - AI News Analysis</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/theme/white.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #0f172a;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --gradient-bg: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            --light-gradient: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }}

        .reveal {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .reveal .slides section {{
            text-align: left;
        }}

        .reveal h1, .reveal h2, .reveal h3 {{
            color: var(--primary-color);
            font-weight: 600;
            text-align: center;
        }}

        .reveal .title-slide {{
            background: var(--gradient-bg);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .reveal .title-slide::before {{
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
        }}

        @keyframes slide {{
            0% {{ transform: translate(-50%, -50%) rotate(0deg); }}
            100% {{ transform: translate(-50%, -50%) rotate(360deg); }}
        }}

        .reveal .title-slide .content {{
            position: relative;
            z-index: 2;
        }}

        .reveal .title-slide h1 {{
            color: white;
            font-size: 2.5em;
            margin-bottom: 0.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .reveal .title-slide .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 1em;
        }}

        .reveal .title-slide .date-badge {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 0.5rem 1rem;
            border-radius: 25px;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
        }}

        .reveal .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}

        .reveal .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .reveal .stat-number {{
            font-size: 2em;
            font-weight: 700;
            color: white;
            display: block;
        }}

        .reveal .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}

        .reveal .content-card {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
            position: relative;
        }}

        .reveal .content-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--accent-color);
            border-radius: 15px 15px 0 0;
        }}

        .reveal .content-card.high-impact::before {{
            background: var(--success-color);
        }}

        .reveal .content-card.medium-impact::before {{
            background: var(--warning-color);
        }}

        .reveal .content-card.low-impact::before {{
            background: #94a3b8;
        }}

        .reveal .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }}

        .reveal .card-title {{
            font-size: 1.4em;
            font-weight: 600;
            color: var(--primary-color);
            margin: 0;
        }}

        .reveal .impact-badge {{
            padding: 0.4rem 1rem;
            border-radius: 25px;
            font-size: 0.9em;
            font-weight: 600;
        }}

        .reveal .impact-high {{
            background: #dcfce7;
            color: #166534;
        }}

        .reveal .impact-medium {{
            background: #fef3c7;
            color: #92400e;
        }}

        .reveal .impact-low {{
            background: #f1f5f9;
            color: #475569;
        }}

        .reveal .key-points {{
            margin: 1.5rem 0;
        }}

        .reveal .key-points ul {{
            list-style: none;
            padding: 0;
        }}

        .reveal .key-points li {{
            padding: 1rem;
            margin: 0.5rem 0;
            background: var(--light-gradient);
            border-left: 4px solid var(--accent-color);
            border-radius: 0 8px 8px 0;
            transition: all 0.3s ease;
        }}

        .reveal .key-points li:hover {{
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .reveal .tech-details {{
            background: #f8fafc;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            margin: 1rem 0;
        }}

        .reveal .tech-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0;
        }}

        .reveal .tech-badge {{
            background: var(--accent-color);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 500;
        }}

        .reveal .tech-badge.company {{
            background: var(--success-color);
        }}

        .reveal .tech-badge.feature {{
            background: var(--warning-color);
        }}

        .reveal .evaluation-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin: 2rem 0;
        }}

        .reveal .eval-item {{
            text-align: center;
        }}

        .reveal .eval-score {{
            font-size: 3em;
            font-weight: 700;
            color: var(--accent-color);
            display: block;
        }}

        .reveal .eval-label {{
            font-size: 1.1em;
            color: var(--primary-color);
            margin-top: 0.5rem;
        }}

        .reveal .progress-bar {{
            width: 100%;
            height: 12px;
            background: #e2e8f0;
            border-radius: 6px;
            overflow: hidden;
            margin: 1rem 0;
        }}

        .reveal .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
            transition: width 0.8s ease;
            border-radius: 6px;
        }}

        .reveal .sources-section {{
            background: white;
            padding: 2rem;
            border-radius: 15px;
            border: 1px solid #e2e8f0;
        }}

        .reveal .source-links {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-top: 1rem;
        }}

        .reveal .source-link {{
            display: inline-block;
            background: var(--accent-color);
            color: white;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            text-decoration: none;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.3s ease;
        }}

        .reveal .source-link:hover {{
            background: #2563eb;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }}

        .reveal .navigation-card {{
            background: var(--gradient-bg);
            color: white;
            padding: 3rem;
            border-radius: 15px;
            text-align: center;
        }}

        .reveal .nav-buttons {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }}

        .reveal .nav-btn {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 1rem 2rem;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}

        .reveal .nav-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            color: white;
        }}

        .reveal .fade-in {{
            animation: fadeInUp 0.8s ease-out;
        }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
    </style>
</head>

<body>
    <div class="reveal">
        <div class="slides">
            
            <!-- Title Slide -->
            <section class="title-slide">
                <div class="content">
                    <h1>{formatted_date}</h1>
                    <div class="subtitle">AI News Analysis & Insights</div>
                    <div class="date-badge">{data['title']}</div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-number">{data['impact_score']}</span>
                            <span class="stat-label">Impact Score</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">{data['confidence']}%</span>
                            <span class="stat-label">Confidence</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">{len(data['technical_details']['companies']) + len(data['technical_details']['technologies'])}</span>
                            <span class="stat-label">Tech Elements</span>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Summary Slide -->
            <section>
                <h2>📋 ニュースサマリー</h2>
                <div class="content-card {impact_class} fade-in">
                    <div class="card-header">
                        <h3 class="card-title">{data['title']}</h3>
                        <div class="impact-badge {impact_badge_class}">
                            {data['impact_score']}pt
                        </div>
                    </div>
                    
                    <div class="summary-content">
                        <p style="font-size: 1.1em; line-height: 1.6; color: #374151;">{data['summary']}</p>
                    </div>
                    
                    <div class="tech-badges">
                        {company_badges}
                        {tech_badges}
                    </div>
                </div>
            </section>

            <!-- Key Points Slide -->
            <section>
                <h2>🎯 重要ポイント</h2>
                <div class="key-points fade-in">
                    <ul>
                        {key_points_html}
                    </ul>
                </div>
                
                <div class="tech-details">
                    <h3 style="margin-top: 0; color: var(--primary-color);">🔧 技術的特徴</h3>
                    <div class="tech-badges">
                        {feature_badges}
                    </div>
                </div>
            </section>

            <!-- Evaluation Slide -->
            <section>
                <h2>📊 評価分析</h2>
                <div class="evaluation-grid fade-in">
                    <div class="eval-item">
                        <span class="eval-score">{data['evaluation']['engineer_score']}</span>
                        <div class="eval-label">エンジニア向け</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {data['evaluation']['engineer_score']}%"></div>
                        </div>
                    </div>
                    <div class="eval-item">
                        <span class="eval-score">{data['evaluation']['business_score']}</span>
                        <div class="eval-label">ビジネス向け</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {data['evaluation']['business_score']}%"></div>
                        </div>
                    </div>
                </div>
                
                <div class="content-card fade-in">
                    <h3 style="text-align: center; margin-bottom: 1rem;">📈 総合評価</h3>
                    <div style="text-align: center;">
                        <div style="font-size: 3em; font-weight: 700; color: var(--accent-color); margin: 1rem 0;">
                            {data['impact_score']}
                        </div>
                        <div style="font-size: 1.2em; color: var(--primary-color);">
                            Impact Score (100点満点)
                        </div>
                        <div class="progress-bar" style="max-width: 400px; margin: 2rem auto;">
                            <div class="progress-fill" style="width: {data['impact_score']}%"></div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Navigation Slide -->
            <section>
                <div class="navigation-card">
                    <h2 style="color: white;">🧭 ナビゲーション</h2>
                    <p style="opacity: 0.9; margin: 1rem 0;">他のレポートやスライドにアクセス</p>
                    
                    <div class="nav-buttons">
                        <a href="../index.html" class="nav-btn">
                            🏠 ホーム
                        </a>
                        <a href="../day_slides_index.html" class="nav-btn">
                            📅 日次スライド一覧
                        </a>
                        <a href="../ai_ranking_report_20250826.html" class="nav-btn">
                            🏆 ランキングレポート
                        </a>
                    </div>
                </div>
            </section>

        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            controls: true,
            progress: true,
            center: false,
            transition: 'slide'
        }});
    </script>
</body>
</html>'''
    
    return template

def main():
    # Setup paths
    day_dir = Path('C:\\Users\\yoshitaka\\input\\day')
    output_dir = Path('presentations\\day_slides')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all txt files
    total_files = 0
    successful = 0
    failed = []
    
    for file_path in sorted(day_dir.glob('*.txt')):
        total_files += 1
        print(f"Processing {file_path.name}...")
        
        try:
            # Extract date
            date_str, formatted_date = extract_date_from_filename(file_path.stem)
            if not date_str:
                print(f"  ⚠️  Could not extract date from {file_path.name}")
                failed.append(file_path.name)
                continue
            
            # Parse file content
            data = parse_day_file(file_path)
            if not data:
                print(f"  ⚠️  Could not parse content from {file_path.name}")
                failed.append(file_path.name)
                continue
            
            # Generate slide HTML
            html_content = generate_slide_html(data, date_str, formatted_date, file_path.stem)
            
            # Write slide file
            output_file = output_dir / f"day_slide_{date_str.replace('-', '_')}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"  ✅ Generated: {output_file.name}")
            successful += 1
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")
            failed.append(file_path.name)
    
    # Summary
    print("\n" + "="*50)
    print("📊 GENERATION SUMMARY")
    print("="*50)
    print(f"Total files found: {total_files}")
    print(f"Successfully generated: {successful}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print(f"\n⚠️  Failed files: {', '.join(failed)}")
    
    print("\n✨ All available slides have been generated!")
    print(f"📁 Output directory: {output_dir.absolute()}")

if __name__ == "__main__":
    main()