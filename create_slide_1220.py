import re
from pathlib import Path
import json

def create_slide_1220():
    # Load base_template.html
    with open("base_template.html", "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-20
    date_jp = "2025年12月20日"
    date_slash = "2025/12/20"
    date_file = "2025-12-20"
    
    # Define content variables
    short_title = "Agent Skills" 
    main_title = "AIエージェントの「仕事術」：新標準『Agent Skills』徹底解説"
    subtitle = "プロンプトからワークフローへのパラダイムシフト：組織の知的資産としてAIを「育てる」新世代の標準仕様"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #10a37f, #007a5e); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            AIを「指示する」から「育てる」時代へ
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            2025年12月18日にオープンスタンダードとして公開された「Agent Skills」は、AIに特定の業務マニュアルと専用工具をインストールし、再利用可能にする画期的な仕組みです。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">💡</span>
            Agent Skillsの核心概念
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>形式知化された「仕事術」</strong>: SKILL.md(マニュアル)とscripts(ツール)により、プロのノウハウをAIにインストール。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>圧倒的な効率性</strong>: 段階的開示設計により、コンテキスト消費を最大98.7%削減。大規模な自動化を経済的に実現。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><span><strong>オープンスタンダード</strong>: Claudeだけでなく、GitHub Copilotや各種ツール間で「スキル」を共有・再利用可能。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">推論空間の制御</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>プロンプト職人から工学的制御へ</li>
                <li>組織のワークフローへの確実な誘導</li>
                <li>非エンジニアでもAIの振る舞いを管理可能</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">実用的な自動化</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>ブランド準拠の資料自動作成</li>
                <li>パートナーSkills(Notion, Figma等)との連携</li>
                <li>TDDなどの開発プロセスの標準化</li>
            </ul>
        </div>
    </div>
    """

    # Detail Card Content
    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: #10a37f; color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem; color: white;">導入におけるセキュリティと戦略</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">サプライチェーン・セキュリティ</h4>
                <p style="margin: 0; color: var(--text-light);">Skillsはコード実行権限を持つため、導入前の徹底した中身のレビューが不可欠。</p>
            </div>
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">推論能力の不変性</h4>
                <p style="margin: 0; color: var(--text-light);">Skillsは「指示」を強化するものであり、LLM自体の推論ミスを完全に消すものではないことに注意。</p>
            </div>
             <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">組成的・長期的資産</h4>
                <p style="margin: 0; color: var(--text-light);">ベンダーに依存しない「神経系」を構築し、組織の知的資産としてAIワークフローを蓄積。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト (1-10) - 1220.pdf has 10 pages? Let me check quickly or just use a loop. 
    # Usually it's around 10-15. Let's look at the dir output from earlier... it didn't exist yet.
    # I'll check the PDF page count in the next step or just use a placeholder and fix it.
    # Actually, the conversion script will tell us. Let's assume 11 pages based on typical files.
    # Wait, I can just dynamically find the images in the directory after conversion.
    # But for simplicity, I'll use a fixed number for now or update it after running conversion.
    # Let's check 1220.txt content again... it doesn't say page count.
    # I'll use a loop that checks file existence or just a safe range like 15.
    
    slides_list = []
    # 1220.pdf has 18 pages
    for i in range(1, 19):
        slides_list.append(f'<img src="../../input/day/1220_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)
    
    # 配色設定 (Green/Teal for Agent Skills)
    css_vars_block = """
    :root {
      --primary: #10a37f;
      --accent: #007a5e;
      --accent2: #202123;
      --bg-dark: #202124;
      --bg-light: #f7f7f8;
      --border: #d9d9e3;
      --text: #353740;
      --text-light: #6e6e80;
      --tron-black: #000000;
    }
    header {
        background: linear-gradient(135deg, #10a37f 0%, #007a5e 100%);
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
    img_tag_parts.append('<img src="../../input/day/1220.jpg" ')
    img_tag_parts.append('alt="Agent Skills Visual">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🧠</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>AIエージェントの能力拡張と標準化</h3>')
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
    pdf_link_parts.append('<a href="../../input/day/1220-Agent_Skills_知識を資産に変える.pdf" target="_blank" ')
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
    output_path = "presentations/day_slides/day_slide_2025_12_20.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1220()
