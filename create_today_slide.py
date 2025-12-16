import json
import re
from pathlib import Path
import datetime

def create_slide():
    today_str = "2025-12-09"
    json_path = Path(f"public-pages/news/{today_str}.json")
    template_path = Path("presentations/day_slides/day_slide_2025_08_27.html")
    output_path = Path(f"presentations/day_slides/day_slide_{today_str.replace('-', '_')}.html")

    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data['items']:
        print("Error: No items in JSON")
        return

    item = data['items'][0]
    
    # Clean up title if it's too long
    title = item['title']
    if len(title) > 50:
        # Try to extract a shorter title
        match = re.match(r'(.*?)(?:は、|が、|で、)', title)
        if match:
            title = match.group(1)
        else:
            title = title[:50] + "..."

    # Prepare content
    summary = item['summary']
    points_html = "<ul>"
    for point in item['points']:
        # Remove bullets if present at start
        clean_point = re.sub(r'^[・\-\d\.]+\s*', '', point)
        # Highlight key phrases
        clean_point = clean_point.replace('**', '<strong>').replace('**', '</strong>')
        points_html += f"<li>{clean_point}</li>"
    points_html += "</ul>"

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Replacements
    html = template
    
    # Date
    date_formatted = "2025年12月9日"
    html = re.sub(r'<title>.*?</title>', f'<title>{date_formatted} - {title}</title>', html)
    html = re.sub(r'<div class="date-badge">.*?</div>', f'<div class="date-badge">{date_formatted}</div>', html)
    
    # Title Slide
    html = html.replace('2025年8月27日', date_formatted)
    html = html.replace('NECのAIエージェント革命：Web操作で人間超え', title)
    html = re.sub(r'<div style="background: rgba\(255,255,255,0.2\);.*?</div>', 
                  f'<div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 15px; margin: 2rem 0;">{title}</div>', 
                  html, flags=re.DOTALL)

    # Stats (Placeholder for now, or extract if possible)
    # Using generic stats or removing them might be better, but let's keep structure
    html = re.sub(r'<span class="stat-number">.*?</span>', '<span class="stat-number">95</span>', html, count=1)
    html = re.sub(r'<span class="stat-label">Impact Score</span>', '<span class="stat-label">Impact Score</span>', html)
    
    # Summary Slide
    html = html.replace('NEC AIエージェント「cotomi Act」発表', title)
    html = re.sub(r'<div class="summary-content">.*?</div>', 
                  f'<div class="summary-content"><p style="font-size: 1.1em; line-height: 1.6; color: #374151;">{summary}</p></div>', 
                  html, flags=re.DOTALL)
    
    # Key Points Slide
    html = re.sub(r'<div class="key-points">.*?</div>', 
                  f'<div class="key-points">{points_html}</div>', 
                  html, flags=re.DOTALL)

    # Tech Badges (Reset to generic)
    badges_html = """
    <div class="tech-badges">
        <span class="tech-badge company">China</span>
        <span class="tech-badge">AI Strategy</span>
        <span class="tech-badge">Vision 2049</span>
    </div>
    """
    html = re.sub(r'<div class="tech-badges">.*?</div>', badges_html, html, flags=re.DOTALL)

    # Evaluation Slide - Adjust score
    html = re.sub(r'<div style="font-size: 3em; font-weight: 700; color: var(--accent-color); margin: 1rem 0;">.*?</div>',
                  '<div style="font-size: 3em; font-weight: 700; color: var(--accent-color); margin: 1rem 0;">95</div>',
                  html)

    # Links - Clear existing and add placeholder or empty
    links_html = """
    <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1rem;">
        <!-- Links would go here -->
    </div>
    """
    html = re.sub(r'<div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1rem;">.*?</div>',
                  links_html, html, flags=re.DOTALL)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Created {output_path}")

if __name__ == "__main__":
    create_slide()
