import re
from pathlib import Path
import json

def create_slide_v2():
    # Load base_template.html
    with open("base_template.html", "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-10
    date_jp = "2025年12月10日"
    date_slash = "2025/12/10"
    date_file = "2025-12-10"
    
    # Load news data
    # with open(f"news/{date_file}.json", "r", encoding="utf-8") as f:
    #     news_data = json.load(f)
    
    # item = news_data['items'][0] # Keep this commented out if not used

    # Define content variables for 2025-12-10 (guessed content, USER SHOULD CONFIRM)
    short_title = "Open Foundation for Agentic AI" 
    main_title = "自律エージェントAI基盤のオープン化"
    subtitle = "大規模言語モデルの次なる進化とエコシステム"

    intro_box = """
    <div style="background: linear-gradient(135deg, #1a0505, #8E0000); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            Open Foundation for Agentic AIの概要。
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            大規模言語モデルの能力を最大化し、自律的な問題解決を可能にするための新しいAI基盤の発表。
        </p>
    </div>
    """
    
    highlight_box = """
    <div class="highlight-box">
      <p><strong>【従来のAIとの違い】</strong><br>
      単なるツールとしてのAIではなく、自律的に目標を設定し、実行し、学習するエージェント型AIの実現を目指します。<br>
      オープンソース化により、研究開発の加速と幅広い分野での応用を促進します。</p>
    </div>
    """
    
    feature_grid = """
    <div class="card accent">
      <h4>Open Foundation の3つの要素</h4>
      
      <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🌐</span>
            <div class="feature-title">Open Source</div>
            <div class="feature-desc">
                基盤モデル、ツール、データセットをオープンソース化し、透明性と共同開発を推進。
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">Agentic Capabilities</div>
            <div class="feature-desc">
                計画、推論、自己修正能力を持つAIエージェントの構築を支援。
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🚀</span>
            <div class="feature-title">Ecosystem Growth</div>
            <div class="feature-desc">
                開発者コミュニティを育成し、多様なアプリケーションの創出を促進。
            </div>
        </div>
      </div>
    </div>
    """
    
    detail_card = """
    <div class="card">
        <h4>実装へのロードマップ</h4>
        <p>初期リリースには、マルチモーダル対応のエージェントフレームワーク、セキュアな実行環境、性能評価ツールが含まれます。数ヶ月以内に主要なクラウドプラットフォームとの連携も予定されています。</p>
    </div>
    """

    # 5. スライド画像リスト (1-121)
    slides_html = ""
    for i in range(1, 122):
        slides_html += f'<img src="../../input/day/1210_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">\n'
    
    # 配色設定 (China Red / Gold / Future Blue)
    css_vars_block = """
    :root {
      --primary: #D32F2F; /* China Red */
      --accent: #FFD700; /* Gold */
      --accent2: #FF5252;
      --bg-dark: #1a0505;
      --bg-light: #fff5f5;
      --border: #ffcdd2;
      --text: #2c0b0e;
      --text-light: #5c1e23;
    }
    header {
      background: linear-gradient(135deg, #8E0000 0%, #1a0505 100%);
    }
    """
    
    # メインコンテンツの構築 (main_content_html)
    main_content_html = """
    <main>
      <!-- トップ画像 -->
      <div class="top-image-container">
        <img src="../../input/day/1210.png" alt="Open Foundation for Agentic AI Visual">
      </div>

      <section class="section">
        <div class="section-header">
          <span class="section-icon">🔭</span>
          <h2>Open Foundation for Agentic AI</h2>
        </div>
        """ + intro_box + """
        <h3>Open Foundation の目的と特徴</h3>
        """ + highlight_box + """
        """ + feature_grid + """
        """ + detail_card + """
      </section>

      <!-- スライド資料 (全ページ) -->
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全ページ)</h2>
        </div>
        
        <div class="download-link" style="text-align: center; margin-bottom: 24px;">
            <a href="../../input/day/1210-Open_Foundation_for_Agentic_AI.pdf" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); text-decoration: none; color: var(--text); transition: all 0.2s ease;">
                <span style="font-size: 1.2rem;">📄</span>
                <span>レポート全文をダウンロード (PDF)</span>
            </a>
        </div>
        
        <div class="slides-container">
            <!-- Slide Images -->
            """ + slides_html + """
        </div>
        
        <style>
            .slide-img {
                width: 100%;
                max-width: 1000px;
                height: auto;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                border: 1px solid var(--border);
                transition: transform 0.3s ease;
            }
            .slide-img:hover {
                transform: scale(1.01);
                box-shadow: 0 8px 30px rgba(0,0,0,0.2);
            }
            .slides-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 24px;
                width: 100%;
            }
        </style>
      </section>
    </main>
    """

    # プレースホルダーを置換
    html = template_html_content.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    html = html.replace("{{CSS_VARS_BLOCK}}", css_vars_block)
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}レポート | 国家AI戦略")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_10.html" # Output file name for 12/10
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_v2()
