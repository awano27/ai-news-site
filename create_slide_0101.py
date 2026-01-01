import re
from pathlib import Path
import json
import os
import glob

def create_slide_0101():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月1日"
    date_slash = "2026/01/01"
    
    # Try to find title from PDF filename if possible
    pdf_files = glob.glob("input/day/0101-*.pdf")
    pdf_title = "Title Placeholder"
    if pdf_files:
        # Extract title from filename "0101-Title.pdf"
        basename = os.path.basename(pdf_files[0])
        # Remove 0101- and .pdf
        pdf_title = basename.replace("0101-", "").replace(".pdf", "").replace("_", " ")

    # Define content variables
    short_title = "2026年AI実装ガイド" 
    main_title = "2026年戦略分析：技術的特異点の到来と変容"
    subtitle = "AI・自動化・ナノテクノロジーが再定義する地政学、経済、そして社会の構造"

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

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #856404, #ffc107); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(133, 100, 4, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            2026年—転換点としての現在地
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            AIが理論的な可能性から、地政学、経済、社会の構造を具体的に再定義する実行可能な力へと移行する、重大な転換点。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🎯</span>
            2026年の3つの重要指標
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>AIガバナンスの本格化</strong>: EU AI法の施行など、規制や指針が「原則から実践へ」と移行。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>計算能力の急増</strong>: 2027年までに計算資源は10倍に。国家インフラ規模の投資が加速。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>人間と機械の融合</strong>: BCI技術の進展により、思考のみでデバイスを操作する共生時代へ。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🚀</span>
            <div class="feature-title">Singularity</div>
            <div class="feature-desc">2026-2029年のAGI達成予測。収穫加速の法則による指数関数的進歩。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">💼</span>
            <div class="feature-title">Labor Market</div>
            <div class="feature-desc">全世界の雇用の40%に影響。破壊と補完の二重構造による再編。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🌐</span>
            <div class="feature-title">Geopolitics</div>
            <div class="feature-desc">超知能を巡る覇権競争。国家安全保障の至上命題としてのAI開発。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>物理的限界とボトルネック</h4>
        <p>爆発的な電力需要とTSMCへの極端な依存。指数関数的進歩を阻む「物理的な壁」への対策が急務となっています。</p>
    </div>

    <div class="card">
        <h4>実存的リスクとアライメント</h4>
        <p>制御不能なAIや悪意ある利用への懸念。人類の価値観とAIの目標を一致させる「アライメント」が最重要課題に。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0101_slides"
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
        <img src="../../input/day/0101.png" alt="01/01 Visual" onerror="this.src='https://placehold.co/1200x600?text=0101+AI+News'">
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
          {"".join([f'<img src="../../input/day/0101_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
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
    output_path = f"presentations/day_slides/day_slide_2026_01_01.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0101()
