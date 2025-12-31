import re
from pathlib import Path
import json
import os
import glob

def create_slide_1231():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年12月31日"
    date_slash = "2025/12/31"
    
    # Try to find title from PDF filename if possible
    pdf_files = glob.glob("input/day/1231-*.pdf")
    pdf_title = "Title Placeholder"
    if pdf_files:
        # Extract title from filename "1231-Title.pdf"
        basename = os.path.basename(pdf_files[0])
        # Remove 1231- and .pdf
        pdf_title = basename.replace("1231-", "").replace(".pdf", "").replace("_", " ")

    # Define content variables
    short_title = "AI開発の混沌と戦略的統制" 
    main_title = "2025年末 AIツール活用戦略レポート"
    subtitle = "ハイプから価値創出への転換点：自律レベルに応じた管理フレームワークの構築"

    # CSS Variables (Deep Blue / Strategy theme)
    css_vars = """
    :root {
      --primary: #1a365d;
      --accent: #3182ce;
      --bg-light: #f7fafc;
      --bg-dark: #1a202c;
      --text: #2d3748;
      --text-light: #718096;
      --border: #e2e8f0;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #1a365d, #3182ce); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(26, 54, 93, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            「どのツールか」から「いかに管理するか」へ
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            AIツールの乱立期を経て、2025年末の焦点は「自律性の安全な管理」と「チームプロセスへの統合」という戦略的課題へと移行しました。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🎯</span>
            AI活用の新常識：3つの柱
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>自律レベルの定義</strong>: インタラクティブ、ローカル自動化、非同期委任の3階層で権限を管理。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>エージェントとの契約</strong>: 直接反映禁止、PRベースの厳格な人間によるレビューを徹底。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>指示のコード化</strong>: プロンプトをバージョン管理し、チームの共有資産・エンジニアリングプロセスへ。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🎻</span>
            <div class="feature-title">Orchestra Model</div>
            <div class="feature-desc">専門家AI（Claude, Gemini, Cursor等）を人間が指揮し、最適な工程で使い分ける。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🛡️</span>
            <div class="feature-title">Guardrails</div>
            <div class="feature-desc">.claude/settings.json等で技術的に制約を強制。ハルシネーションや漏洩を防止。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📊</span>
            <div class="feature-title">ROI Focus</div>
            <div class="feature-desc">2026年は「ハイプ」から「経済的価値」へ。40%のプロジェクトが失敗するとの予測も。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>「Vibe Coding」の幻想と現実</h4>
        <p>プロの開発者はAI生成コードの平均50%を修正。盲信ではなく、厳格な「コントロール」こそが価値を最大化する鍵であることが研究で示されています。</p>
    </div>

    <div class="card">
        <h4>2026年への展望</h4>
        <p>Agentic AIの普及、ROIへのシビアなチェック、そしてオンザジョブでの継続学習。技術の価格ではなく「管理フレームワークの厳格さ」が組織の差を生みます。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/1231_slides"
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
        <img src="../../input/day/1231.png" alt="12/31 Visual" onerror="this.src='https://placehold.co/1200x600?text=1231+AI+News'">
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
          {"".join([f'<img src="../../input/day/1231_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
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
    output_path = f"presentations/day_slides/day_slide_2025_12_31.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1231()
