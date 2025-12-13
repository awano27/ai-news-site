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
    short_title = "GPT-5.2 業務エンジン" 
    main_title = "GPT-5.2：知識労働を加速する「業務エンジン」への進化"
    subtitle = "調査・分析・資料化・実装支援を統合し、知的生産性を刷新する"

    # HTML Parts Construction
    
    # Intro Box
    intro_box = """
    <div style=\"background: linear-gradient(135deg, #000000, #10a37f); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);\">
        <p style=\"font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;\">
            AIは「ツール」から「業務エンジン」へ
        </p>
        <p style=\"font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;\">
            GPT-5.2は単なる便利なチャットAIではなく、調査・分析・資料化・実装といった「知識労働」をまとめて加速するための「業務エンジン」です。
            意思決定と実行のスピードを劇的に上げ、競合に対する構造的な優位性を構築します。
        </p>
    </div>
    """

    # Highlight Box (3つの価値)
    highlight_box = """
    <div class="highlight-box" style="background-color: #f0fdf4; border-left: 5px solid #10a37f; padding: 24px; margin-bottom: 32px; border-radius: 8px;">
      <h3 style="color: #0d8a6a; margin-top: 0; margin-bottom: 12px; display: flex; align-items: center; font-size: 1.4rem;">
         <span style="font-size: 1.8rem; margin-right: 10px;">🚀</span>
         GPT-5.2がもたらす3つの核心的価値
      </h3>
      <ul style="font-size: 1.1rem; line-height: 1.8; color: #202123; list-style: none; padding: 0;">
        <li style="margin-bottom: 12px;"><strong>1. 統合と整理：</strong> 長文や複数資料（契約書、仕様書等）を横断的に解析し、要点や論点を短時間で抽出。</li>
        <li style="margin-bottom: 12px;"><strong>2. 直結する資料化：</strong> 調査結果をそのままスライドや表計算のたたき台へ。企画から資料化までのリードタイムを圧縮。</li>
        <li><strong>3. リスク管理と最大化：</strong> 信頼性は向上したが、「人の検証」を前提とした運用でリスクを抑えつつ効果を最大化。</li>
      </ul>
    </div>
    """

    # Feature Grid (部門別メリット)
    feature_grid = """
    <div class="card accent" style="background: white; border: 1px solid var(--border); border-top: 4px solid var(--primary); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <h4 style="margin-bottom: 20px; font-size: 1.3rem; color: var(--text); border-bottom: 1px solid var(--border); padding-bottom: 10px;">部門別・活用インパクト</h4>
      
      <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">📊</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">企画・マーケ・財務</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                市場・競合整理、提案書や稟議骨子の作成、モデル草案などで作業の初速を最大化。
            </div>
        </div>
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">💻</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">開発・IT</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                設計検討、実装案作成、リファクタリング支援により、開発リードタイムを大幅短縮。
            </div>
        </div>
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">⚖️</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">法務・知財・R&D</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                契約横断レビュー、論文大量要約、リスク条項抽出など、高負荷タスクを効率化。
            </div>
        </div>
      </div>
    </div>
    """

    # Detail Card (推奨90日プラン)
    detail_card = """
    <div class="card" style="background: white; border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <h3 style="margin-bottom: 20px; color: var(--text); display: flex; align-items: center;">
            <span style="width: 6px; height: 24px; background: var(--primary); margin-right: 10px; border-radius: 3px;"></span>
            推奨：成果を出すための「90日プラン」
        </h3>
        
        <p style="margin-bottom: 20px; line-height: 1.7;">
            知的生産プロセスを刷新し、確実に成果につなげるための導入ステップです。
        </p>

        <div style="display: grid; grid-template-columns: 1fr; gap: 15px; margin-bottom: 20px;">
            <div style="background: #f9f9f9; padding: 16px; border-radius: 8px; border-left: 4px solid #10a37f; display: flex; align-items: flex-start;">
                <div style="background: #10a37f; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px; flex-shrink: 0;">1</div>
                <div>
                    <h4 style="margin: 0 0 5px 0; color: #202123;">優先業務の選定</h4>
                    <p style="margin: 0; font-size: 0.95rem; color: #666;">頻度が高く工数が重い業務を3件選び、優先順位を設定。</p>
                </div>
            </div>
             <div style="background: #f9f9f9; padding: 16px; border-radius: 8px; border-left: 4px solid #10a37f; display: flex; align-items: flex-start;">
                <div style="background: #10a37f; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px; flex-shrink: 0;">2</div>
                <div>
                    <h4 style="margin: 0 0 5px 0; color: #202123;">PoC（概念実証）- 2週間</h4>
                    <p style="margin: 0; font-size: 0.95rem; color: #666;">品質・工数・再現性・リスクを数字と具体例で評価。</p>
                </div>
            </div>
             <div style="background: #f9f9f9; padding: 16px; border-radius: 8px; border-left: 4px solid #10a37f; display: flex; align-items: flex-start;">
                <div style="background: #10a37f; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px; flex-shrink: 0;">3</div>
                <div>
                    <h4 style="margin: 0 0 5px 0; color: #202123;">ガバナンスと標準化</h4>
                    <p style="margin: 0; font-size: 0.95rem; color: #666;">運用ルール（権限、監査、レビュー）を整備し、テンプレート化して展開。</p>
                </div>
            </div>
        </div>
        <p style="font-size: 0.95rem; background: #eff6ff; padding: 12px; border-radius: 6px; color: #1e40af; border: 1px solid #bfdbfe;">
            💡 <strong>Point:</strong> 「作業を少し早くする」のではなく、「プロセスそのものを短縮する」ことを目指しましょう。
        </p>
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
    pdf_link_parts.append('<a href="../../input/day/1212-GPT-5.2-Business-Engine.pdf" target="_blank" ') # Escaped quotes here
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