import re
from pathlib import Path
import json
import os
import glob

import re
from pathlib import Path
import json
import os
import glob

def create_slide_0101():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月1日"
    date_slash = "2026/01/01"
    
    # Define content variables
    short_title = "2026年戦略分析" 
    main_title = "2026年戦略分析：技術的特異点の到来と地政学的・経済的・社会的変容"
    subtitle = "AI・自動化・ナノテクノロジーが再定義する文明の転換点"

    # Intro Box Content (Based on 0101.txt)
    intro_box = """
    <div style="background: linear-gradient(135deg, #856404, #b8860b); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(133, 100, 4, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            技術的シンギュラリティの地平線
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            技術成長が人間の制御を超えて加速し、文明に予測不能な変化をもたらす。
            2026年は、この「知能爆発」が理論から現実へと移行し、人類の時代を再定義する重大な局面。
        </p>
    </div>
    """

    # Highlight Box Content (Based on 0101.txt Section 2)
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🎯</span>
            2026年の3つの重要論点
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>能力の到達点</strong>: 数学・コーディング・法務で「博士号レベル」の推論能力が出現。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>物理的限界</strong>: ロボティクスは認知進化に追いつかず、LLMの根本課題も残存。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>顕在化するリスク</strong>: 電力制約、セキュリティ脅威、AI地政学が成長のブレーキに。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">中核概念：知能爆発</h4>
            <p style="margin: 0; color: var(--text-light); font-size: 0.95rem;">
                自己改良AIが再帰的に賢いAIを作り、知能が加速度的に向上して超知能に至る（I.J.Good, 1965）。
            </p>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">到来時期の不確実性</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light); font-size: 0.95rem;">
                <li>Kurzweil予測：2045年</li>
                <li>現在の進歩率：収穫加速の法則に従う</li>
                <li>制御可能性：Vingeの「人類の時代の終わり」</li>
            </ul>
        </div>
    </div>
    """

    # Detail Card Content
    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: var(--primary); color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem; color: white;">展望：博士号レベル能力の社会実装</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">専門領域の革新</h4>
                <p style="margin: 0; color: var(--text-light);">推論能力の向上により、創薬や法務、高度なエンジニアリング領域での実用化が加速します。</p>
            </div>
            <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">物理世界のボトルネック</h4>
                <p style="margin: 0; color: var(--text-light);">エネルギー確保とロボティクスの進化が、2020年代後半の主要な競争軸となります。</p>
            </div>
        </div>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0101_slides"
    if os.path.exists(slide_dir):
        slides = sorted([f for f in os.listdir(slide_dir) if f.endswith(".jpg")])
        slide_count = len(slides)
    else:
        slide_count = 0
        print(f"Warning: Slide directory {slide_dir} not found.")

    # Slides Section HTML
    slides_html = ""
    if slide_count > 0:
        slides_html = "\n".join([f'<img src="../../input/day/0101_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])
    else:
        slides_html = '<p style="text-align: center; color: var(--text-light);">表示できるスライド画像がありません。</p>'

    # CSS Variables (Gold / New Year theme)
    css_vars_block = """
    :root {
      --primary: #856404;
      --accent: #ffc107;
      --accent2: #b8860b;
      --bg-dark: #212529;
      --bg-light: #fff3cd;
      --border: #ffeeba;
      --text: #212529;
      --text-light: #6c757d;
      --tron-black: #000000;
    }
    header {
      background: linear-gradient(135deg, var(--tron-black) 0%, #1a1a1a 100%);
    }
    h3::before {
      background: var(--primary);
    }
    .section-header {
      border-bottom: 3px solid var(--primary);
    }
    .slide-img {
      width: 100%;
      max-width: 1000px;
      height: auto;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      border: 1px solid var(--border);
      transition: transform 0.3s ease;
      margin-bottom: 24px;
    }
    .slide-img:hover {
      transform: scale(1.01);
      box-shadow: 0 8px 30px rgba(0,0,0,0.2);
    }
    .slides-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 24px;
      width: 100%;
    }
    """

    # Assemble Main Content
    main_content_html = f"""
    <main>
      <div class="top-image-container" style="text-align: center; margin-bottom: 48px;">
        <img src="../../input/day/0101.png" alt="01/01 Visual" style="width: 100%; max-width: 1000px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🔗</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>今日のハイライト</h3>
        {highlight_box}
        {feature_grid}
        {detail_card}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全{slide_count}ページ)</h2>
        </div>
        <div class="slides-container">
          {slides_html}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars_block)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"📰 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2026_01_01.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0101()
