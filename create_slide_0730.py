import re
from pathlib import Path
import json
import os

def create_slide_0730():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年7月30日"
    date_slash = "2025/07/30"
    
    # Define content variables
    short_title = "AlphaEarth Foundations" 
    main_title = "Google DeepMind: AlphaEarth Foundations"
    subtitle = "地球全体を高精度に表現する「仮想衛星」埋め込みモデル"

    # CSS Variables for "Dark Earth" theme
    css_vars = """
    :root {
      --primary: #4caf50;
      --accent: #00e676;
      --bg-light: #1b5e20;
      --bg-dark: #000000;
      --text: #e8f5e9;
      --text-light: #c8e6c9;
      --border: #2e7d32;
      --tron-black: #000a12;
    }
    body {
        background: linear-gradient(135deg, #000000 0%, #1b5e20 100%);
    }
    .container {
        background: rgba(0, 20, 0, 0.8);
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
    <div style="background: linear-gradient(135deg, #1b5e20, #000000); color: var(--accent); padding: 24px; border-radius: 16px; margin-bottom: 32px; border: 1px solid var(--primary); box-shadow: 0 0 15px rgba(76, 175, 80, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em; text-shadow: 0 0 5px var(--primary);">
            地球をコードする：AlphaEarth Foundations
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6; color: var(--text);">
            Google DeepMindが放つ、地球観測の新たな基盤モデル。10m解像度・64次元の「Satellite Embedding」が、Earth Engineで今すぐ利用可能です。これは単なる地図ではなく、地球そのものを計算可能なデータ構造へと変換する試みです。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: rgba(0, 0, 0, 0.3); border: 1px solid var(--accent); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--accent); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🛰️</span>
            エンジニアのための3つの革新
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: black; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>即時実装</strong>: `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` をインポートするだけで、前処理なしに解析開始。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: black; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>高次元解析</strong>: 64次元ベクトルを用いた類似度検索や変化検出が、わずか数行のコードで実現。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: black; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>スケーラビリティ</strong>: Googleのインフラ上で、地球規模の解析をブラウザから実行可能。</span>
            </li>
        </ul>
    </div>
    """

    # Code Snippet Content
    code_snippet = """
    <div style="background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 16px; margin-bottom: 32px; font-family: 'Fira Code', monospace; overflow-x: auto;">
        <div style="color: #808080; margin-bottom: 8px;">// Earth Engine Code Editor Example</div>
        <div style="color: #d4d4d4;">
            <span style="color: #569cd6;">var</span> ds = ee.ImageCollection(<span style="color: #ce9178;">'GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL'</span>);<br><br>
            <span style="color: #6a9955;">// 年次変化をベクトルの内積で検出</span><br>
            <span style="color: #569cd6;">var</span> img2024 = ds.filterDate(<span style="color: #ce9178;">'2024-01-01'</span>, <span style="color: #ce9178;">'2025-01-01'</span>).first();<br>
            <span style="color: #569cd6;">var</span> img2023 = ds.filterDate(<span style="color: #ce9178;">'2023-01-01'</span>, <span style="color: #ce9178;">'2024-01-01'</span>).first();<br><br>
            <span style="color: #569cd6;">var</span> similarity = img2024.multiply(img2023).reduce(ee.Reducer.sum());<br>
            Map.addLayer(similarity, {min:0, max:1}, <span style="color: #ce9178;">'Similarity'</span>);
        </div>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">🌍</span>
            <div class="feature-title" style="color: var(--accent);">Virtual Satellite</div>
            <div class="feature-desc">雲や欠損のない、完全な地球のデジタルツイン基盤。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">💻</span>
            <div class="feature-title" style="color: var(--accent);">Analysis Ready</div>
            <div class="feature-desc">前処理の泥沼から解放。純粋な分析とインサイト発見に集中。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">⚡</span>
            <div class="feature-title" style="color: var(--accent);">Fast Action</div>
            <div class="feature-desc">立地選定から災害対応まで、意思決定のスピードを劇的に加速。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4 style="color: var(--accent);">ビジネスインパクト</h4>
        <p>サプライチェーンのリスク管理、ESG投資のための環境モニタリング、新規出店の立地分析。これらすべてが、AlphaEarth Foundationsによって「明日から」高精度化・効率化されます。専門家でなくとも、高度な地理空間分析の恩恵を受けられる時代の到来です。</p>
    </div>
    """

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="https://placehold.co/1200x600/000000/00e676?text=AlphaEarth+Foundations" alt="AlphaEarth Foundations Visual" onerror="this.src='https://placehold.co/1200x600/000000/00e676?text=AlphaEarth+Foundations'">
      </div>
      <section class="section">
        <div class="section-header" style="border-bottom-color: var(--accent);">
          <span class="section-icon">🌌</span>
          <h2 style="color: var(--text);">{short_title}</h2>
        </div>
        {intro_box}
        <h3 style="color: var(--text);">Quick Start Guide</h3>
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
    output_path = f"presentations/day_slides/day_slide_2025_07_30.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0730()
