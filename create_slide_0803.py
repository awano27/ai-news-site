import re
from pathlib import Path
import json
import os

def create_slide_0803():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年8月3日"
    date_slash = "2025/08/03"
    
    # Define content variables
    short_title = "AlphaEarth Foundations" 
    main_title = "Google DeepMind: AlphaEarth Foundations"
    subtitle = "地球規模のAI基盤モデル、Natureで拡散"

    # CSS Variables for "Nature Green" theme
    css_vars = """
    :root {
      --primary: #2e7d32;
      --accent: #a5d6a7;
      --bg-light: #e8f5e9;
      --bg-dark: #1b5e20;
      --text: #e8f5e9;
      --text-light: #c8e6c9;
      --border: #43a047;
      --tron-black: #000a12;
    }
    body {
        background: linear-gradient(135deg, #000a12 0%, #1b5e20 100%);
    }
    .container {
        background: rgba(27, 94, 32, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid var(--primary);
    }
    .card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--border);
    }
    .feature-item {
        background: rgba(255, 255, 255, 0.05);
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #1b5e20, #000a12); color: var(--accent); padding: 24px; border-radius: 16px; margin-bottom: 32px; border: 1px solid var(--primary); box-shadow: 0 0 15px rgba(46, 125, 50, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em; text-shadow: 0 0 5px var(--primary);">
            地球を「埋め込み」で理解する
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6; color: var(--text);">
            Google DeepMindの「AlphaEarth Foundations」がNature公式Xで拡散され、大きな注目を集めています。10m解像度・64次元の「仮想衛星」モデルは、地球観測データを統合し、誤差を大幅に低減。Earth Engineで即日利用可能です。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: rgba(0, 0, 0, 0.3); border: 1px solid var(--accent); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--accent); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🌍</span>
            3つの革新ポイント
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>Nature拡散</strong>: 科学界の権威であるNatureが注目。技術的信頼性とインパクトの証。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>即日実装</strong>: Earth Engineのデータカタログに公開済み。ブラウザ上で数行のコードで解析開始。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>ビジネス直結</strong>: 立地選定、災害対応、ESGレポートなど、明日の意思決定に使える精度と速度。</span>
            </li>
        </ul>
    </div>
    """

    # Code Snippet Content
    code_snippet = """
    <div style="background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 16px; margin-bottom: 32px; font-family: 'Fira Code', monospace; overflow-x: auto;">
        <div style="color: #808080; margin-bottom: 8px;">// Earth Engine Code Editor Example: Tokyo Station Analysis</div>
        <div style="color: #d4d4d4;">
            <span style="color: #569cd6;">var</span> ds = ee.ImageCollection(<span style="color: #ce9178;">'GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL'</span>);<br>
            <span style="color: #569cd6;">var</span> pt = ee.Geometry.Point(139.7671, 35.6812); <span style="color: #6a9955;">// Tokyo Station</span><br><br>
            <span style="color: #569cd6;">var</span> y2023 = ds.filterDate(<span style="color: #ce9178;">'2023-01-01'</span>,<span style="color: #ce9178;">'2024-01-01'</span>).filterBounds(pt).first();<br>
            <span style="color: #569cd6;">var</span> y2024 = ds.filterDate(<span style="color: #ce9178;">'2024-01-01'</span>,<span style="color: #ce9178;">'2025-01-01'</span>).filterBounds(pt).first();<br><br>
            <span style="color: #6a9955;">// Calculate Cosine Similarity</span><br>
            <span style="color: #569cd6;">var</span> sim = y2023.multiply(y2024).reduce(ee.Reducer.sum());<br>
            Map.addLayer(sim, {min:0,max:1}, <span style="color: #ce9178;">'23→24 Similarity'</span>);
        </div>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">🛰️</span>
            <div class="feature-title" style="color: var(--accent);">Virtual Satellite</div>
            <div class="feature-desc">10m解像度×64次元の埋め込み表現。物理的な制約を超えた「仮想衛星」。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">📉</span>
            <div class="feature-title" style="color: var(--accent);">Error Reduction</div>
            <div class="feature-desc">従来手法と比較して誤差を23.9%低減。高精度な地表・沿岸マッピングを実現。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">⚡</span>
            <div class="feature-title" style="color: var(--accent);">Analysis Ready</div>
            <div class="feature-desc">前処理不要。雲マスクなどの手間を省き、即座にインサイト抽出へ。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4 style="color: var(--accent);">ビジネスインパクト</h4>
        <p>「明日から使える」がキーワード。小売店の出店計画、物流拠点の最適化、災害時の迅速な状況把握。AlphaEarth Foundationsは、これらの意思決定に必要な「地図の基礎体力」を劇的に向上させます。</p>
    </div>
    """

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="https://placehold.co/1200x600/1b5e20/a5d6a7?text=AlphaEarth+Foundations" alt="AlphaEarth Foundations Visual" onerror="this.src='https://placehold.co/1200x600/1b5e20/a5d6a7?text=AlphaEarth+Foundations'">
      </div>
      <section class="section">
        <div class="section-header" style="border-bottom-color: var(--accent);">
          <span class="section-icon">🌌</span>
          <h2 style="color: var(--text);">{short_title}</h2>
        </div>
        {intro_box}
        <h3 style="color: var(--text);">Quick Start: Tokyo Analysis</h3>
        {code_snippet}
        {highlight_box}
        {feature_grid}
        {detail_cards}
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
    output_path = f"presentations/day_slides/day_slide_2025_08_03.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0803()
