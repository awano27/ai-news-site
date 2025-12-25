import re
from pathlib import Path
import json
import os

def create_slide_0801():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2025年8月1日"
    date_slash = "2025/08/01"
    
    # Define content variables
    short_title = "Gemini 2.5 Deep Think" 
    main_title = "Google: Gemini 2.5 Deep Think"
    subtitle = "並列思考で「正解」を導き出す、新たな推論モデル"

    # CSS Variables for "Gemini Blue" theme
    css_vars = """
    :root {
      --primary: #1976d2;
      --accent: #4fc3f7;
      --bg-light: #e3f2fd;
      --bg-dark: #0d47a1;
      --text: #e1f5fe;
      --text-light: #b3e5fc;
      --border: #2196f3;
      --tron-black: #000a12;
    }
    body {
        background: linear-gradient(135deg, #000a12 0%, #0d47a1 100%);
    }
    .container {
        background: rgba(13, 71, 161, 0.8);
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
    <div style="background: linear-gradient(135deg, #0d47a1, #000a12); color: var(--accent); padding: 24px; border-radius: 16px; margin-bottom: 32px; border: 1px solid var(--primary); box-shadow: 0 0 15px rgba(25, 118, 210, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em; text-shadow: 0 0 5px var(--primary);">
            思考の深淵へ：Gemini 2.5 Deep Think
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6; color: var(--text);">
            Googleは、複数の仮説を並列に検討し、最良の解を導き出す推論モデル「Gemini 2.5 Deep Think」を一般公開しました。数学、コーディング、複雑な仕様検討において、圧倒的な正答率と論理的深さを提供します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: rgba(0, 0, 0, 0.3); border: 1px solid var(--accent); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--accent); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🧠</span>
            エンジニアのための3つの進化
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>並列思考プロセス</strong>: 複数のアプローチを同時にシミュレーションし、最適な設計案やアルゴリズムを選択。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>100万トークン対応</strong>: 大規模なコードベースや複雑な要件定義書を丸ごと読み込み、矛盾やバグを特定。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>即日検証可能</strong>: Geminiアプリ（AI Ultra）で今すぐ利用可能。API連携前のPoCに最適。</span>
            </li>
        </ul>
    </div>
    """

    # Code Snippet Content
    code_snippet = """
    <div style="background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 16px; margin-bottom: 32px; font-family: 'Fira Code', monospace; overflow-x: auto;">
        <div style="color: #808080; margin-bottom: 8px;">// Prompt Example: Parallel Reasoning for Architecture Design</div>
        <div style="color: #d4d4d4;">
            <span style="color: #ce9178;">"以下の2000行の要件定義書から、競合する制約条件を抽出せよ。<br>
            その後、3つの異なるアーキテクチャ設計案（モノリス、マイクロサービス、サーバーレス）を並列に検討し、<br>
            それぞれのメリット・デメリット、およびこのプロジェクトに最適な案を論理的根拠とともに提示せよ。"</span>
        </div>
        <div style="color: #569cd6; margin-top: 12px;">
            -> Output: <span style="color: #4fc3f7;">[Deep Think Process]</span><br>
            1. Analyzing constraints... (Latency vs Consistency)<br>
            2. Simulating Monolith scaling... (Failed at peak load)<br>
            3. Evaluating Serverless cost... (Optimal for sporadic traffic)<br>
            4. <strong>Recommendation: Serverless with Event-Driven Architecture</strong>
        </div>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">💎</span>
            <div class="feature-title" style="color: var(--accent);">Deep Reasoning</div>
            <div class="feature-desc">「直感」ではなく「論理」で答える。数学的難問や複雑なロジックに特化。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">📚</span>
            <div class="feature-title" style="color: var(--accent);">Huge Context</div>
            <div class="feature-desc">1Mトークンの文脈保持。プロジェクト全体の文脈を理解した上での提案。</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon" style="filter: drop-shadow(0 0 5px var(--accent));">⚡</span>
            <div class="feature-title" style="color: var(--accent);">Instant PoC</div>
            <div class="feature-desc">環境構築不要。アプリを開くだけで、最先端の推論エンジンをテスト可能。</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4 style="color: var(--accent);">ビジネスインパクト</h4>
        <p>意思決定の質とスピードを劇的に向上させます。複雑なトレードオフが存在するビジネス課題に対して、Deep Thinkは複数のシナリオをシミュレーションし、リスクとリターンを整理した上で「最善の一手」を提案します。これは、あなた専用の優秀な戦略コンサルタントです。</p>
    </div>
    """

    # Assemble Main Content
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="https://placehold.co/1200x600/0d47a1/4fc3f7?text=Gemini+2.5+Deep+Think" alt="Gemini 2.5 Deep Think Visual" onerror="this.src='https://placehold.co/1200x600/0d47a1/4fc3f7?text=Gemini+2.5+Deep+Think'">
      </div>
      <section class="section">
        <div class="section-header" style="border-bottom-color: var(--accent);">
          <span class="section-icon">🌌</span>
          <h2 style="color: var(--text);">{short_title}</h2>
        </div>
        {intro_box}
        <h3 style="color: var(--text);">Reasoning in Action</h3>
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
    output_path = f"presentations/day_slides/day_slide_2025_08_01.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0801()
