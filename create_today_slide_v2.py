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
    
    # 置換実行
    html = template
    
    # CSS変数の置換 (TRON設定を削除し、新しい設定を挿入)
    html = re.sub(r':root \{.*?\}(?=\s*\*)', css_vars, html, flags=re.DOTALL)
    html = re.sub(r'header \{.*?background:.*?;', 'header {\n      background: linear-gradient(135deg, #8E0000 0%, #1a0505 100%);', html, flags=re.DOTALL)
    
    # ヘッダー情報の置換
    html = html.replace("TRON GenAI CODEアシスタント: 組み込みAI開発の新時代", f"{short_title}: {main_title}") # Title tag
    html = html.replace("🤖 2025年12月8日レポート | 組み込みAI開発", f"🌏 2025年12月9日レポート | 国家AI戦略")
    html = html.replace("TRON GenAI CODEアシスタント", main_title)
    html = html.replace("組み込みシステム開発に特化した生成AIアシスタントが登場", subtitle)
    html = html.replace("2025年12月8日", date_jp)
    
    # 画像パスの置換
    html = html.replace("../../input/day/1208.png", "../../input/day/1209.png")
    html = html.replace('alt="TRON GenAI CODE Assistant Visual"', 'alt="China Vision 2049 Visual"')
    
    # コンテンツセクションの置換
    section_content_regex = r'(<section class="section">\s*<div class="section-header">.*?<h2>.*?</h2>\s*</div>)(.*?)(</section>)'
    
    new_section_content = f"""
        <div class="section-header">
          <span class="section-icon">🔭</span>
          <h2>Vision 2049: AIと人類の融合</h2>
        </div>
        {intro_box}
        <h3>独自のシンギュラリティ観</h3>
        {highlight_box}
        {feature_grid}
        {detail_card}
    """
    
    # 最初のセクションを置換 (TRONの内容が入っている部分)
    html = re.sub(section_content_regex, f'\1\n{new_section_content}\n\3', html, count=1, flags=re.DOTALL)

    # PDFダウンロードリンクの置換
    html = html.replace("../../input/day/1208-TRON_GenAI_The_Embedded_Coding_Revolution.pdf", "../../input/day/1209-China_ASI_BCI_2049_Strategy.pdf")
    
    # スライド画像の置換
    slides_container_regex = r'(<div class="slides-container">)(.*?)(</div>)'
    html = re.sub(slides_container_regex, f'\1\n{slides_html}\3', html, flags=re.DOTALL)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_09.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_v2()