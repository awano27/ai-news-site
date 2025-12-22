import re
from pathlib import Path
import json
import os

def create_slide_1222():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-22
    date_jp = "2025年12月22日"
    date_slash = "2025/12/22"
    
    # Define content variables
    short_title = "国産AI 3兆円プロジェクト" 
    main_title = "国産AIの逆襲：政府・企業連合による3兆円プロジェクトの全貌"
    subtitle = "「フィジカルAI」で世界をリードする、日本の新たな国家戦略を徹底解説"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #1a73e8, #1557b0); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            日本の未来をかけた「3兆円」の巨大投資
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            日本政府とソフトバンクなどのトップ企業がタッグを組み、総額3兆円を投じて「国産AI」の開発に乗り出します。これは単なる技術開発ではなく、日本の産業競争力と安全保障を守るための国家的な挑戦です。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🇯🇵</span>
            なぜ今「国産」が必要なのか？
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>経済競争力の確保</strong>: 海外AIへの依存を脱却し、日本独自の「ルール」で産業を強化。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>安全保障の強化</strong>: 医療・インフラなどの重要技術を自国で管理し、国民の暮らしを守る。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>フィジカルAIの創出</strong>: 日本の強みである「ものづくり」とAIを融合させ、新市場を開拓。</span>
            </li>
        </ul>
    </div>
    """

    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">官民連携のドリームチーム</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>政府：5年間で約1兆円を支援</li>
                <li>民間：ソフトバンク中心に約2兆円投資</li>
                <li>2026年春：100人規模の「新会社」設立</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">切り札「フィジカルAI」</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>現実世界でロボットを賢く動かすAI</li>
                <li>コンビニの品出しや介護の自動化</li>
                <li>災害現場やインフラ点検での活用</li>
            </ul>
        </div>
    </div>
    """

    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: #1a73e8; color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem; color: white;">展望：AIとロボットが当たり前の社会へ</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">1兆パラメータ規模の高性能モデル</h4>
                <p style="margin: 0; color: var(--text-light);">世界のトップAIに匹敵する性能を目指し、北海道や堺市に巨大データセンターを建設。</p>
            </div>
            <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">社会課題の解決へ</h4>
                <p style="margin: 0; color: var(--text-light);">深刻な人手不足を解消し、医療・介護・物流の現場をAIの力で支える未来を目指します。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト
    slides_list = []
    # Note: 1222_slides directory might not exist yet based on previous list_dir, 
    # but the user asked to create slides, so we assume images might be there or will be added.
    # Actually, list_dir showed 1222.jpg but no 1222_slides dir.
    slide_dir = Path(f"input/day/1222_slides")
    if slide_dir.exists():
        count = len(list(slide_dir.glob("slide_*.jpg")))
        for i in range(1, count + 1):
            slides_list.append(f'<img src="../../input/day/1222_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    else:
        slides_list.append('<p style="text-align: center; color: var(--text-light);">スライド画像がまだ準備されていません。</p>')
    
    slides_html = "\n".join(slides_list)
    
    # 配色設定 (Japan Blue theme)
    css_vars_block = """
    :root {
      --primary: #1a73e8;
      --accent: #4285f4;
      --accent2: #1557b0;
      --bg-dark: #202124;
      --bg-light: #f8f9fa;
      --border: #dadce0;
      --text: #202124;
      --text-light: #5f6368;
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
    content_parts.append('  <div class="top-image-container">')
    content_parts.append('    <img src="../../input/day/1222.jpg" alt="Japan AI Project Visual" onerror="this.src=\'https://via.placeholder.com/1200x600?text=1222+Japan+AI+Project\'">')
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🇯🇵</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>国家の命運を分ける戦略的投資</h3>')
    content_parts.append(highlight_box)
    content_parts.append(feature_grid)
    content_parts.append(detail_card)
    content_parts.append('  </section>')
  
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">📖</span>')
    content_parts.append('      <h2>スライド資料 (全ページ)</h2>')
    content_parts.append('    </div>')
    content_parts.append('    <div class="slides-container">')
    content_parts.append(slides_html)
    content_parts.append('    </div>')
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
    output_path = "presentations/day_slides/day_slide_2025_12_22.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1222()
