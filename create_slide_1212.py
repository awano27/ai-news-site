import re
from pathlib import Path
import json

def create_slide_1212():
    # Load base_template.html
    try:
        with open("base_template.html", "r", encoding="utf-8") as f:
            template_html_content = f.read()
    except FileNotFoundError:
        print("Error: base_template.html not found.")
        return

    # Define date variables for 2025-12-12
    date_jp = "2025年12月12日"
    date_slash = "2025/12/12"
    
    # Define content variables from 1212.txt
    short_title = "GPT-5.2 解説" 
    main_title = "OpenAI最新モデル「GPT-5.2」徹底解説"
    subtitle = "専門家レベルのAIパートナーの登場：何が変わり、何が可能になったのか"

    # HTML Parts Construction
    
    # Intro Box
    intro_box = """
    <div style=\"background: linear-gradient(135deg, #000000, #10a37f); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);\">
        <p style=\"font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;\">
            AIは「ツール」から「パートナー」へ
        </p>
        <p style=\"font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;\">
            2025年12月11日発表の「GPT-5.2」は、単なる性能向上モデルではありません。
            実務能力を測る新指標「GDPval」で史上初めて人間の専門家レベルに到達し、
            ビジネスの現場におけるAIの役割を根本から変えようとしています。
        </p>
    </div>
    """

    # Highlight Box (GDPval)
    highlight_box = """
    <div class="highlight-box" style="background-color: #f0fdf4; border-left: 5px solid #10a37f; padding: 24px; margin-bottom: 32px; border-radius: 8px;">
      <h3 style="color: #0d8a6a; margin-top: 0; margin-bottom: 12px; display: flex; align-items: center; font-size: 1.4rem;">
         <span style="font-size: 1.8rem; margin-right: 10px;">📈</span>
         衝撃の新指標「GDPval」
      </h3>
      <p style="font-size: 1.1rem; line-height: 1.8; color: #202123;">
        実際の経済活動に貢献する専門的タスク遂行能力において、GPT-5.2は勝率<strong>70.9%</strong>を記録。
        これはAI史上初めて、広範な知識労働タスクにおいて<strong>「人間の専門家レベル」</strong>に到達したことを意味します。
        しかも、人間の11倍以上の速度、1/100未満のコストで実行可能です。
      </p>
    </div>
    """

    # Feature Grid (3つの進化点)
    feature_grid = """
    <div class="card accent" style="background: white; border: 1px solid var(--border); border-top: 4px solid var(--primary); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <h4 style="margin-bottom: 20px; font-size: 1.3rem; color: var(--text); border-bottom: 1px solid var(--border); padding-bottom: 10px;">GPT-5.2の核心的な3つの進化</h4>
      
      <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">🛡️</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">信頼性の飛躍</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                幻覚（ハルシネーション）を30%削減。金融や法務など、正確性が求められる分野での実務利用が現実に。
            </div>
        </div>
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">📚</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">圧倒的な長文処理</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                256kトークンでほぼ100%の精度を達成。書籍一冊分のレポートや複雑な契約書も一括で正確に解析。
            </div>
        </div>
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">💻</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">最強のコーディング</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                SWE-Benchで80%の新記録。バグ修正からリファクタリングまで、自律的な開発パートナーとして機能。
            </div>
        </div>
      </div>
    </div>
    """

    # Detail Card (Gemini比較)
    detail_card = """
    <div class="card" style="background: white; border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <h3 style="margin-bottom: 20px; color: var(--text); display: flex; align-items: center;">
            <span style="width: 6px; height: 24px; background: var(--primary); margin-right: 10px; border-radius: 3px;"></span>
            競合モデルとの使い分け
        </h3>
        
        <p style="margin-bottom: 20px; line-height: 1.7;">
            最大のライバルであるGoogleの<strong>Gemini 3 Pro</strong>とは設計思想が異なります。
            目的や利用シーンに応じて最適なモデルを選択することが、生産性最大化の鍵となります。
        </p>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div style="background: #f0fdf4; padding: 16px; border-radius: 8px; border: 1px solid #bbf7d0;">
                <h4 style="color: #15803d; margin-bottom: 10px; border-bottom: 1px solid #bbf7d0; padding-bottom: 5px;">OpenAI GPT-5.2</h4>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin-bottom: 8px;">✅ <strong>会話の自然さ・創造性</strong></li>
                    <li style="margin-bottom: 8px;">✅ <strong>インタラクティブな応答速度</strong></li>
                    <li style="margin-bottom: 8px;">✅ <strong>プラグイン・API連携の柔軟さ</strong></li>
                    <li style="font-size: 0.9rem; color: #166534;">👉 アイデア創出、コーディング支援、対話型学習に最適</li>
                </ul>
            </div>
            <div style="background: #eff6ff; padding: 16px; border-radius: 8px; border: 1px solid #bfdbfe;">
                <h4 style="color: #1d4ed8; margin-bottom: 10px; border-bottom: 1px solid #bfdbfe; padding-bottom: 5px;">Google Gemini 3 Pro</h4>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin-bottom: 8px;">✅ <strong>情報統合力・正確性</strong></li>
                    <li style="margin-bottom: 8px;">✅ <strong>超長文処理 (100万トークン~)</strong></li>
                    <li style="margin-bottom: 8px;">✅ <strong>Googleエコシステム連携</strong></li>
                    <li style="font-size: 0.9rem; color: #1e40af;">👉 技術文書作成、大規模データ分析、リサーチに最適</li>
                </ul>
            </div>
        </div>
    </div>
    """
    
    # 配色設定 (OpenAI Green Theme)
    css_vars_block = """
    :root {
      --primary: #10a37f; /* OpenAI Green */
      --accent: #202123; /* Dark Background */
      --accent2: #55efc4; /* Lighter Green */
      --bg-dark: #202123;
      --bg-light: #f9f9f9;
      --border: #e5e5e5;
      --text: #202123;
      --text-light: #6e6e80;
    }
    header {
      background: linear-gradient(135deg, #000000 0%, #10a37f 100%);
    }
    .breaking-badge {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
    }
    .subtitle {
        color: #e2e8f0;
    }
    """
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 -->')
    content_parts.append('  <div class="top-image-container">')
    
    # Image tag construction
    img_tag_parts = []
    img_tag_parts.append('<img src="../../input/day/1212.jpg" ') # Escaped quote here
    img_tag_parts.append('alt="GPT-5.2 Visual" style="width: 100%; max-width: 800px; border-radius: 12px; display: block; margin: 0 auto 32px auto;">') # Escaped quote here
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🤖</span>')
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
    pdf_link_parts.append('<a href="../../input/day/1212-GPT-52_The_Human_Expert_AI.pdf" target="_blank" ') # Escaped quotes here
    pdf_link_parts.append('style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); ') # Escaped quote here
    pdf_link_parts.append('padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); ') # Escaped quote here
    pdf_link_parts.append('text-decoration: none; color: var(--text); transition: all 0.2s ease;">') # Escaped quote here
    content_parts.append('        ' + "".join(pdf_link_parts))
    
    content_parts.append('            <span style="font-size: 1.2rem;">📄</span>') # Escaped quote here
    content_parts.append('            <span>レポート全文をダウンロード (PDF)</span>')
    content_parts.append('        </a>')
    content_parts.append('    </div>')
    
    # Slides construction (13 pages)
    slides_list = []
    for i in range(1, 14):
        slides_list.append(f'<img src="../../input/day/1212_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">') # Escaped quotes here
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
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}レポート | OpenAI GPT-5.2")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_12.html" # Escaped quote here
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1212()
