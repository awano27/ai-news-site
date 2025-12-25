import re
from pathlib import Path
import json
import os

def create_slide_1225():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年12月25日"
    date_slash = "2025/12/25"
    
    # Define content variables
    short_title = "NVIDIA Checkmate" 
    main_title = "The $20 Billion Strategic Move"
    subtitle = "NVIDIA 200億ドルのチェックメイト：AIインフラの覇権"

    # CSS Variables for "NVIDIA Green" theme
    css_vars = """
    :root {
      --primary: #76b900;
      --accent: #b4d455;
      --bg-light: #f0f4e8;
      --bg-dark: #1a1a1a;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
      --border: #d4e0b5;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #76b900, #5d9200); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            AI時代の計算資源を掌握する
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            2025年のクリスマス、NVIDIAが発表した200億ドル規模の戦略的投資は、単なる資金投入ではなく、次世代AI計算資源の排他的確保とエコシステムの完全支配を意味します。この「チェックメイト」が市場に与える衝撃を分析します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">💡</span>
            戦略の3大要素
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>供給網の垂直統合</strong>: キーコンポーネントの製造ラインを長期独占契約。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>独自プロトコルの普及</strong>: インターコネクト技術の標準化による競合排除。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>次世代ソフトウェア層</strong>: CUDAを超えた自律型エージェント用OSの開発。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">💰</span>
            <div class="feature-title">圧倒的な資本力</div>
            <div class="feature-desc">12ヶ月で蓄積した巨額のキャッシュを戦略的に投下。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🏭</span>
            <div class="feature-title">生産能力の拡充</div>
            <div class="feature-desc">高度なパッケージング技術への直接投資。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🏗️</span>
            <div class="feature-title">DC規模の最適化</div>
            <div class="feature-desc">計算機単体ではなく、データセンター全体を一つの計算機に変革。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>なぜ「チェックメイト」なのか？</h4>
        <p>今回の投資により、競合他社が追随するために必要な物理的なリソース（最先端のファウンドリ資源や特殊冷却ソリューション）の大部分をNVIDIAが事実上封鎖したためです。他社は性能ではなく、まず「物理的に作れる場所」で苦慮することになります。</p>
    </div>

    <div class="card">
        <h4>2026年への展望</h4>
        <p>NVIDIAはハードウェアベンダーから「AIインフラのOSベンダー」へと完全に進化します。全てのAIエージェントがNVIDIAの提供する抽象化レイヤー上で動作する未来が、この投資によって確固たるものとなりました。</p>
    </div>
    """

    # Assemble Main Content (12 pages)
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/1225.jpg" alt="NVIDIA 200 Billion Visual" onerror="this.src='https://placehold.co/1200x600?text=1225+NVIDIA+Checkmate'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🔗</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>AIインフラの覇権争い</h3>
        {highlight_box}
        {feature_grid}
        {detail_cards}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全12ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/1225_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, 13)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🎓 12/25レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2025_12_25.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1225()
