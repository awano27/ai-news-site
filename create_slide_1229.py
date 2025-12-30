import re
from pathlib import Path
import json
import os

def create_slide_1229():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年12月29日"
    date_slash = "2025/12/29"
    
    # Define content variables
    short_title = "Defining The AI World" 
    main_title = "Structural Hallucination Prevention"
    subtitle = "Model-First Reasoningによる信頼性の向上"

    # CSS Variables for "Structure/Logic" theme (Blue/Teal/Grey)
    css_vars = """
    :root {
      --primary: #006064;
      --accent: #00bcd4;
      --bg-light: #e0f7fa;
      --bg-dark: #00363a;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
      --border: #b2ebf2;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #006064, #00838f); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            ハルシネーションを防ぐ構造的アプローチ
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            LLMにまず明示的な問題モデルを構築させる「Model-First Reasoning」により、計画の信頼性が飛躍的に向上します。タスクのルールを事前に定義することで、一貫性のある検証可能な計画が可能になります。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">📐</span>
            Model-First Reasoningの利点
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>明示的な問題定義</strong>: 計画前に「何が存在し、何が許可されるか」をリストアップ。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>表現と推論の分離</strong>: 長期的なドリフトを減らし、隠れた仮定の発明（ハルシネーション）を防ぐ。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>高い検証可能性</strong>: Chain-of-ThoughtやReActと比較して、より安定した計画を生成。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🧩</span>
            <div class="feature-title">適用分野</div>
            <div class="feature-desc">スケジューリング、ルーティング、リソース割り当て、ロジックパズル等で効果を発揮。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🛡️</span>
            <div class="feature-title">制約遵守</div>
            <div class="feature-desc">制約違反が減少し、より明確な構造を持つ計画が作成される。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📄</span>
            <div class="feature-title">論文情報</div>
            <div class="feature-desc">arXiv:2512.14474 "Model-First Reasoning LLM Agents"</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>核心の主張</h4>
        <p>多くのハルシネーションは「表現のエラー」に起因します。最初に問題を明示的にモデル化することで、これらのエラーを根本から防ぐことができます。</p>
    </div>

    <div class="card">
        <h4>実装アプローチ</h4>
        <p>シンプルなプロンプトで実装可能であり、複雑なアーキテクチャ変更を必要とせずに、エージェントの信頼性を向上させる実用的な手法です。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/1229_slides"
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
        <img src="../../input/day/1229.jpg" alt="Defining The AI World Visual" onerror="this.src='https://placehold.co/1200x600?text=1229+Defining+The+AI+World'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🏗️</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>構造的ハルシネーション防止</h3>
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
          {"".join([f'<img src="../../input/day/1229_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🏗️ {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2025_12_29.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1229()
