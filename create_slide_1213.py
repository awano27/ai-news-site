import re
from pathlib import Path
import json

def create_slide_1213():
    # Load base_template.html
    try:
        with open("base_template.html", "r", encoding="utf-8") as f:
            template_html_content = f.read()
    except FileNotFoundError:
        print("Error: base_template.html not found.")
        return

    # Define date variables for 2025-12-13
    date_jp = "2025年12月13日"
    date_slash = "2025/12/13"
    
    # Define content variables from 1213.txt
    short_title = "Cursor Visual Editor" 
    main_title = "Cursor Visual Editorが描く未来：デザインとコードの壁が溶ける日"
    subtitle = "ドラッグ＆ドロップで実装を直接操作。もう「行ったり来たり」は不要に。"

    # HTML Parts Construction
    
    # Intro Box
    intro_box = """
    <div style=\"background: linear-gradient(135deg, #1e1e2e, #3b3b4f); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);\">
        <p style=\"font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;\">
            もう、デザインとコードで迷わない
        </p>
        <p style=\"font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;\">
            「エディタで書いて、ブラウザで確認して、微調整して...」そんな非効率なループは終わります。
            Cursor Visual Editorは、目の前のWebサイトを直接操作し、裏側でAIにコードを書かせる、全く新しい開発体験への招待状です。
        </p>
    </div>
    """

    # Highlight Box (3つの魔法)
    highlight_box = """
    <div class="highlight-box" style="background-color: #f3f4f6; border-left: 5px solid #6366f1; padding: 24px; margin-bottom: 32px; border-radius: 8px;">
      <h3 style="color: #4f46e5; margin-top: 0; margin-bottom: 12px; display: flex; align-items: center; font-size: 1.4rem;">
         <span style="font-size: 1.8rem; margin-right: 10px;">✨</span>
         体験を変える3つの魔法
      </h3>
      <ul style="font-size: 1.1rem; line-height: 1.8; color: #1f2937; list-style: none; padding: 0;">
        <li style="margin-bottom: 12px;"><strong>✋ 見て、動かす (Drag & Drop)：</strong> ボタンやセクションをマウスで掴んで移動。パワポ感覚でレイアウト変更が可能。</li>
        <li style="margin-bottom: 12px;"><strong>🎨 触って、仕上げる (Visual Control)：</strong> Figmaのようなパネルで余白や色を調整。繊細な感覚をそのまま反映。</li>
        <li><strong>🗣️ 指さして、話す (Point & Prompt)：</strong> 要素をクリックして「これを赤にして」と言うだけ。AIが裏でコードを書き換え。</li>
      </ul>
    </div>
    """

    # Feature Grid (働き方の変化)
    feature_grid = """
    <div class="card accent" style="background: white; border: 1px solid var(--border); border-top: 4px solid var(--primary); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <h4 style="margin-bottom: 20px; font-size: 1.3rem; color: var(--text); border-bottom: 1px solid var(--border); padding-bottom: 10px;">働き方はどう変わる？</h4>
      
      <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">🤝</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">役割の融合</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                デザイナーが実装を直接いじり、エンジニアが瞬時にプロトタイプを作る。「デザインエンジニア」の時代へ。
            </div>
        </div>
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">🧠</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">思考のシフト</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                仕事は「タイピング」から「AIの指揮(Directing)」へ。人間はより高度な設計やアイデア創出に集中。
            </div>
        </div>
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">🚀</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">スピード革命</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                「コンテキストの切り替え」による中断が消滅。思考が一直線にゴールへ向かうフロー状態を実現。
            </div>
        </div>
      </div>
    </div>
    """

    # Detail Card (Figma vs Cursor)
    detail_card = """
    <div class="card" style="background: white; border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <h3 style="margin-bottom: 20px; color: var(--text); display: flex; align-items: center;">
            <span style="width: 6px; height: 24px; background: var(--primary); margin-right: 10px; border-radius: 3px;"></span>
            Q. Figmaはもう要らない？
        </h3>
        
        <p style="margin-bottom: 20px; line-height: 1.7;">
            結論：「役割が違う」。現時点では、以下のように使い分けるのが最適解です。
        </p>

        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 1rem; min-width: 500px;">
                <thead>
                    <tr style="background: #f3f4f6; border-bottom: 2px solid #e5e7eb;">
                        <th style="padding: 12px; text-align: left; color: #4b5563; width: 30%;">ツール</th>
                        <th style="padding: 12px; text-align: left; color: #4b5563; width: 70%;">役割と目的</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 12px; font-weight: bold; color: #f24e1e;">Figma</td>
                        <td style="padding: 12px; color: #1f2937;">
                            <strong>「自由なキャンバス」</strong><br>
                            0→1のデザイン案出し。制約のない状態でアイデアを探る場所。
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold; color: #6366f1;">Cursor</td>
                        <td style="padding: 12px; color: #1f2937;">
                            <strong>「精密な手術台」</strong><br>
                            実装後の微調整。本物のコードをベースに完璧に磨き上げる場所。
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """
    
    # 配色設定 (Cursor Purple/Blue Theme)
    css_vars_block = """
    :root {
      --primary: #6366f1; /* Indigo */
      --accent: #1e1e2e; /* Dark Cursor-like bg */
      --accent2: #a5b4fc; /* Light Indigo */
      --bg-dark: #1e1e2e;
      --bg-light: #f8fafc;
      --border: #e2e8f0;
      --text: #1f2937;
      --text-light: #6b7280;
    }
    header {
      background: linear-gradient(135deg, #1e1e2e 0%, #4338ca 100%);
    }
    .breaking-badge {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
    }
    .subtitle {
        color: #e0e7ff;
    }
    """
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 -->')
    content_parts.append('  <div class="top-image-container">')
    
    # Image tag construction
    img_tag_parts = []
    img_tag_parts.append('<img src="../../input/day/1213.jpg" ')
    img_tag_parts.append('alt="Cursor Visual Editor" style="width: 100%; max-width: 800px; border-radius: 12px; display: block; margin: 0 auto 32px auto;">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🖱️</span>')
    content_parts.append(f'      <h2>{main_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
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
    pdf_link_parts.append('<a href="../../input/day/1213-Code_Transformation_Cost.pdf" target="_blank" ')
    pdf_link_parts.append('style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); ')
    pdf_link_parts.append('padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); ')
    pdf_link_parts.append('text-decoration: none; color: var(--text); transition: all 0.2s ease;">')
    content_parts.append('        ' + "".join(pdf_link_parts))
    
    content_parts.append('            <span style="font-size: 1.2rem;">📄</span>')
    content_parts.append('            <span>レポート全文をダウンロード (PDF)</span>')
    content_parts.append('        </a>')
    content_parts.append('    </div>')
    
    # Slides construction (12 pages)
    slides_list = []
    for i in range(1, 13):
        slides_list.append(f'<img src="../../input/day/1213_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)

    content_parts.append('    <div class="slides-container">')
    content_parts.append('        <!-- Slide Images -->')
    content_parts.append('        ' + slides_html)
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
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"⚡ {date_jp}レポート | Cursor Visual Editor")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_13.html"
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1213()
