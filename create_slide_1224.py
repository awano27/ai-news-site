import re
from pathlib import Path
import json
import os

def create_slide_1224():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年12月24日"
    date_slash = "2025/12/24"
    
    # Define content variables
    short_title = "AGI Now" 
    main_title = "Exponential Acceleration"
    subtitle = "指数関数的な加速とAGIの現在地"

    # CSS Variables for "AGI Blue" theme
    css_vars = """
    :root {
      --primary: #1976d2;
      --accent: #00bcd4;
      --bg-light: #e3f2fd;
      --bg-dark: #0d47a1;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
      --border: #bbdefb;
      --tron-black: #000a12;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #1976d2, #1565c0); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            AGI実現へのカウントダウン
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            2025年、AI技術はかつてない速度で進化を遂げました。「AGI Frontier 2025 Status Report」は、汎用人工知能（AGI）に向けた現在の到達点、技術的課題、そして未来へのロードマップを包括的に解説します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">📊</span>
            2025年の主要な進展
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>推論能力の飛躍</strong>: 複雑な論理的推論において、人間専門家レベルを一貫して達成。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>自律性の拡大</strong>: 長期間にわたるタスク遂行と自己修正能力の実装。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>物理世界への適応</strong>: ロボティクスとの融合による、実世界での操作能力の向上。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">認知アーキテクチャ</div>
            <div class="feature-desc">人間の脳を模倣した新しい記憶・学習システムの採用。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">⚡</span>
            <div class="feature-title">エネルギー効率</div>
            <div class="feature-desc">高性能を維持しつつの消費電力削減技術のブレイクスルー。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🛡️</span>
            <div class="feature-title">AIセーフティ</div>
            <div class="feature-desc">高度な知能を制御・整列させるための新たな安全基準の確立。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>AGIとは何か？</h4>
        <p>AGI（Artificial General Intelligence）は、人間のようにあらゆる知的タスクを学習・実行できる人工知能です。特定のタスクに特化した従来のAI（Narrow AI）とは異なり、未知の状況にも適応し、創造的な問題解決を行う能力を持ちます。</p>
    </div>

    <div class="card">
        <h4>2026年への展望</h4>
        <p>2025年の成果を基盤に、2026年は「社会実装」と「協調」がキーワードとなります。AGIシステムが社会インフラに統合され、人間とAIが真のパートナーとして共創する未来が現実のものとなりつつあります。</p>
    </div>
    """

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/1224.jpg" alt="AGI Frontier 2025 Visual" onerror="this.src='https://placehold.co/1200x600?text=1224+AGI+Frontier'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🌐</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>AGI開発の最前線</h3>
        {highlight_box}
        {feature_grid}
        {detail_cards}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全20ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/1224_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, 21)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🚀 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2025_12_24.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1224()
