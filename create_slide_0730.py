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

    # CSS Variables for "Earth Green" theme
    css_vars = """
    :root {
      --primary: #2e7d32;
      --accent: #66bb6a;
      --bg-light: #e8f5e9;
      --bg-dark: #1b5e20;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
      --border: #c8e6c9;
      --tron-black: #000a12;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #2e7d32, #1b5e20); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            地球観測の新たな基盤モデル
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            Google DeepMindは、地球観測データを統合し、地球全体を高精度に表現する「AlphaEarth Foundations」を発表しました。Google Earth Engineで即座に利用可能な「Satellite Embedding」データセットも公開され、環境監視やビジネスへの応用が期待されます。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🚀</span>
            3つの主要ポイント
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>AlphaEarth Foundations公開</strong>: 地球全体を高精度に表現する埋め込みモデル。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>即利用可能なデータセット</strong>: Earth Engineで10m解像度・64次元のSatellite Embeddingが利用可能。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>広範な応用可能性</strong>: 立地選定、災害監視、ESGレポートなど、ビジネスと環境保護の両面で活用。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🌍</span>
            <div class="feature-title">Earth Engine連携</div>
            <div class="feature-desc">Google Earth Engineで直接呼び出し可能。前処理不要で即座に分析開始。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔍</span>
            <div class="feature-title">高精度分析</div>
            <div class="feature-desc">類似検索、変化検出、分類などをコード数十行で実装可能。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📉</span>
            <div class="feature-title">コスト削減</div>
            <div class="feature-desc">少ない教師データで迅速にモデル構築が可能。工数とコストを大幅に削減。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>エンジニア向け情報</h4>
        <p>データID: `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`。10m解像度、64次元。2017年以降の年次データが利用可能です。公式チュートリアルも充実しており、Similarity SearchやChange Detectionをすぐに試せます。</p>
    </div>

    <div class="card">
        <h4>ビジネスへのインパクト</h4>
        <p>森林伐採の監視、都市拡張の把握、再エネ適地選定など、地理空間情報を活用した意思決定を加速させます。個人を特定しない地表特徴に限定されているため、リスク説明も容易です。</p>
    </div>
    """

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="https://placehold.co/1200x600?text=AlphaEarth+Foundations" alt="AlphaEarth Foundations Visual" onerror="this.src='https://placehold.co/1200x600?text=AlphaEarth+Foundations'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🛰️</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>ニュースの要点</h3>
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
