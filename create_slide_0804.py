import re
from pathlib import Path
import json
import os

def create_slide_0804():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年8月4日"
    date_slash = "2025/08/04"
    
    # Define content variables
    short_title = "MLE-STAR" 
    main_title = "Google Research: MLE-STAR"
    subtitle = "MLエンジニアリングを自動化するエージェント"

    # CSS Variables for "Google Research" theme (Blue/Yellow/Grey)
    css_vars = """
    :root {
      --primary: #4285f4;
      --accent: #fbbc04;
      --bg-light: #f8f9fa;
      --bg-dark: #202124;
      --text: #e8eaed;
      --text-light: #bdc1c6;
      --border: #5f6368;
      --tron-black: #000a12;
    }
    body {
        background: linear-gradient(135deg, #202124 0%, #3c4043 100%);
    }
    .container {
        background: rgba(32, 33, 36, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid var(--primary);
    }
    .card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--border);
    }
    .feature-item {
        background: rgba(255, 255, 255, 0.05);
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #174ea6, #202124); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; border: 1px solid var(--primary); box-shadow: 0 0 15px rgba(66, 133, 244, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em; text-shadow: 0 0 5px var(--primary);">
            MLエンジニアリングの自律化
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6; color: var(--text);">
            Google Researchが発表した「MLE-STAR」は、機械学習エンジニアリング専用のエージェントです。Web検索、コード生成、標的的リファイン、アンサンブル自動化を組み合わせ、Kaggleレベルのタスクで高いパフォーマンスを発揮します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: rgba(0, 0, 0, 0.3); border: 1px solid var(--accent); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--accent); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🛠️</span>
            エンジニアのための3つの武器
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>Agent Development Kit (ADK)</strong>: `pip install google-adk` で即導入可能。公式サンプルも充実。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>高性能ベンチマーク</strong>: MLE-Bench-Liteで63%のメダル獲得率。実務レベルのタスク解決能力。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>初期モデル構築の自動化</strong>: 要件定義から初期コード生成、検証ループまでを短縮し、PoCを加速。</span>
            </li>
        </ul>
    </div>
    """

    # Code Snippet Content
    code_snippet = """
    <div style="background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 16px; margin-bottom: 32px; font-family: 'Fira Code', monospace; overflow-x: auto;">
        <div style="color: #808080; margin-bottom: 8px;">// Quickstart with Google ADK</div>
        <div style="color: #d4d4d4;">
            <span style="color: #6a9955;"># 1. Install ADK</span><br>
            <span style="color: #ce9178;">pip install google-adk</span><br><br>
            <span style="color: #6a9955;"># 2. Clone Samples (MLE-STAR)</span><br>
            <span style="color: #ce9178;">git clone https://github.com/google/adk-samples</span><br>
            <span style="color: #ce9178;">cd adk-samples/python/agents/machine-learning-engineering</span><br><br>
            <span style="color: #6a9955;"># 3. Run Agent (after config)</span><br>
            <span style="color: #ce9178;">python main.py --task "Predict customer churn using xgboost"</span>
        </div>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">🤖</span>
            <div class="feature-title" style="color: var(--accent);">Targeted Refinement</div>
            <div class="feature-desc">アブレーションスタディで重要なブロックを特定し、集中的に改善。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">🔄</span>
            <div class="feature-title" style="color: var(--accent);">Auto Ensemble</div>
            <div class="feature-desc">複数のモデルを自動的に組み合わせ、予測精度を最大化。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">📦</span>
            <div class="feature-title" style="color: var(--accent);">ADK Integration</div>
            <div class="feature-desc">GoogleのAgent Development Kitと統合され、拡張性と再利用性が高い。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4 style="color: var(--accent);">ビジネスインパクト</h4>
        <p>「とりあえずモデルを作ってみる」コストが激減します。需要予測や分類タスクなどの非クリティカルな領域で、MLE-STARに初期モデルを作成させることで、データサイエンティストはより高度な課題解決に集中できます。</p>
    </div>
    """

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="https://placehold.co/1200x600/202124/4285f4?text=MLE-STAR+Agent" alt="MLE-STAR Agent Visual" onerror="this.src='https://placehold.co/1200x600/202124/4285f4?text=MLE-STAR+Agent'">
      </div>
      <section class="section">
        <div class="section-header" style="border-bottom-color: var(--accent);">
          <span class="section-icon">🌌</span>
          <h2 style="color: var(--text);">{short_title}</h2>
        </div>
        {intro_box}
        <h3 style="color: var(--text);">Quick Start Guide</h3>
        {code_snippet}
        {highlight_box}
        {feature_grid}
        {detail_cards}
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🚀 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2025_08_04.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0804()
