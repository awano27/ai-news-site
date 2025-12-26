import os
from pathlib import Path

def create_slide_1226():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Content for 12/26
    today_str = "2025-12-26"
    date_slash = "2025/12/26"
    title = "AIPO: Autonomous Project Owner — AI時代の新・意思決定"
    short_title = "AIPO: Autonomous Project Owner"
    
    # CSS Variables for "AIPO Deep Blue" theme
    css_vars = """
    :root {
      --primary: #004aad;
      --accent: #00c2cb;
      --bg-light: #f0f7ff;
      --bg-dark: #001a33;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
      --border: #cce0ff;
      --tron-black: #000a12;
    }
    """

    intro_box = f"""
    <div style="background: linear-gradient(135deg, var(--bg-dark), #003366); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; border: 1px solid var(--accent); box-shadow: 0 0 20px rgba(0, 194, 203, 0.2);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; color: var(--accent);">自律型意思決定の夜明け</p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            単なる「生成」から「所有（Ownership）」へ。AIPOは、プロジェクトの要件定義からリソース管理、最終的な成果物の品質保証までを自律的に担う、次世代のAI役割（ロール）です。
        </p>
    </div>
    """

    highlight_box = f"""
    <div class="highlight-box">
      <strong>エンジニアリングの終焉ではなく、進化:</strong> AIが「何を作るか」だけでなく「なぜ作るか」「どう進めるか」を自律的に判断。人間の役割は、AIPOが提示する戦略の最終承認と、ハイレベルなアーキテクチャ設計へとシフトします。
    </div>
    """

    feature_grid = """
    <div class="feature-grid">
      <div class="feature-item">
        <span class="feature-icon">🛡️</span>
        <div class="feature-title">Ownership</div>
        <div class="feature-desc">プロジェクトのKPIに責任を持ち、自らタスクを生成・割り当てます。</div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">⚡</span>
        <div class="feature-title">Real-time Pivot</div>
        <div class="feature-desc">市場や技術の変化を即座に検知し、ロードマップを動的に書き換えます。</div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">🔍</span>
        <div class="feature-title">Validation</div>
        <div class="feature-desc">自らテストコードを書き、要件を満たしているかを厳格に検証します。</div>
      </div>
    </div>
    """

    detail_cards = f"""
    <div class="card accent">
      <h4>AIPOがもたらすビジネスインパクト</h4>
      <p>意思決定のボトルネックを解消し、プロダクトの開発速度を10倍以上に加速させます。AIがプロジェクトの文脈を完全に把握することで、コミュニケーションコストが最小化され、創造的な課題解決に集中できる環境を構築します。</p>
    </div>
    """

    # Assemble Main Content (14 pages)
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/1226.jpg" alt="AIPO Visual" onerror="this.src='https://placehold.co/1200x600?text=1226+AIPO+Autonomous+Project+Owner'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🧠</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>自律型プロジェクト管理の衝撃</h3>
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
          {"".join([f'<img src="../../input/day/1226_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, 15)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders
    html_content = template_html_content.replace("{{ CSS_VARS_BLOCK }}", css_vars)
    html_content = html_content.replace("{ { CSS_VARS_BLOCK } }", css_vars) # Handle potential double spacing
    html_content = html_content.replace("{{ TITLE }}", title)
    html_content = html_content.replace("{{ DATE }}", date_slash)
    html_content = html_content.replace("{{ BREAKING_BADGE }}", f"🚀 {date_slash} レポート | {short_title}")
    html_content = html_content.replace("{{ SUBTITLE }}", "自律型プロジェクトオーナーによる意思決定の自動化")
    html_content = html_content.replace("{{ MAIN_CONTENT }}", main_content)

    # Output path
    output_filename = f"day_slide_{today_str.replace('-', '_')}.html"
    output_path = os.path.join("presentations", "day_slides", output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1226()
