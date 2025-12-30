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
    short_title = "MetaによるManus買収" 
    main_title = "AI業界の常識を覆した4つの「サプライズ」"
    subtitle = "「対話」から「実行」へ：AI覇権争いの主戦場がシフト"

    # CSS Variables (Meta Blue / Tech Dark theme)
    css_vars = """
    :root {
      --primary: #0668E1;
      --accent: #00F2FF;
      --bg-light: #f0f2f5;
      --bg-dark: #050505;
      --text: #1c1e21;
      --text-light: #65676b;
      --border: #dddfe2;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #0668E1, #00F2FF); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(6, 104, 225, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            AIの価値基準が「対話」から「実行」へ
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            MetaによるManus買収は、AIの覇権がモデルの「頭脳」ではなく「手足」で争われる時代への歴史的な転換点です。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">💡</span>
            4つの衝撃的な真実（サプライズ）
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>価値の源泉</strong>: 最強の頭脳（基盤モデル）ではなく、最高の司令塔（実行レイヤー）へ。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>技術革新</strong>: 「実行」を支えるCodeActやマルチエージェント・アーキテクチャ。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>非同期実行</strong>: ユーザーがPCを閉じた後も自律的にタスクを完遂。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">4</span>
                <span><strong>地政学的脱出</strong>: 中国発技術が地政学的制約を越えて米テック企業へExit。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <div class="feature-title">CodeAct</div>
            <div class="feature-desc">Pythonコードを直接生成・実行。JSONベースより柔軟で成功率が20%向上。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔄</span>
            <div class="feature-title">Multi-Agent</div>
            <div class="feature-desc">PlannerとExecutorが協調。GAIAベンチマークで86.5%の驚異的スコア。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">Context Eng.</div>
            <div class="feature-desc">KV-Cache最適化やtodo.mdパターンで、長期タスクの目的逸脱を防止。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>非同期実行能力の衝撃</h4>
        <p>クラウド上のVMで動作するため、ユーザーがオフラインでもタスクを継続。8,000万台以上の仮想コンピュータを生成し、147兆トークンを処理する圧倒的なスケールを実現しています。</p>
    </div>

    <div class="card">
        <h4>戦略的な「脱中国」措置</h4>
        <p>Metaは買収に際し、中国の投資家との関係断絶、中国内サービスの停止、データの隔離を徹底。地政学的リスクを遮断し、グローバル市場での成功を確実なものにしました。</p>
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
        <img src="../../input/day/1230.png" alt="12/30 Visual" onerror="this.src='https://placehold.co/1200x600?text=1230+AI+News'">
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
