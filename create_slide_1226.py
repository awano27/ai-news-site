import os
import re
from pathlib import Path

def create_slide_1226():
    # SKILL WORKFLOW: Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Content for 12/26 - Refined after PDF review
    today_str = "2025-12-26"
    date_slash = "2025/12/26"
    title = "AIプロジェクト管理の革命：指示するAIから、自律するオーナーへ (AIPO)"
    short_title = "AIPO: Autonomous Project Owner"
    
    # CSS Variables for "AIPO Deep Blue" theme
    css_vars = """
    :root {
      --primary: #0052cc;
      --accent: #2684ff;
      --bg-light: #f4f5f7;
      --bg-dark: #0747a6;
      --text: #172b4d;
      --text-light: #5e6c84;
      --border: #dfe1e6;
      --tron-black: #091e42;
    }
    """

    intro_box = f"""
    <div style="background: linear-gradient(135deg, var(--bg-dark), #003366); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; border: 1px solid var(--accent); box-shadow: 0 0 20px rgba(0, 194, 203, 0.2);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; color: var(--accent);">GOALを伝えれば、AIが勝手に仕事を進める</p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            従来の「AIの手を引いてあげる」ようなもどかしさ（AIPM）から脱却し、AIが自律的にプロジェクトを完遂する「AIPO」へ。DifyやCursorエージェントを活用した、次世代の意思決定システムを全解説します。
        </p>
    </div>
    """

    highlight_box = f"""
    <div class="highlight-box">
      <strong>旧来のパラダイム「AIPM」の限界:</strong> 人間がAIに逐次的な指示を出し続ける必要があり、文脈の忘却や認知負荷の増大が大きな壁となっていました。AIPOはこれらの制約を超え、真の自律性を実現します。
    </div>
    """

    feature_grid = """
    <div class="feature-grid">
      <div class="feature-item">
        <span class="feature-icon">⛓️</span>
        <div class="feature-title">パラダイムシフト</div>
        <div class="feature-desc">「指示するAI」から、ゴールを共有して「自律するオーナー」へ。</div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">🧠</span>
        <div class="feature-title">認知負荷の低減</div>
        <div class="feature-desc">AIの管理コストを最小化し、人間は高次元な設計に集中可能。</div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">📍</span>
        <div class="feature-title">技術スタック</div>
        <div class="feature-desc">Dify、Cursor、AIエージェントを組み合わせた実用的な構成。</div>
      </div>
    </div>
    """

    detail_cards = f"""
    <div class="card accent">
      <h4>著者：Daisuke Miyata氏（株式会社エクスプラザ）</h4>
      <p>生成AIエバンジェリストとしての知見を集約。単なる理論にとどまらず、ツールを駆使して「行動する」エージェントとしてのAI活用を提唱しています。</p>
    </div>
    """

    # Assemble Main Content (14 pages)
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/1226.jpg" alt="AIPO Visual" onerror="this.src='https://placehold.co/1200x600?text=1226+AIPO+Autonomous+Project+Owner'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🔗</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>AIプロジェクト管理の革命</h3>
        {highlight_box}
        {feature_grid}
        {detail_cards}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全15ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/1226_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, 16)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders to match base_template.html
    html_content = template_html_content
    
    # Handle the weirdly formatted CSS block
    css_placeholder = "{\n        {\n        CSS_VARS_BLOCK\n      }\n    }"
    if css_placeholder in html_content:
        html_content = html_content.replace(css_placeholder, css_vars)
    else:
        # Fallback for other variations
        html_content = re.sub(r'\{\s*\{\s*CSS_VARS_BLOCK\s*\}\s*\}', css_vars, html_content)

    html_content = html_content.replace("{{FULL_TITLE}}", title)
    html_content = html_content.replace("{{H1_TITLE}}", title)
    html_content = html_content.replace("{{DATE}}", date_slash)
    html_content = html_content.replace("{{BREAKING_BADGE_TEXT}}", f"🚀 {date_slash} レポート | {short_title}")
    html_content = html_content.replace("{{SUBTITLE}}", "指示するAIから、自律するオーナーへの進化")
    html_content = html_content.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Output path
    output_filename = f"day_slide_{today_str.replace('-', '_')}.html"
    output_path = os.path.join("presentations", "day_slides", output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1226()
