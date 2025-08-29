#!/usr/bin/env python3
"""Generate missing daily slides from input day files."""

import os
import json
import re
from pathlib import Path
from datetime import datetime

def parse_day_file(file_path):
    """Parse a day file and extract structured information."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Extract basic info
    lines = content.split('\n')
    title_line = lines[2] if len(lines) > 2 else ""
    title_match = re.search(r'\*\*(.*?)\*\*', title_line)
    title = title_match.group(1) if title_match else "AI News Update"
    
    # Extract summary (TL;DR section)
    summary_match = re.search(r'\*\*TL;DR\*\*[：:](.*?)(?=\n\n|\n---)', content, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""
    
    # Clean up summary
    summary = re.sub(r'\([^)]*\)', '', summary)  # Remove citations
    summary = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', summary)  # Convert bold
    summary = summary.replace('\\*\\*', '**')  # Fix escaped asterisks
    
    # Extract key points from main content
    key_points = []
    sections = re.split(r'\n##\s+', content)
    for section in sections[1:3]:  # Take first 2 main sections
        if section:
            points = re.findall(r'^\d+\.\s+\*\*(.*?)\*\*[：:](.*?)(?=\n\d+\.|\n\n|\Z)', section, re.MULTILINE | re.DOTALL)
            for point_title, point_content in points:
                clean_content = re.sub(r'\([^)]*\)', '', point_content).strip()
                clean_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', clean_content)
                key_points.append({
                    'title': point_title.strip(),
                    'content': clean_content[:200] + '...' if len(clean_content) > 200 else clean_content
                })
    
    # Generate evaluation scores based on content analysis
    impact_score = 85 if 'Google' in content or 'Meta' in content else 75
    technical_score = 90 if 'API' in content or 'SDK' in content else 80
    business_score = 80 if '売上' in content or 'ROI' in content else 70
    
    # Extract companies mentioned
    companies = []
    company_patterns = ['Google', 'Meta', 'OpenAI', 'Microsoft', 'Amazon', 'Apple', 'Tesla', 'NVIDIA', 'Baidu', 'Anthropic']
    for company in company_patterns:
        if company in content:
            companies.append(company)
    
    # Extract technologies
    tech_patterns = ['AI', 'ML', '機械学習', 'ディープラーニング', 'LLM', 'GPT', 'API', 'SDK']
    technologies = []
    for tech in tech_patterns:
        if tech in content:
            technologies.append(tech)
    
    return {
        'title': title,
        'summary': summary,
        'key_points': key_points[:4],  # Limit to 4 points
        'evaluation': {
            'impact_score': impact_score,
            'technical_score': technical_score,
            'business_score': business_score,
            'overall_score': round((impact_score + technical_score + business_score) / 3)
        },
        'companies': companies[:3],  # Limit to 3 companies
        'technologies': technologies[:4],  # Limit to 4 technologies
        'source_count': len(re.findall(r'\[.*?\]:', content))
    }

def create_slide_html(date_str, data):
    """Create HTML slide content."""
    template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily AI News - {date_str}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/plugin/notes/notes.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/plugin/markdown/markdown.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/plugin/highlight/highlight.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.css">
    <style>
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --border-color: #e5e7eb;
        }}

        .reveal {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}

        .reveal .slides section {{
            background: var(--bg-primary);
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}

        .slide-title {{
            color: var(--primary-color);
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-align: center;
            border-bottom: 3px solid var(--accent-color);
            padding-bottom: 0.5rem;
        }}

        .slide-date {{
            color: var(--text-secondary);
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 500;
        }}

        .summary-box {{
            background: var(--bg-secondary);
            border-left: 4px solid var(--accent-color);
            padding: 1.5rem;
            margin: 1.5rem 0;
            border-radius: 8px;
            font-size: 1.1rem;
            line-height: 1.6;
        }}

        .key-points {{
            display: grid;
            gap: 1rem;
            margin: 2rem 0;
        }}

        .key-point {{
            background: var(--bg-secondary);
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid var(--success-color);
        }}

        .key-point h4 {{
            color: var(--primary-color);
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
        }}

        .key-point p {{
            color: var(--text-primary);
            font-size: 0.95rem;
            margin: 0;
            line-height: 1.5;
        }}

        .evaluation-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}

        .score-card {{
            background: var(--bg-secondary);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            border: 2px solid var(--border-color);
        }}

        .score-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
        }}

        .score-label {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }}

        .metadata-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin: 2rem 0;
        }}

        .metadata-box {{
            background: var(--bg-secondary);
            padding: 1rem;
            border-radius: 8px;
        }}

        .metadata-box h4 {{
            color: var(--primary-color);
            font-size: 1rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
        }}

        .tag {{
            display: inline-block;
            background: var(--accent-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin: 0.25rem;
        }}

        .chart-container {{
            width: 100%;
            max-width: 400px;
            margin: 2rem auto;
        }}

        .navigation {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }}

        .nav-button {{
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            margin-left: 0.5rem;
            transition: all 0.3s ease;
        }}

        .nav-button:hover {{
            background: var(--secondary-color);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            <!-- Title Slide -->
            <section>
                <h1 class="slide-title">{data['title']}</h1>
                <p class="slide-date">Daily AI News Report - {date_str}</p>
                <div class="summary-box">
                    <p>{data['summary']}</p>
                </div>
                <div class="evaluation-grid">
                    <div class="score-card">
                        <div class="score-value">{data['evaluation']['overall_score']}</div>
                        <div class="score-label">Overall Score</div>
                    </div>
                    <div class="score-card">
                        <div class="score-value">{len(data['key_points'])}</div>
                        <div class="score-label">Key Points</div>
                    </div>
                    <div class="score-card">
                        <div class="score-value">{data['source_count']}</div>
                        <div class="score-label">Sources</div>
                    </div>
                </div>
            </section>

            <!-- Key Points Slide -->
            <section>
                <h2 class="slide-title">Key Developments</h2>
                <div class="key-points">
"""

    # Add key points
    for i, point in enumerate(data['key_points'], 1):
        template += f"""                    <div class="key-point">
                        <h4>{i}. {point['title']}</h4>
                        <p>{point['content']}</p>
                    </div>
"""

    template += """                </div>
            </section>

            <!-- Evaluation Slide -->
            <section>
                <h2 class="slide-title">Impact Evaluation</h2>
                <div class="evaluation-grid">
                    <div class="score-card">
                        <div class="score-value">""" + str(data['evaluation']['impact_score']) + """</div>
                        <div class="score-label">Impact Score</div>
                    </div>
                    <div class="score-card">
                        <div class="score-value">""" + str(data['evaluation']['technical_score']) + """</div>
                        <div class="score-label">Technical Score</div>
                    </div>
                    <div class="score-card">
                        <div class="score-value">""" + str(data['evaluation']['business_score']) + """</div>
                        <div class="score-label">Business Score</div>
                    </div>
                    <div class="score-card">
                        <div class="score-value">""" + str(data['evaluation']['overall_score']) + """</div>
                        <div class="score-label">Overall Score</div>
                    </div>
                </div>

                <div class="chart-container">
                    <canvas id="evaluationChart"></canvas>
                </div>
            </section>

            <!-- Metadata Slide -->
            <section>
                <h2 class="slide-title">Analysis Overview</h2>
                <div class="metadata-section">
                    <div class="metadata-box">
                        <h4>Companies Mentioned</h4>"""

    # Add companies
    for company in data['companies']:
        template += f"""
                        <span class="tag">{company}</span>"""

    template += """
                    </div>
                    <div class="metadata-box">
                        <h4>Technologies</h4>"""

    # Add technologies  
    for tech in data['technologies']:
        template += f"""
                        <span class="tag">{tech}</span>"""

    template += f"""
                    </div>
                </div>

                <div style="text-align: center; margin-top: 2rem;">
                    <p style="color: var(--text-secondary); font-size: 0.9rem;">
                        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • 
                        Sources: {data['source_count']} • 
                        Analysis: AI-powered content evaluation
                    </p>
                </div>
            </section>
        </div>
    </div>

    <div class="navigation">
        <button class="nav-button" onclick="window.parent.postMessage('navigate:dashboard', '*')">
            ← Dashboard
        </button>
        <button class="nav-button" onclick="window.parent.postMessage('navigate:slides', '*')">
            All Slides →
        </button>
    </div>

    <script>
        Reveal.initialize({{
            hash: true,
            transition: 'slide',
            transitionSpeed: 'default',
            backgroundTransition: 'fade',
            controls: true,
            progress: true,
            center: true,
            touch: true,
            loop: false,
            rtl: false,
            navigationMode: 'default',
            plugins: [RevealMarkdown, RevealHighlight, RevealNotes]
        }});

        // Create evaluation chart
        const ctx = document.getElementById('evaluationChart').getContext('2d');
        new Chart(ctx, {{
            type: 'radar',
            data: {{
                labels: ['Impact', 'Technical', 'Business', 'Overall'],
                datasets: [{{
                    label: 'Scores',
                    data: [{data['evaluation']['impact_score']}, {data['evaluation']['technical_score']}, {data['evaluation']['business_score']}, {data['evaluation']['overall_score']}],
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgb(59, 130, 246)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            stepSize: 20
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    return template

def main():
    input_dir = Path("C:/Users/yoshitaka/input/day")
    output_dir = Path("C:/Users/yoshitaka/ai-news-site/presentations/day_slides")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get existing slides
    existing_slides = {f.stem.split('_')[-1] for f in output_dir.glob("day_slide_*.html")}
    
    created_count = 0
    
    # Process each day file
    for day_file in sorted(input_dir.glob("*.txt")):
        date_part = day_file.stem  # e.g., "0804"
        date_formatted = f"2025_08_{date_part[2:4]}"  # e.g., "2025_08_04"
        
        # Skip if slide already exists
        if date_part[2:4] in existing_slides:
            print(f"Skipping {date_part} - slide already exists")
            continue
        
        try:
            # Parse day file
            data = parse_day_file(day_file)
            
            # Create slide HTML
            slide_html = create_slide_html(f"2025-08-{date_part[2:4]}", data)
            
            # Write slide file
            output_file = output_dir / f"day_slide_{date_formatted}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(slide_html)
            
            print(f"Created: {output_file.name}")
            created_count += 1
            
        except Exception as e:
            print(f"Error processing {day_file.name}: {e}")
    
    print(f"Generated {created_count} new slides")

if __name__ == "__main__":
    main()