import re
from pathlib import Path
import json
import os

def create_slide_skills():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年12月22日"
    date_slash = "2025/12/22"
    
    # Define content variables
    short_title = "Skill: Slide Generation" 
    main_title = "デイリーAIニューススライド生成スキル"
    subtitle = "ニュース要約からGit反映までの標準ワークフローをマスターする"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #0f9d58, #0b8043); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            効率的で一貫性のある情報発信のために
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            このスキルは、特定の日のAIニュース情報を基に、ウェブサイト用のスライドHTMLを生成し、インデックスを更新してGitに成果物を反映させるための標準的な手順を定義します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🛠️</span>
            ワークフローの3つの柱
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>スクリプトの継承</strong>: 前日のスクリプトをベースに、日付と内容を迅速に更新。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>自動化と検証</strong>: 画像変換からHTML生成までを自動化し、ブラウザでレイアウトを確認。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>確実な同期</strong>: インデックス更新後、Git pull --rebase を経てリモートへ反映。</span>
            </li>
        </ul>
    </div>
    """

    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">主要な成果物</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>スライド画像群 (MMDD_slides/)</li>
                <li>スライドHTML (day_slide_YYYY_MM_DD.html)</li>
                <li>更新されたインデックス (day_slides_index.html)</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">入力ソース</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>MMDD.txt: ニュースの要約テキスト</li>
                <li>MMDD-Topic.pdf: 技術解説等の元資料</li>
                <li>base_template.html: 共通デザイン</li>
            </ul>
        </div>
    </div>
    """

    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: #0f9d58; color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem; color: white;">運用上の注意点</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">デザインの一貫性</h4>
                <p style="margin: 0; color: var(--text-light);">トピックに合わせた配色（--primary等のCSS変数）を設定し、ブランドイメージを維持します。</p>
            </div>
            <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">競合の回避</h4>
                <p style="margin: 0; color: var(--text-light);">プッシュ前に必ず git pull --rebase を行い、リモートの変更を安全に取り込みます。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト (Skills slide doesn't have specific images, so we show a placeholder or just skip)
    slides_html = '<p style="text-align: center; color: var(--text-light);">このスキルガイドには個別のスライド画像はありません。</p>'
    
    # 配色設定 (Gemma Green theme)
    css_vars_block = """
    :root {
      --primary: #0f9d58;
      --accent: #34a853;
      --accent2: #188038;
      --bg-dark: #202124;
      --bg-light: #f8f9fa;
      --border: #dadce0;
      --text: #202124;
      --text-light: #5f6368;
      --tron-black: #000000;
    }
    header {
        background: linear-gradient(135deg, #0f9d58 0%, #34a853 100%);
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
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🔗</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>ワークフローの標準化</h3>')
    content_parts.append(highlight_box)
    content_parts.append(feature_grid)
    content_parts.append(detail_card)
    content_parts.append('  </section>')
  
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">📖</span>')
    content_parts.append('      <h2>スキル詳細</h2>')
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
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🎓 スキルガイド | {short_title}")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_skills.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_skills()
