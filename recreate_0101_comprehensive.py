import os
import re
from pathlib import Path

def parse_txt_content(content):
    sections = []
    # Split by horizontal lines
    raw_sections = re.split(r'-{10,}', content)
    
    for raw in raw_sections:
        stripped = raw.strip()
        if not stripped:
            continue
        
        # Skip speaker notes for the main slide content, but keep for later if needed
        if "スピーカーノート:" in stripped:
            continue
            
        lines = stripped.split('\n')
        title = lines[0].strip()
        body = '\n'.join(lines[1:]).strip()
        
        sections.append({
            'title': title,
            'body': body
        })
    return sections

def format_body(body):
    # Convert bullet points to list items
    lines = body.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
            
        if line.startswith('*') or line.startswith('-') or line.startswith('・'):
            if not in_list:
                html_lines.append('<ul style="margin-left: 20px; margin-bottom: 16px;">')
                in_list = True
            text = re.sub(r'^[*\-・]\s*', '', line)
            # Bold keys like "定義" or "中核概念"
            text = re.sub(r'^([^：:]+)[：:]', r'<strong>\1</strong>：', text)
            html_lines.append(f'<li style="margin-bottom: 8px;">{text}</li>')
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            # Handle tables (simple tab/space separated)
            if '\t' in line or '    ' in line:
                cols = re.split(r'\t| {4,}', line)
                html_lines.append('<table style="width:100%; border-collapse: collapse; margin: 20px 0;">')
                html_lines.append('<tr>' + ''.join([f'<th style="border: 1px solid #ffeeba; padding: 12px; background: #856404; color: white;">{c}</th>' for c in cols]) + '</tr>')
                continue # The next lines will be data? (This is a bit simplified)
            
            # Regular paragraph
            html_lines.append(f'<p style="margin-bottom: 16px; line-height: 1.8;">{line}</p>')
            
    if in_list:
        html_lines.append("</ul>")
        
    return '\n'.join(html_lines)

def main():
    input_path = "input/day/0101.txt"
    template_path = "base_template.html"
    output_path = "presentations/day_slides/day_slide_2026_01_01.html"
    
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    lines = content.split('\n')
    main_title = lines[0].strip()
    subtitle = lines[2].strip()
    date_jp = "2026年1月1日"
    date_slash = "2026/01/01"
    
    sections = parse_txt_content(content)
    
    # CSS Variables (Gold / New Year theme)
    css_vars = """
    :root {
      --primary: #856404;
      --accent: #ffc107;
      --bg-light: #fff3cd;
      --bg-dark: #212529;
      --text: #212529;
      --text-light: #6c757d;
      --border: #ffeeba;
      --tron-black: #000000;
    }
    """
    
    html_content = []
    html_content.append('<main style="padding: 48px;">')
    
    # Top Image
    html_content.append('  <div class="top-image-container" style="text-align: center; margin-bottom: 48px;">')
    html_content.append('    <img src="../../input/day/0101.png" alt="01/01 Visual" style="width: 100%; max-width: 1000px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">')
    html_content.append('  </div>')
    
    for i, section in enumerate(sections):
        # Skip the header info if it's identical to main title
        if section['title'] == main_title or "日付:" in section['title']:
            continue
            
        html_content.append(f'<section class="section" style="margin-bottom: 48px;">')
        html_content.append(f'  <div class="section-header" style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 3px solid var(--primary);">')
        html_content.append(f'    <span class="section-icon" style="font-size: 2rem;">📌</span>')
        html_content.append(f'    <h2 style="font-size: 1.8rem; font-weight: 800;">{section["title"]}</h2>')
        html_content.append(f'  </div>')
        
        # Special handling for "結論サマリー" and "2027年以降" which contain tables
        if "サマリー" in section['title'] or "シナリオ" in section['title']:
            lines = section['body'].split('\n')
            p_text = []
            table_data = []
            for l in lines:
                if '\t' in l or '    ' in l:
                    table_data.append(re.split(r'\t| {4,}', l.strip()))
                else:
                    p_text.append(l)
            
            if p_text:
                html_content.append(f'<div class="highlight-box" style="background-color: #fff8e1; border-left: 5px solid var(--primary); padding: 24px; margin-bottom: 24px; border-radius: 8px;">')
                html_content.append(format_body('\n'.join(p_text)))
                html_content.append('</div>')
            
            if table_data:
                html_content.append('<div style="overflow-x: auto; margin-bottom: 24px;">')
                html_content.append('<table style="width:100%; border-collapse: collapse; border: 1px solid #ffeeba;">')
                for idx, row in enumerate(table_data):
                    bg = "#856404" if idx == 0 else "white"
                    color = "white" if idx == 0 else "black"
                    weight = "bold" if idx == 0 else "normal"
                    html_content.append('<tr>')
                    for cell in row:
                        cell_html = cell.replace('<br>', '<br/>')
                        html_content.append(f'<td style="border: 1px solid #ffeeba; padding: 12px; background: {bg}; color: {color}; font-weight: {weight}; vertical-align: top;">{cell_html}</td>')
                    html_content.append('</tr>')
                html_content.append('</table>')
                html_content.append('</div>')
        else:
            # Regular section
            html_content.append('<div class="card" style="background: white; border: 1px solid var(--border); border-radius: 16px; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">')
            html_content.append(format_body(section['body']))
            html_content.append('</div>')
            
        html_content.append('</section>')
        
    # Slides Section
    slide_dir = Path("input/day/0101_slides")
    if slide_dir.exists():
        slides = sorted(list(slide_dir.glob("*.jpg")))
        if slides:
            html_content.append('<section class="section">')
            html_content.append('  <div class="section-header" style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 3px solid var(--primary);">')
            html_content.append('    <span class="section-icon" style="font-size: 2rem;">📖</span>')
            html_content.append(f'    <h2 style="font-size: 1.8rem; font-weight: 800;">スライド資料 (全{len(slides)}ページ)</h2>')
            html_content.append('  </div>')
            html_content.append('  <div class="slides-container" style="display: flex; flex-direction: column; align-items: center; gap: 24px;">')
            for i in range(1, len(slides) + 1):
                html_content.append(f'    <img src="../../input/day/0101_slides/slide_{i:03d}.jpg" alt="Slide {i}" style="width: 100%; max-width: 1000px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); border: 1px solid var(--border);">')
            html_content.append('  </div>')
            html_content.append('</section>')
            
    html_content.append('</main>')
    
    # Assembly
    final_html = template
    final_html = final_html.replace("{{FULL_TITLE}}", f"2026年AI実装ガイド: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"📰 {date_jp}レポート | 2026年AI実装ガイド")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", '\n'.join(html_content))
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    main()
