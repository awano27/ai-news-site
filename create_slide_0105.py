import re
from pathlib import Path
import json
import os
import glob

def create_slide_0105():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月5日"
    date_slash = "2026/01/05"

    # Define content variables
    short_title = "Sentient Sparks"
    main_title = "Sentient Sparks: オープンソースAGIコミュニティプログラム"
    subtitle = "オープンソースAGI開発を加速する戦略的コミュニティ貢献者プログラムの全貌"

    # CSS Variables (AGI / Community theme - purple & teal)
    css_vars = """
    :root {
      --primary: #7c3aed;
      --accent: #14b8a6;
      --bg-light: #f5f3ff;
      --bg-dark: #1e1b4b;
      --text: #1e1b4b;
      --text-light: #6b7280;
      --border: #e0e7ff;
      --tron-black: #0f172a;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #7c3aed, #14b8a6); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(124, 58, 237, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            技術者だけでなく、すべての貢献者を公式に認定する
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            Sentient Foundationは、オープンソースAGIの民主化という壮大なビジョンを広めるため、コンテンツクリエイター、教育者、翻訳者、コミュニティビルダーなど、多様な才能を持つコミュニティメンバーを公式に支援します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🌟</span>
            Sentient Sparksプログラムの特徴
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>月次10名選出</strong>: グローバル貢献者6名 + リージョナル貢献者4名のローテーション制</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>多様なスキルセット歓迎</strong>: エンジニア以外も対象。教育、翻訳、イベント主催、コンテンツ制作など</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>非金銭的インセンティブ</strong>: X公式バッジ、限定グッズ、イベントVIP招待、ロードマップ早期アクセス</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🌍</span>
            <div class="feature-title">グローバル貢献者</div>
            <div class="feature-desc">世界規模で影響力を持ち、英語を中心に広範囲にリーチする6名</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📍</span>
            <div class="feature-title">リージョナル貢献者</div>
            <div class="feature-desc">特定地域のコミュニティに根差し、地域言語で活動する4名</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔄</span>
            <div class="feature-title">ローテーション制</div>
            <div class="feature-desc">毎月一部入れ替わることで、新しい才能に門戸を開く柔軟な仕組み</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>戦略的意義：長期コミットメントの育成</h4>
        <p>本プログラムは、将来的なトークン生成イベント(TGE)を見据え、短期的なハイプではなく、真にSentientのビジョンに共感する忠実なコミュニティを構築するための布石です。技術者以外の貢献を正式に評価することで、エコシステムの裾野を広げ、グローバルな採用を促進します。</p>
    </div>

    <div class="card">
        <h4>オープンソースAGI民主化への貢献</h4>
        <p>Sentient Foundationは「単一の事業体に支配されないオープンソースAGIの開発」というミッションを掲げています。Sparksプログラムは、このビジョンを世界中に伝える「声」を増幅させ、技術面とコミュニティ面の両輪でエコシステムを成長させる重要な施策です。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0105_slides"
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
        <img src="../../input/day/0105.png" alt="01/05 Visual" onerror="this.src='https://placehold.co/1200x600?text=0105+AI+News'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🌟</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>プログラム概要</h3>
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
          {"".join([f'<img src="../../input/day/0105_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🌟 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2026_01_05.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0105()
