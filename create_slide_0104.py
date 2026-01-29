import re
from pathlib import Path
import json
import os
import glob

def create_slide_0104():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月4日"
    date_slash = "2026/01/04"
    
    # Try to find title from PDF filename if possible
    pdf_files = glob.glob("input/day/0104-*.pdf")
    pdf_title = "DeepTutor: The Ultimate AI Tutor"
    if pdf_files:
        # Extract title from filename "0104-Title.pdf"
        basename = os.path.basename(pdf_files[0])
        # Remove 0104- and .pdf
        pdf_title = basename.replace("0104-", "").replace(".pdf", "").replace("_", " ")

    # Define content variables (based on 0104.txt)
    short_title = "DeepTutor" 
    main_title = "次世代パーソナル学習アシスタント「DeepTutor」"
    subtitle = "コンテンツフリー・アーキテクチャとマルチエージェント・システムによる個別最適化学習の実現"

    # CSS Variables (Education theme - warm and inviting)
    css_vars = """
    :root {
      --primary: #f59e0b;
      --accent: #fb923c;
      --bg-light: #f8f9fa;
      --bg-dark: #212529;
      --text: #212529;
      --text-light: #6c757d;
      --border: #dee2e6;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #f59e0b, #fb923c); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(245, 158, 11, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            あらゆる文書を、インテリジェントな対話のパートナーへ
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            教科書、論文、社内マニュアル——あなたの手元にある文書そのものが、最高の個別指導教師に変わります。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🎓</span>
            DeepTutorの革新的特徴
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>コンテンツフリー・アーキテクチャ</strong>: あらゆる文書を学習素材として活用可能。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>マルチエージェント・システム</strong>: 複数のAIエージェントが協調して最適な学習体験を提供。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>個別最適化学習</strong>: 学習者一人ひとりのニーズに完全に対応。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">📚</span>
            <div class="feature-title">教育現場での活用</div>
            <div class="feature-desc">学生の理解度に合わせた個別指導を大規模に実現。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔬</span>
            <div class="feature-title">研究支援</div>
            <div class="feature-desc">専門論文の深い理解と研究の加速をサポート。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">💼</span>
            <div class="feature-title">企業研修</div>
            <div class="feature-desc">社内マニュアルを活用した効率的な人材育成。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>学習のパラダイムシフト</h4>
        <p>DeepTutorは、画一的なカリキュラムから脱却し、学習者が持つ文書そのものを最高の教材に変えます。これにより、ニッチな専門分野や個別の課題にも完全に対応できます。</p>
    </div>

    <div class="card">
        <h4>高い投資対効果（ROI）</h4>
        <p>教育、研究、企業研修の3つの分野で、学習効率の劇的な向上と人材育成コストの削減を同時に実現します。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0104_slides"
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
        <img src="../../input/day/0104.png" alt="01/04 Visual" onerror="this.src='https://placehold.co/1200x600?text=0104+AI+News'">
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
          {"".join([f'<img src="../../input/day/0104_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
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
    output_path = f"presentations/day_slides/day_slide_2026_01_04.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0104()
