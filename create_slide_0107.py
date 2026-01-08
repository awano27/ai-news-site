import re
from pathlib import Path
import json
import os
import glob

def create_slide_0107():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月7日"
    date_slash = "2026/01/07"

    # Define content variables
    short_title = "NVIDIA Rubin"
    main_title = "NVIDIA Rubin AIプラットフォーム: AIファクトリーの再定義"
    subtitle = "Blackwellの後継としてCES 2026で発表された次世代AIプラットフォームの全貌"

    # CSS Variables (NVIDIA tech theme - green & black)
    css_vars = """
    :root {
      --primary: #76b900;
      --accent: #1E5128;
      --bg-light: #f0f8f0;
      --bg-dark: #0f1419;
      --text: #0f1419;
      --text-light: #6b7280;
      --border: #c8e6c9;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #76b900, #1E5128); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(118, 185, 0, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            年次リリースサイクルを維持する次世代AIプラットフォーム
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            NVIDIAはCES 2026において、Blackwellアーキテクチャの後継となる次世代AIプラットフォーム「Rubin」を発表しました。6種類の新チップを統合し、エージェント型AI、長文脈推論、MoEモデルといった次世代AIワークロードに最適化された単一のAIスーパーコンピュータとして機能します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">⚡</span>
            性能向上の概要
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>推論性能: 最大5倍</strong> - Blackwell比で次世代AIモデルの推論処理速度を大幅向上</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>トレーニング性能: 最大3.5倍</strong> - 大規模モデルの学習効率を劇的に改善</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>コスト削減: 1/10</strong> - 推論トークンコストを最大10分の1に削減</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">4</span>
                <span><strong>MoE GPU削減: 1/4</strong> - 混合専門家モデルのトレーニングに必要なGPU数を4分の1に削減</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🔗</span>
            <div class="feature-title">6チップ統合</div>
            <div class="feature-desc">Vera CPU、Rubin GPUを含む6種類の新チップを単一システムとして統合</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🏢</span>
            <div class="feature-title">ラック規模の最適化</div>
            <div class="feature-desc">計算、ネットワーキング、ストレージを単一ユニットとして最適化</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <div class="feature-title">次世代AIワークロード</div>
            <div class="feature-desc">エージェント型AI、長文脈推論、MoEモデルに特化した設計</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>市場展開とパートナーシップ</h4>
        <p>発表時点で既に<strong>完全生産体制（in full production）</strong>にあることが明言されており、Microsoft、CoreWeaveを含む主要なクラウドプロバイダーやAIラボが初期導入パートナーとして名を連ねています。Canonical、Red Hat、SUSEなどのエンタープライズLinuxパートナーも最適化されたサポートを表明しており、AIインフラ市場におけるNVIDIAの支配的地位をさらに強固にするものと見られています。パートナー企業によるRubinベースのシステムは、<strong>2026年後半に出荷が開始される予定</strong>です。</p>
    </div>

    <div class="card">
        <h4>戦略的焦点: システム全体のバランス</h4>
        <p>Rubinの戦略的焦点は、単なる計算能力の向上だけでなく、システム全体のバランスと効率を重視することにあります。これは、長文脈を理解し、複数の行動を調整するような、より高度な「思考する」AIの需要に応えるためです。プラットフォームは、計算、ネットワーキング、ストレージを単一のユニットとして扱うラック規模の統合を実現し、最先端AIの構築と展開にかかるコストを大幅に削減することを目標としています。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0107_slides"
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
        <img src="../../input/day/0107.png" alt="01/07 Visual" onerror="this.src='https://placehold.co/1200x600?text=0107+AI+News'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🚀</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>性能向上の詳細</h3>
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
          {"".join([f'<img src="../../input/day/0107_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
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
    output_path = f"presentations/day_slides/day_slide_2026_01_07.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0107()
