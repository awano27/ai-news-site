import re
from pathlib import Path
import json
import os
import glob

def create_slide_0103():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月3日"
    date_slash = "2026/01/03"
    
    # Try to find title from PDF filename if possible
    pdf_files = glob.glob("input/day/0103-*.pdf")
    pdf_title = "AI Orchestrator Playbook"
    if pdf_files:
        # Extract title from filename "0103-Title.pdf"
        basename = os.path.basename(pdf_files[0])
        # Remove 0103- and .pdf
        pdf_title = basename.replace("0103-", "").replace(".pdf", "").replace("_", " ")

    # Define content variables (based on 0103.txt)
    short_title = "AI Orchestrator Playbook" 
    main_title = "Claude Codeの生みの親が実践する「AI開発パートナー」戦略"
    subtitle = "認知負荷の最小化、超並列処理、複利エンジニアリング、検証ループによる開発の変革"

    # CSS Variables (Dark / Tech theme)
    css_vars = """
    :root {
      --primary: #7c3aed;
      --accent: #a78bfa;
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
    <div style="background: linear-gradient(135deg, #7c3aed, #a78bfa); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(124, 58, 237, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            Claudeを「自律的な開発パートナー」へ変革する
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            Claude Codeの生みの親であるBoris Cherny氏が実践する先進的なワークフローに基づき、ソフトウェア開発における根本的なパラダイムシフトを提示します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🎯</span>
            4つの核心原則
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>認知負荷の最小化</strong>: 人間の余剰注意力を生み出し、より高度な思考に集中できる環境を構築。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>超並列処理</strong>: 複数のタスクを同時進行させ、生産性を飛躍的に向上。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>複利エンジニアリング</strong>: 学びを資産化し、継続的な成長を実現。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">4</span>
                <span><strong>検証ループ</strong>: 成果物の品質を自律的に保証する仕組み。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">バニラセットアップ</div>
            <div class="feature-desc">特別なツールに頼らず、標準的な環境で最大の生産性を実現。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">⚡</span>
            <div class="feature-title">並列タスク処理</div>
            <div class="feature-desc">複数のClaudeインスタンスを活用し、待ち時間をゼロに。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📚</span>
            <div class="feature-title">知識の資産化</div>
            <div class="feature-desc">プロジェクトごとの学びを再利用可能な資産として蓄積。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>パラダイムシフト：AIは「部下」ではなく「パートナー」</h4>
        <p>Boris氏のアプローチは、AIを単なるツールではなく、自律的に判断し行動できる開発パートナーとして扱います。これにより、開発者は戦略的な意思決定に集中できます。</p>
    </div>

    <div class="card">
        <h4>実践的なワークフロー</h4>
        <p>本戦略は理論だけでなく、実際のプロジェクトで検証された具体的な手法を提供します。すぐに実践できる実用的なアプローチです。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0103_slides"
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
        <img src="../../input/day/0103.png" alt="01/03 Visual" onerror="this.src='https://placehold.co/1200x600?text=0103+AI+News'">
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
          {"".join([f'<img src="../../input/day/0103_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
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
    output_path = f"presentations/day_slides/day_slide_2026_01_03.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0103()
