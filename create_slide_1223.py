import re
from pathlib import Path
import json
import os

def create_slide_1223():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-23
    date_jp = "2025年12月23日"
    date_slash = "2025/12/23"
    
    # Define content variables
    short_title = "AIエージェントの「スキル」" 
    main_title = "プロンプトはもう古い？AIの真価を引き出す「スキル」という新常識"
    subtitle = "AIに真の能力を「装備」させる、次世代の活用コンセプトを徹底解説"

    # CSS Variables for "Skill Purple" theme
    css_vars = """
    :root {
      --primary: #673ab7;
      --accent: #ffd600;
      --bg-light: #f3e5f5;
      --bg-dark: #311b92;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
      --border: #d1c4e9;
      --tron-black: #12005e;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #673ab7, #512da8); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            指示（プロンプト）から「装備（スキル）」へ
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            AIとの対話に限界を感じていませんか？「Agent Skills」は、AIに特定の能力や知識をパッケージ化して与える新しい仕組みです。これにより、AIは単なる対話相手から、あなたの専門知識を完璧に実行する「有能なエージェント」へと進化します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">💡</span>
            スキルがもたらす5つの衝撃
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>実行可能な知識</strong>: 指示書・資料・ツールを一体化した「知識のパッケージ」。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>段階的開示</strong>: 必要な時だけ詳細を読み込み、AIの短期記憶（トークン）を劇的に節約。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>オープン標準</strong>: プラットフォームを越えて使い回せる「AI業界のUSB規格」。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">暗黙知の資産化</div>
            <div class="feature-desc">あなたの思考プロセスや職人芸をデジタル資産としてパッケージ化。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">⚙️</span>
            <div class="feature-title">ハイブリッドモデル</div>
            <div class="feature-desc">柔軟な「スキル」と確実な「ワークフロー」を組み合わせて最強の自動化を実現。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🚀</span>
            <div class="feature-title">ポータビリティ</div>
            <div class="feature-desc">一度作ったスキルは、異なるAIツール間でも再利用可能に。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>なぜ「スキル」が必要なのか？</h4>
        <p>従来のプロンプトでは、毎回同じ指示を繰り返す必要があり、複雑なタスクではAIが混乱しがちでした。スキル化することで、AIは「専門家としての振る舞い」を永続的に装備し、ハルシネーション（嘘）を抑制しながら、正確かつ迅速にタスクを遂行できるようになります。</p>
    </div>

    <div class="card">
        <h4>「段階的開示」の魔法</h4>
        <p>AIに100個の知識を詰め込むと、それだけで記憶容量がいっぱいになります。スキルは「名前と説明」だけをまず教え、必要になった瞬間だけ「詳細」をロードします。この賢い仕組みにより、AIはパフォーマンスを落とさずに数百の専門知識を使い分けることが可能になります。</p>
    </div>
    """

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/1223.jpg" alt="Agent Skills Visual" onerror="this.src='https://via.placeholder.com/1200x600?text=1223+Agent+Skills'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🤖</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>AI活用の新常識：指示から能力へ</h3>
        {highlight_box}
        {feature_grid}
        {detail_cards}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全21ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/1223_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, 22)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🚀 {date_jp}最新動向 | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2025_12_23.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1223()
