import re
from pathlib import Path
import json
import os

def create_slide_1228():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年12月28日"
    date_slash = "2025/12/28"
    
    # Define content variables
    short_title = "Code Is Written" 
    main_title = "While You Sleep"
    subtitle = "自律型コーディングAIの新たな地平"

    # CSS Variables for "Night Coding" theme (Dark Blue/Purple)
    css_vars = """
    :root {
      --primary: #311b92;
      --accent: #7c4dff;
      --bg-light: #ede7f6;
      --bg-dark: #12005e;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
      --border: #d1c4e9;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #311b92, #4527a0); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            眠っている間に進化するソフトウェア
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            AIエージェントが24時間体制でコードを書き、テストし、デプロイする時代が到来しました。「Code Is Written While You Sleep」は、開発プロセスの完全自動化がもたらすインパクトと、エンジニアの役割の変化について詳述します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🌙</span>
            常時稼働開発のメリット
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>開発サイクルの短縮</strong>: 人間の休息中も開発が進行し、リードタイムが劇的に短縮。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>バグ修正の迅速化</strong>: 継続的なテストと修正により、品質が向上。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>リソースの最適化</strong>: 人間は創造的なタスクに集中し、ルーチンワークはAIが担当。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <div class="feature-title">自律エージェント</div>
            <div class="feature-desc">要件定義から実装までを自律的に行うAIエージェント。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔄</span>
            <div class="feature-title">CI/CD統合</div>
            <div class="feature-desc">既存のパイプラインにシームレスに統合されるAIワークフロー。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📈</span>
            <div class="feature-title">生産性向上</div>
            <div class="feature-desc">開発チーム全体の生産性を飛躍的に向上させる。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>パラダイムシフト</h4>
        <p>「コードを書く」という行為自体が、人間からAIへと移行しつつあります。エンジニアはコードの書き手から、AIエージェントの監督者、アーキテクトへと役割を変えていく必要があります。</p>
    </div>

    <div class="card">
        <h4>未来の展望</h4>
        <p>この技術はまだ始まったばかりですが、その可能性は無限大です。将来的には、複雑なシステム全体を一晩で構築することも可能になるかもしれません。</p>
    </div>
    """

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/1228.jpg" alt="Code Is Written While You Sleep Visual" onerror="this.src='https://placehold.co/1200x600?text=1228+Code+Is+Written'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">💤</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>24時間開発体制の実現</h3>
        {highlight_box}
        {feature_grid}
        {detail_cards}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全14ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/1228_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, 15)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🌙 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2025_12_28.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1228()
