import re
from pathlib import Path
import json

def create_slide_1219():
    # Load base_template.html
    with open("base_template.html", "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-19
    date_jp = "2025年12月19日"
    date_slash = "2025/12/19"
    date_file = "2025-12-19"
    
    # Define content variables
    short_title = "GPT-5.2-Codex" 
    main_title = "OpenAI、自律型エンジニアリングモデル「GPT-5.2-Codex」をリリース"
    subtitle = "エージェント型ワークフローへの転換：開発・セキュリティを自律的に遂行する新世代モデル"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #00a67e, #007a5e); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            自律型エージェント時代の開幕
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            2025年12月18日に発表されたGPT-5.2-Codexは、単なるコード補完ツールを超え、複雑なエンジニアリングタスクを自律的に計画・遂行する「エージェント型」への本格的な移行を象徴するモデルです。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">⚙️</span>
            技術的進化と中核機能
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>ネイティブなコンテキスト圧縮</strong>: 長期タスクにおける情報の減衰を防ぎ、大規模リポジトリの継続的な操作を可能に。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>エージェント専用の推論層</strong>: 複数ステップの複雑なコーディングタスクを、エラーの試行錯誤を含めて自律的に完遂。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>セキュリティ特化の評価</strong>: 現実の脆弱性発見（Reactの事例など）において実証された、防御的サイバーセキュリティにおける高い性能。</span>
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
                <li>SWE-Bench Pro: 56.4%（業界最高水準）</li>
                <li>Terminal-Bench 2.0: 64.0%</li>
                <li>複雑なタスクの完遂能力が飛躍的に向上</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">戦略的・防御的な活用</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>Reactの未知の脆弱性3件を発見・修正</li>
                <li>「Trusted Access」による安全な展開</li>
                <li>エンジニアは「戦略立案・レビュー」へ役割シフト</li>
            </ul>
        </div>
    </div>
    """

    # Detail Card Content
    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: #00a67e; color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem; color: white;">デュアルユースのリスクと安全対策</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">Preparedness Framework</h4>
                <p style="margin: 0; color: var(--text-light);">OpenAI独自の安全性評価に基づき、サイバーセキュリティ能力のリスクを常時監視。</p>
            </div>
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">Trusted Accessプログラム</h4>
                <p style="margin: 0; color: var(--text-light);">高度な防御機能を、信頼できるセキュリティ専門家から優先的に提供し、非対称な優位性を確保。</p>
            </div>
             <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">エンジニアリングの再定義</h4>
                <p style="margin: 0; color: var(--text-light);">単なるコード生成を超え、AIと協働する「戦略としてのソフトウェア開発」の時代へ。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト (1-15)
    slides_list = []
    for i in range(1, 16):
        slides_list.append(f'<img src="../../input/day/1219_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)
    
    # 配色設定 (OpenAI / Codex Green)
    css_vars_block = """
    :root {
      --primary: #00a67e; /* OpenAI Green */
      --accent: #10a37f;
      --accent2: #202123;
      --bg-dark: #202124;
      --bg-light: #f7f7f8;
      --border: #d9d9e3;
      --text: #353740;
      --text-light: #6e6e80;
      --tron-black: #000000;
    }
    header {
        background: linear-gradient(135deg, #00a67e 0%, #10a37f 100%);
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
    img_tag_parts.append('<img src="../../input/day/1219.jpg" ')
    img_tag_parts.append('alt="GPT-5.2-Codex Visual">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🤖</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>自律型エージェントへの進化</h3>')
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
    pdf_link_parts.append('<a href="../../input/day/1219-GPT-5.2-Codex_自律型エンジニアリング.pdf" target="_blank" ')
    pdf_link_parts.append('style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); ')
    pdf_link_parts.append('padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); ')
    pdf_link_parts.append('text-decoration: none; color: var(--text); transition: all 0.2s ease;">')
    content_parts.append('        ' + "".join(pdf_link_parts))
    
    content_parts.append('            <span style="font-size: 1.2rem;">📄</span>')
    content_parts.append('            <span>技術ホワイトペーパーをダウンロード (PDF)</span>')
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
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}最新動向 | {short_title}")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_19.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1219()
