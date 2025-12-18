import re
from pathlib import Path
import json

def create_slide_1218():
    # Load base_template.html
    with open("base_template.html", "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-18
    date_jp = "2025年12月18日"
    date_slash = "2025/12/18"
    date_file = "2025-12-18"
    
    # Define content variables
    short_title = "Gemini 3 Flash" 
    main_title = "Google、知能と速度を両立した「Gemini 3 Flash」を提供開始"
    subtitle = "Proクラスの知能をFlashの速度とコストで：AIエージェント時代の新基準モデル"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #1a73e8, #4285f4); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            Gemini 3 Flashの革新性
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            2025年12月17日に発表されたGemini 3 Flashは、Googleの最新AIモデルであり、「Pro」クラスの最先端の知能と、「Flash」クラスの卓越した速度およびコスト効率を両立させた画期的な存在です。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">💡</span>
            主要な特徴と性能
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>最強のコスパ</strong>: 知能あたりのコストパフォーマンスにおいて、現時点で最強のモデル。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>思考レベル機能</strong>: 開発者がモデルの思考の深さを動的に調整可能。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>1Mコンテキスト</strong>: 100万トークンの広大なコンテキストウィンドウと高度なマルチモーダル能力。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">圧倒的なベンチマーク</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>Artificial Analysisでスコア71を記録</li>
                <li>Anthropic Opus 4.5(70)を超える性能</li>
                <li>最上位の3 Pro/GPT 5.2(73)に肉薄</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">新次元のユースケース</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>リアルタイムの動画解析</li>
                <li>自律的なコーディングエージェント</li>
                <li>大規模なデータ抽出の効率化</li>
            </ul>
        </div>
    </div>
    """

    # Detail Card Content
    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: #1a73e8; color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem; color: white;">エコシステムと提供形態</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">全ユーザーに無償提供</h4>
                <p style="margin: 0; color: var(--text-light);">GeminiアプリやGoogle検索のAIモードでデフォルトモデルとして利用可能。</p>
            </div>
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">開発者向けプラットフォーム</h4>
                <p style="margin: 0; color: var(--text-light);">Google AI Studioや新プラットフォーム「Google Antigravity」でAPI提供。</p>
            </div>
             <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">リアルタイム・エージェント</h4>
                <p style="margin: 0; color: var(--text-light);">Google製品群全体を「リアルタイムな自律型エージェント」へと進化させる核となるモデル。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト (1-15)
    slides_list = []
    for i in range(1, 16):
        slides_list.append(f'<img src="../../input/day/1218_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)
    
    # 配色設定 (Google Blue)
    css_vars_block = """
    :root {
      --primary: #1a73e8; /* Google Blue */
      --accent: #4285f4;
      --accent2: #ea4335;
      --bg-dark: #202124;
      --bg-light: #f8f9fa;
      --border: #dadce0;
      --text: #3c4043;
      --text-light: #70757a;
      --tron-black: #000000;
    }
    header {
        background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%);
    }
    h3::before {
        background: var(--primary);
    }
    .section-header {
        border-bottom: 3px solid var(--primary);
    }
    """
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 -->')
    content_parts.append('  <div class="top-image-container">')
    
    # Image tag construction
    img_tag_parts = []
    img_tag_parts.append('<img src="../../input/day/1218.jpg" ')
    img_tag_parts.append('alt="Gemini 3 Flash Visual">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🚀</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>Proクラスの知能をFlashの速度とコストで</h3>')
    content_parts.append(highlight_box)
    content_parts.append(feature_grid)
    content_parts.append(detail_card)
    content_parts.append('  </section>')

    content_parts.append('  <!-- スライド資料 (全ページ) -->')
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">📖</span>')
    content_parts.append('      <h2>スライド資料 (全ページ)</h2>')
    content_parts.append('    </div>')
    
    content_parts.append('    <div class="download-link" style="text-align: center; margin-bottom: 24px;">')
    
    # PDF link construction
    pdf_link_parts = []
    pdf_link_parts.append('<a href="../../input/day/1218-No_Compromise_AI.pdf" target="_blank" ')
    pdf_link_parts.append('style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); ')
    pdf_link_parts.append('padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); ')
    pdf_link_parts.append('text-decoration: none; color: var(--text); transition: all 0.2s ease;">')
    content_parts.append('        ' + "".join(pdf_link_parts))
    
    content_parts.append('            <span style="font-size: 1.2rem;">📄</span>')
    content_parts.append('            <span>レポート全文をダウンロード (PDF)</span>')
    content_parts.append('        </a>')
    content_parts.append('    </div>')
    
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
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}レポート | Gemini 3 Flash")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_18.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1218()
