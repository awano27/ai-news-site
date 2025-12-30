import re
from pathlib import Path
import json
import os
import glob

def create_slide_1230():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年12月30日"
    date_slash = "2025/12/30"
    
    # Try to find title from PDF filename if possible
    pdf_files = glob.glob("input/day/1230-*.pdf")
    pdf_title = "Title Placeholder"
    if pdf_files:
        # Extract title from filename "1230-Title.pdf"
        basename = os.path.basename(pdf_files[0])
        # Remove 1230- and .pdf
        pdf_title = basename.replace("1230-", "").replace(".pdf", "").replace("_", " ")

    # Define content variables
    short_title = "AI News" 
    main_title = pdf_title
    subtitle = "Daily AI Update"

    # CSS Variables (Default Blue/Purple theme)
    css_vars = """
    :root {
      --primary: #311b92;
      --accent: #7c4dff;
      --bg-light: #ede7f6;
      --bg-dark: #12005e;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
      --border: #d1c4e9;
      --tron-black: #000000;
    }
    """

    # Intro Box Content (Placeholder)
    intro_box = """
    <div style="background: linear-gradient(135deg, #311b92, #4527a0); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            Daily AI News Update
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            Summary of the latest AI developments for December 30, 2025.
        </p>
    </div>
    """

    # Highlight Box Content (Placeholder)
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🚀</span>
            Key Highlights
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>Highlight 1</strong>: Details about highlight 1.</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>Highlight 2</strong>: Details about highlight 2.</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content (Placeholder)
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <div class="feature-title">Topic A</div>
            <div class="feature-desc">Description of Topic A.</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔄</span>
            <div class="feature-title">Topic B</div>
            <div class="feature-desc">Description of Topic B.</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📈</span>
            <div class="feature-title">Topic C</div>
            <div class="feature-desc">Description of Topic C.</div>
        </div>
    </div>
    """

    # Detail Cards Content (Placeholder)
    detail_cards = """
    <div class="card accent">
        <h4>Analysis</h4>
        <p>In-depth analysis of today's news.</p>
    </div>

    <div class="card">
        <h4>Future Outlook</h4>
        <p>What this means for the future of AI.</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/1230_slides"
    if os.path.exists(slide_dir):
        slides = sorted([f for f in os.listdir(slide_dir) if f.endswith(".jpg")])
        slide_count = len(slides)
    else:
        slide_count = 0
        print(f"Warning: Slide directory {slide_dir} not found. Assuming 0 slides.")

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/1230.jpg" alt="12/30 Visual" onerror="this.src='https://placehold.co/1200x600?text=1230+AI+News'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📰</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>Today's Updates</h3>
        {highlight_box}
        {feature_grid}
        {detail_cards}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全{slide_count}ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/1230_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"📰 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2025_12_30.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1230()
