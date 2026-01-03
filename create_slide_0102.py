import re
from pathlib import Path
import json
import os
import glob

def create_slide_0102():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月2日"
    date_slash = "2026/01/02"
    
    # Try to find title from PDF filename if possible
    pdf_files = glob.glob("input/day/0102-*.pdf")
    pdf_title = "Title Placeholder"
    if pdf_files:
        # Extract title from filename "0102-Title.pdf"
        basename = os.path.basename(pdf_files[0])
        # Remove 0102- and .pdf
        pdf_title = basename.replace("0102-", "").replace(".pdf", "").replace("_", " ")

    # Define content variables (based on 0102.txt)
    short_title = "Control, Not Vibe" 
    main_title = "プロは “バイブス” でコードを書かない。支配する。"
    subtitle = "AIエージェント時代の新たな「熟練」：ソフトウェア工学の原理原則による徹底した制御戦略"

    # CSS Variables (Dark / Tech theme)
    css_vars = """
    :root {
      --primary: #007bff;
      --accent: #17a2b8;
      --bg-light: #f8f9fa;
      --bg-dark: #212529;
      --text: #212529;
      --text-light: #6c757d;
      --border: #dee2e6;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #007bff, #17a2b8); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 123, 255, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            AIは「魔法の杖」ではなく「部下」である
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            2025年に流行した「Vibe Coding」の幻想を排し、熟練の開発者がいかにしてAIエージェントを徹底的な管理下に置き、品質と生産性を両立させているかを解き明かします。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🛠️</span>
            プロフェッショナルの「制御」戦略
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>コンテキストの徹底管理</strong>: 曖昧な指示を避け、技術スタックや命名規則まで明確な文脈を叩き込む。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>分割統治の徹底</strong>: 巨大な計画も小刻みなステップに分解し、AIの脱線を許さない。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>全行レビューの遂行</strong>: 出力されたコードは一行残らず読み、保守性と可読性を人間が審査する。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <div class="feature-title">AIの独壇場</div>
            <div class="feature-desc">ボイラープレート生成、テスト記述、ドキュメント作成などの定型業務。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">人間の聖域</div>
            <div class="feature-desc">複雑なビジネスロジック、アーキテクチャ設計、セキュリティの意思決定。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">⚖️</span>
            <div class="feature-title">品質への執着</div>
            <div class="feature-desc">「動いたからヨシ」ではなく、工学的な原理原則に基づいた厳格な評価。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>幻想の破壊：AIは自律しない</h4>
        <p>プロの開発者の100%が、AI任せにせず設計と実装の主導権を握り続けています。AIは「自動運転車」ではなく、人間が操る「F1マシン」です。</p>
    </div>

    <div class="card">
        <h4>AI時代の新たな「熟練」</h4>
        <p>ソフトウェア工学の原理原則を知り、AIの手綱を厳格に握れる者だけが、より高度な指揮官として生き残る世界が到来しています。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0102_slides"
    if os.path.exists(slide_dir):
        slides = sorted([f for f in os.listdir(slide_dir) if f.endswith(".jpg")])
        slide_count = len(slides)
    else:
        slide_count = 0
        print(f"Warning: Slide directory {slide_dir} not found. Assuming 0 slides.")

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/0102.png" alt="01/02 Visual" onerror="this.src='https://placehold.co/1200x600?text=0102+AI+News'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📰</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>Today's Updates</h3>
        {highlight_box}
        {feature_grid}
        {detail_cards}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全{slide_count}ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/0102_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"📰 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2026_01_02.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0102()
