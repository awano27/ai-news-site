import re
from pathlib import Path
import json

def create_slide_v2():
    # テンプレート（12/08の内容）を読み込む
    with open("presentations/day_slides/day_slide_2025_12_08.html", "r", encoding="utf-8") as f:
        template = f.read()

    # 入力データ（12/09）
    date_jp = "2025年12月9日"
    date_slash = "2025/12/09"
    date_file = "2025-12-09"
    
    # JSONデータの読み込み（タイトル等の取得）
    with open(f"news/{date_file}.json", "r", encoding="utf-8") as f:
        news_data = json.load(f)
    
    # item = news_data['items'][0]
    
    # タイトル加工
    short_title = "China Tech Vision 2049"
    main_title = "中国 Vision 2049: AI × BCI国家戦略"
    subtitle = "ASI（人工超知能）と脳–機械インターフェースの完全融合"
    
    # 配色設定 (China Red / Gold / Future Blue)
    css_vars = """
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
    
    # コンテンツの生成
    intro_box = """
    <div style="background: linear-gradient(135deg, #1a0505, #8E0000); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            中国が描く2049年の未来像「Vision 1」は、欧米のAGI論とは一線を画します。
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            国家主導のタイムライン、脳–機械インターフェース（BCI）のインフラ化、そして人間拡張（Augmentation）。「社会主義的近代化の完成形」としてのAI戦略の全貌が明らかになりました。
        </p>
    </div>
    """
    
    highlight_box = """
    <div class="highlight-box">
      <p><strong>【従来のAI戦略との決定的な違い】</strong><br>
      Big Tech主導の欧米型モデルに対し、中国は<strong>「国家安全保障」と「社会実装」</strong>を最優先。<br>
      単なる知能の自動化ではなく、BCIを通じてAIを人間の脳に直接接続し、認知能力を物理的に拡張する「トランスヒューマン的アプローチ」を国家規模で推進しています。</p>
    </div>
    """
    
    feature_grid = """
    <div class="card accent">
      <h4>Vision 2049 の3つの柱</h4>
      
      <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🇨🇳</span>
            <div class="feature-title">State Driven</div>
            <div class="feature-desc">
                建国100周年(2049年)に向けた政治的マイルストーン。民間任せではなく、国家が「自主可控」な技術体系を整備。
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">BCI Infrastructure</div>
            <div class="feature-desc">
                脳–機械インターフェースを次世代インフラと定義。思考を直接デジタル空間へ送る「シームレスな融合」を目指す。
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🚀</span>
            <div class="feature-title">Human Augmentation</div>
            <div class="feature-desc">
                AIによる「人間の置き換え」ではなく「能力拡張」。ASI（超知能）を脳の延長として活用する独自のアプローチ。
            </div>
        </div>
      </div>
    </div>
    """
    
    detail_card = """
    <div class="card">
        <h4>実装へのロードマップ</h4>
        <p>2027年までにBCIの「重要技術ブレイクスルー」を達成するという産業指針が既に公表されています。半侵襲型ワイヤレス脳チップ「Beinao No.1」の臨床試験など、ビジョンは既に実験段階から実装段階へと移行しつつあります。</p>
    </div>
    """

    # 5. スライド画像リスト (1-15)
    slides_html = ""
    for i in range(1, 16):
        slides_html += f'<img src="../../input/day/1209_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">\n'
    
    # テンプレート（base_template.html）を読み込む
    with open("base_template.html", "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # 入力データ（12/09）
    date_jp = "2025年12月9日"
    date_slash = "2025/12/09"
    date_file = "2025-12-09"
    
    # JSONデータの読み込み（タイトル等の取得）
    with open(f"news/{date_file}.json", "r", encoding="utf-8") as f:
        news_data = json.load(f)
    
    # item = news_data['items'][0]
    
    # タイトル加工
    short_title = "China Tech Vision 2049"
    main_title = "中国 Vision 2049: AI × BCI国家戦略"
    subtitle = "ASI（人工超知能）と脳–機械インターフェースの完全融合"
    
    intro_box = """
    <div style="background: linear-gradient(135deg, #1a0505, #8E0000); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            中国が描く2049年の未来像「Vision 1」は、欧米のAGI論とは一線を画します。
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            国家主導のタイムライン、脳–機械インターフェース（BCI）のインフラ化、そして人間拡張（Augmentation）。「社会主義的近代化の完成形」としてのAI戦略の全貌が明らかになりました。
        </p>
    </div>
    """
    
    highlight_box = """
    <div class="highlight-box">
      <p><strong>【従来のAI戦略との決定的な違い】</strong><br>
      Big Tech主導の欧米型モデルに対し、中国は<strong>「国家安全保障」と「社会実装」</strong>を最優先。<br>
      単なる知能の自動化ではなく、BCIを通じてAIを人間の脳に直接接続し、認知能力を物理的に拡張する「トランスヒューマン的アプローチ」を国家規模で推進しています。</p>
    </div>
    """
    
    feature_grid = """
    <div class="card accent">
      <h4>Vision 2049 の3つの柱</h4>
      
      <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🇨🇳</span>
            <div class="feature-title">State Driven</div>
            <div class="feature-desc">
                建国100周年(2049年)に向けた政治的マイルストーン。民間任せではなく、国家が「自主可控」な技術体系を整備。
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">BCI Infrastructure</div>
            <div class="feature-desc">
                脳–機械インターフェースを次世代インフラと定義。思考を直接デジタル空間へ送る「シームレスな融合」を目指す。
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🚀</span>
            <div class="feature-title">Human Augmentation</div>
            <div class="feature-desc">
                AIによる「人間の置き換え」ではなく「能力拡張」。ASI（超知能）を脳の延長として活用する独自のアプローチ。
            </div>
        </div>
      </div>
    </div>
    """
    
    detail_card = """
    <div class="card">
        <h4>実装へのロードマップ</h4>
        <p>2027年までにBCIの「重要技術ブレイクスルー」を達成するという産業指針が既に公表されています。半侵襲型ワイヤレス脳チップ「Beinao No.1」の臨床試験など、ビジョンは既に実験段階から実装段階へと移行しつつあります。</p>
    </div>
    """

    # 5. スライド画像リスト (1-15)
    slides_html = ""
    for i in range(1, 16):
        slides_html += f'<img src="../../input/day/1209_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">\n'
    
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
    
    # メインコンテンツの構築 (full_main_contentに全てを統合)
    main_content_html = f"""
    <main>
      <!-- トップ画像 -->
      <div class="top-image-container">
        <img src="../../input/day/1209.png" alt="China Vision 2049 Visual">
      </div>

      <section class="section">
        <div class="section-header">
          <span class="section-icon">🔭</span>
          <h2>Vision 2049: AIと人類の融合</h2>
        </div>
        {intro_box}
        <h3>独自のシンギュラリティ観</h3>
        {highlight_box}
        {feature_grid}
        {detail_card}
      </section>

      <!-- スライド資料 (全ページ) -->
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全ページ)</h2>
        </div>
        
        <div class="download-link" style="text-align: center; margin-bottom: 24px;">
            <a href="../../input/day/1209-China_ASI_BCI_2049_Strategy.pdf" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); text-decoration: none; color: var(--text); transition: all 0.2s ease;">
                <span style="font-size: 1.2rem;">📄</span>
                <span>レポート全文をダウンロード (PDF)</span>
            </a>
        </div>
        
        <div class="slides-container">
            <!-- Slide Images -->
            {slides_html}
        </div>
        
        <style>
            .slide-img {{
                width: 100%;
                max-width: 1000px;
                height: auto;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                border: 1px solid var(--border);
                transition: transform 0.3s ease;
            }}
            .slide-img:hover {{
                transform: scale(1.01);
                box-shadow: 0 8px 30px rgba(0,0,0,0.2);
            }}
            .slides-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 24px;
                width: 100%;
            }}
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
    output_path = "presentations/day_slides/day_slide_2025_12_09.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_v2()