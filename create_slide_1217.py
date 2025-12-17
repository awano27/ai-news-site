import re
from pathlib import Path
import json

def create_slide_1217():
    # Load base_template.html
    with open("base_template.html", "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-17
    date_jp = "2025年12月17日"
    date_slash = "2025/12/17"
    date_file = "2025-12-17"
    
    # Define content variables
    short_title = "ChatGPT Images" 
    main_title = "OpenAI、新画像生成モデル「ChatGPT Images」を発表"
    subtitle = "最大4倍の高速化も、Googleとの品質競争が激化"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #000000, #10A37F); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            画像生成AIの新時代：ビジネスツールへの進化
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            OpenAIは、新旗艦モデル「GPT-Image-1.5」を搭載した「ChatGPT Images」をリリースしました。最大4倍の高速化とビジネス利用に特化した機能強化により、画像生成AIは技術デモの段階を超え、実用的なプロダクションツールとしての地位を確立しようとしています。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">⚡</span>
            ChatGPT Imagesの核心的な強化点
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>最大4倍の高速化</strong>: クリエイティブな試行錯誤のサイクルを劇的に短縮し、反復可能な業務プロセスへ。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>指示追従性と編集精度の向上</strong>: 人物の顔やロゴなど、一貫性が求められるディテールを維持しながら精密に編集可能。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>専用UI「Images」</strong>: プリセットスタイルやトレンドプロンプトを備え、専門知識不要で高品質なビジュアルを作成可能。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">ChatGPT Images (OpenAI)</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li><strong>強み</strong>: 圧倒的な生成速度、効率性、手軽さ</li>
                <li><strong>最適用途</strong>: アイデア出し、SNS投稿、プロトタイピング</li>
                <li><strong>評価</strong>: LMArenaベンチマークで1位（指示追従性）</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">Nano Banana (Google)</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li><strong>強み</strong>: 写真のようなリアリズム、AIっぽさの少なさ</li>
                <li><strong>最適用途</strong>: 最終ビジュアル制作、高品質資料、写真</li>
                <li><strong>評価</strong>: ユーザーコミュニティで画質・質感を高く評価</li>
            </ul>
        </div>
    </div>
    """

    # Detail Card Content
    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: var(--bg-dark); color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem;">市場評価の乖離：ベンチマーク vs ユーザー実感</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">客観的ベンチマーク (LMArena)</h4>
                <p style="margin: 0; color: var(--text-light);">GPT-Image-1.5が1位を獲得。プロンプトへの忠実性や多様なスタイルへの対応力が高く評価されています。</p>
            </div>
             <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">ユーザーコミュニティ (X/Reddit)</h4>
                <p style="margin: 0; color: var(--text-light);">「Nano Bananaの方がリアルでAIっぽくない」という声が根強い。微細な質感やドキュメンタリー風のリアリティにおいては、依然としてGoogleに優位性があるとの認識です。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト (1-13)
    slides_list = []
    for i in range(1, 14):
        slides_list.append(f'<img src="../../input/day/1217_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)
    
    # 配色設定 (OpenAI Green)
    css_vars_block = """
    :root {
      --primary: #10A37F; /* OpenAI Green */
      --accent: #000000; /* Black */
      --accent2: #4A4A4A;
      --bg-dark: #202123;
      --bg-light: #f7f7f8;
      --border: #d9d9e3;
      --text: #343541;
      --text-light: #6e6e80;
    }
    header {
        background: linear-gradient(135deg, #000000 0%, #10A37F 100%);
    }
    """
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 -->')
    content_parts.append('  <div class="top-image-container">')
    
    # Image tag construction
    img_tag_parts = []
    img_tag_parts.append('<img src="../../input/day/1217.jpg" ')
    img_tag_parts.append('alt="ChatGPT Images Visual">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🎨</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>機能強化と競合比較</h3>')
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
    pdf_link_parts.append('<a href="../../input/day/1217-AI_Image_Giants_Showdown.pdf" target="_blank" ')
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
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}レポート | {short_title}")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_17.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1217()
