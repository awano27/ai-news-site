import re
from pathlib import Path
import json
import os
import glob

def create_slide_0109():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月9日"
    date_slash = "2026/01/09"

    # Define content variables
    short_title = "NousCoder-14B"
    main_title = "NousCoder-14B: 4日間でExpertレベルに到達したオープンソースコード生成AI"
    subtitle = "NousResearchが放つ、Apache 2.0ライセンスの競技プログラミング特化モデル"

    # CSS Variables (NousResearch theme - purple & blue)
    css_vars = """
    :root {
      --primary: #6366f1;
      --accent: #8b5cf6;
      --bg-light: #f5f3ff;
      --bg-dark: #1e1b4b;
      --text: #0f172a;
      --text-light: #6b7280;
      --border: #c7d2fe;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            わずか4日間の訓練で競技プログラミングExpertレベルに到達
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            NousResearchがリリースしたNousCoder-14Bは、オープンソースコード生成AIの新たなマイルストーンです。強化学習と検証可能報酬の組み合わせにより、驚異的な速度で高性能を達成。Apache 2.0ライセンスでローカル実行可能なため、PHI（保護対象保健情報）を外部に送信せずに高性能なコード生成を利用できます。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">⚡</span>
            主な特徴
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>競技プログラミングExpertレベル</strong> - わずか4日間の訓練で到達</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>Apache 2.0ライセンス</strong> - 商用利用可能なオープンソース</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>ローカル実行可能</strong> - RTX 4090でQ4_K_M量子化版が動作</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">4</span>
                <span><strong>強化学習 + 検証可能報酬</strong> - 革新的な訓練手法</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🔒</span>
            <div class="feature-title">PHI保護</div>
            <div class="feature-desc">外部サービスに依存せず、保護対象保健情報を外部送信なしでコード生成</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🏆</span>
            <div class="feature-title">競プロ特化</div>
            <div class="feature-desc">アルゴリズム実装、テストコード生成に強み</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">💻</span>
            <div class="feature-title">Ollama対応</div>
            <div class="feature-desc">量子化版をOllamaで簡単にローカル起動可能</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>医療IT開発者への価値</h4>
        <p>医療IT開発者にとっての最大の価値は、<strong>Apache 2.0ライセンス + ローカル実行可能</strong>という組み合わせです。Claude CodeやGitHub Copilotのような商用サービスに依存せず、PHI（保護対象保健情報）を外部に送信することなく、高性能なコード生成を利用できます。セキュリティとプライバシーを重視する医療分野において、この特性は非常に重要です。</p>
    </div>

    <div class="card">
        <h4>導入時の注意点</h4>
        <p>競技プログラミング特化という性質上、<strong>汎用的なソフトウェア開発への適用は慎重に評価すべき</strong>です。まずはローカル環境でテスト評価を行い、自組織のユースケースでの性能を検証してから本番導入を検討することを推奨します。競プロ特化の強みが活かせる領域（アルゴリズム実装、テストコード生成）から段階的に適用範囲を広げていくのが効果的です。</p>
    </div>

    <div class="card">
        <h4>今すぐ始められること</h4>
        <p><strong>RTX 4090環境でQ4_K_M量子化版をOllamaで起動</strong>し、実際の開発タスクで試用できます。競プロ特化の強みが活かせる領域（アルゴリズム実装、テストコード生成）から段階的に適用範囲を広げていくことで、NousCoder-14Bの真価を体験できます。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0109_slides"
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
        <img src="../../input/day/0109.png" alt="01/09 Visual" onerror="this.src='https://placehold.co/1200x600?text=0109+AI+News'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🚀</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>主な特徴</h3>
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
          {"".join([f'<img src="../../input/day/0109_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🚀 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2026_01_09.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0109()
