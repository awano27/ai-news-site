import re
from pathlib import Path
import json

def create_slide_1211():
    # Load base_template.html
    try:
        with open("base_template.html", "r", encoding="utf-8") as f:
            template_html_content = f.read()
    except FileNotFoundError:
        print("Error: base_template.html not found.")
        return

    # Define date variables for 2025-12-11
    date_jp = "2025年12月11日"
    date_slash = "2025/12/11"
    
    # Define content variables from 1211.txt
    short_title = "Emergent & Google" 
    main_title = "AIの魔法？急成長スタートアップ「Emergent」とGoogleの関係"
    subtitle = "「vibe coding」が変えるソフトウェア開発の未来"

    # HTML Parts Construction
    
    # Intro Box
    intro_box = """
    <div style="background: linear-gradient(135deg, #1a0505, #8E0000); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            急成長スタートアップ「Emergent」の衝撃
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            サービス開始から数ヶ月で250万人以上のユーザーを獲得し、年間収益2,500万ドルに達した「Emergent」。
            言葉で伝えるだけでアプリが完成するその「魔法」の正体とは？
        </p>
    </div>
    """

    # Highlight Box (Emergentとは)
    highlight_box = """
    <div style="background: #fff5f5; border-left: 5px solid #D32F2F; padding: 20px; margin-bottom: 32px; border-radius: 4px;">
        <h3 style="color: #D32F2F; margin-bottom: 12px; font-size: 1.4rem;">魔法のコンセプト「vibe coding」</h3>
        <p style="line-height: 1.8; margin-bottom: 16px;">
            Emergentは<strong>「優秀なAIアシスタントに話しかけるだけで、本格的なアプリが完成する」</strong>ツールです。
            プログラミングの知識は不要。「こんな雰囲気で」「こんな感じで」というニュアンス（vibe）を伝えるだけで、
            AIが設計から開発、公開までを自動で行います。
        </p>
    </div>
    """

    # Feature Grid (3つのポイント)
    feature_grid = """
    <div class="card accent" style="background: white; border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <h4 style="margin-bottom: 20px; font-size: 1.2rem; color: var(--text);">Emergentが「他とは違う」3つのポイント</h4>
      
      <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <div class="feature-item" style="padding: 16px; background: var(--bg-light); border-radius: 12px;">
            <span class="feature-icon" style="font-size: 2rem; display: block; margin-bottom: 12px;">✨</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px;">プロ級の完成度</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5;">
                アイデアを思いついただけで、試作品止まりではなく、実際にビジネスで使える本格的なアプリが作れる。
            </div>
        </div>
        <div class="feature-item" style="padding: 16px; background: var(--bg-light); border-radius: 12px;">
            <span class="feature-icon" style="font-size: 2rem; display: block; margin-bottom: 12px;">⚡</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px;">準備一切不要</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5;">
                専門家がやるような難しい裏側の設定（バックエンドやデプロイ）を気にせず、アプリ作りに集中できる。
            </div>
        </div>
        <div class="feature-item" style="padding: 16px; background: var(--bg-light); border-radius: 12px;">
            <span class="feature-icon" style="font-size: 2rem; display: block; margin-bottom: 12px;">📱</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px;">スマホアプリも対応</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5;">
                Webサービスだけでなく、本格的なスマホアプリ（React Native製）も作成可能。
            </div>
        </div>
      </div>
    </div>
    """

    # Detail Card (Googleとの関係・未来)
    detail_card = """
    <div class="card" style="background: white; border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <h3 style="margin-bottom: 16px; color: var(--text);">Googleとの物語と未来への展望</h3>
        
        <div style="margin-bottom: 24px;">
            <h4 style="color: #D32F2F; margin-bottom: 8px;">創業者と巨人の円環</h4>
            <p style="line-height: 1.7; margin-bottom: 12px;">
                創業者のMukund Jha氏は、2005年に「Googleで働きたい」という夢を抱き、実際にGoogleでキャリアを積みました。
                時を経て、今度は彼が立ち上げたEmergentにGoogleが投資するという、夢が循環するような展開を迎えました。
            </p>
        </div>

        <div style="margin-bottom: 24px;">
            <h4 style="color: #D32F2F; margin-bottom: 8px;">Googleの狙い</h4>
            <ul style="list-style-type: disc; padding-left: 20px; line-height: 1.7;">
                <li><strong>技術の民主化:</strong> 誰もがクリエイターになれる世界の実現。</li>
                <li><strong>未来の「創作の入口」:</strong> アイデアを製品にする最初の入口を押さえる戦略。</li>
                <li><strong>インド市場への期待:</strong> インドを次世代AIの重要市場と位置づけ。</li>
            </ul>
        </div>

        <div>
            <h4 style="color: #D32F2F; margin-bottom: 8px;">これからの世界</h4>
            <p style="line-height: 1.7;">
                プログラミング経験がなくても誰もが「発明家」になれる可能性と、AI生成アプリの信頼性やベンダーロックインといった課題。
                「vibe coding」はソフトウェア開発のあり方を根本から変えようとしています。
            </p>
        </div>
    </div>
    """
    
    # 配色設定
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
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 -->')
    content_parts.append('  <div class="top-image-container">')
    
    # Image tag construction
    img_tag_parts = []
    img_tag_parts.append('<img src="../../input/day/1211.png" ')
    img_tag_parts.append('alt="Emergent and Google Visual" style="width: 100%; max-width: 800px; border-radius: 12px; display: block; margin: 0 auto 32px auto;">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">✨</span>')
    content_parts.append(f'      <h2>{main_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>Emergentの特徴</h3>')
    content_parts.append(highlight_box)
    content_parts.append(feature_grid)
    content_parts.append(detail_card)
    content_parts.append('  </section>')

    content_parts.append('  <!-- スライド資料 (全ページ) -->')
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">📖</span>')
    content_parts.append('      <h2>レポート全文 (PDF)</h2>')
    content_parts.append('    </div>')
    
    content_parts.append('    <div class="download-link" style="text-align: center; margin-bottom: 24px;">')
    
    # PDF link construction
    pdf_link_parts = []
    pdf_link_parts.append('<a href="../../input/day/1211-Agentic_AI_The_New_Software_Stack.pdf" target="_blank" ')
    pdf_link_parts.append('style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); ')
    pdf_link_parts.append('padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); ')
    pdf_link_parts.append('text-decoration: none; color: var(--text); transition: all 0.2s ease;">')
    content_parts.append('        ' + "".join(pdf_link_parts))
    
    content_parts.append('            <span style="font-size: 1.2rem;">📄</span>')
    content_parts.append('            <span>レポート全文をダウンロード (PDF)</span>')
    content_parts.append('        </a>')
    content_parts.append('    </div>')
    
    # Slides construction
    slides_list = []
    for i in range(1, 16):
        slides_list.append(f'<img src="../../input/day/1211_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)

    content_parts.append('    <div class="slides-container">')
    content_parts.append('        <!-- Slide Images -->')
    content_parts.append(slides_html)
    content_parts.append('    </div>')
    
    content_parts.append('    <style>')
    content_parts.append('        .slide-img {')
    content_parts.append('            width: 100%;')
    content_parts.append('            max-width: 1000px;')
    content_parts.append('            height: auto;')
    content_parts.append('            border-radius: 12px;')
    content_parts.append('            box-shadow: 0 4px 20px rgba(0,0,0,0.15);')
    content_parts.append('            border: 1px solid var(--border);')
    content_parts.append('            transition: transform 0.3s ease;')
    content_parts.append('        }')
    content_parts.append('        .slide-img:hover {')
    content_parts.append('            transform: scale(1.01);')
    content_parts.append('            box-shadow: 0 8px 30px rgba(0,0,0,0.2);')
    content_parts.append('        }')
    content_parts.append('        .slides-container {')
    content_parts.append('            display: flex;')
    content_parts.append('            flex-direction: column;')
    content_parts.append('            align-items: center;')
    content_parts.append('            gap: 24px;')
    content_parts.append('            width: 100%;')
    content_parts.append('        }')
    content_parts.append('    </style>')
    
    content_parts.append('  </section>')
    content_parts.append('</main>')

    main_content_html = "\n".join(content_parts)

    # プレースホルダーを置換
    html = template_html_content.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    html = html.replace("{{CSS_VARS_BLOCK}}", css_vars_block)
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}レポート | スタートアップ")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_11.html"
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1211()
