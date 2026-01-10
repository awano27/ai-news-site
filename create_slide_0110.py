import re
from pathlib import Path
import json
import os
import glob

def create_slide_0110():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月10日"
    date_slash = "2026/01/10"

    # Define content variables
    short_title = "CES 2026 Physical AI"
    main_title = "CES 2026: Physical AIへのパラダイムシフト"
    subtitle = "AIが画面から飛び出し、物理世界でタスクを実行する時代の幕開け"

    # CSS Variables (CES/Tech theme - electric blue & cyan)
    css_vars = """
    :root {
      --primary: #0ea5e9;
      --accent: #06b6d4;
      --bg-light: #f0f9ff;
      --bg-dark: #0c4a6e;
      --text: #0f172a;
      --text-light: #6b7280;
      --border: #bae6fd;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            AIが物理世界へ飛び出した「Physical AI」の時代
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            CES 2026（2026年1月6日〜9日、ラスベガス）は約4,100社が出展、14万8,000人以上が来場した世界最大級の技術見本市。今年の決定的な特徴は、AIがチャットボットや画像生成からロボットや自動車などの「身体」を持って現実世界でタスクを実行する段階へ移行したことです。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🔑</span>
            CES 2026 主要トピック
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>Physical AIへのシフト</strong> - 物理法則を理解し、現実世界でタスクを実行するAI</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>ロボットが労働力へ</strong> - ヒューマノイドロボットの具体的導入計画が発表</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>AI PC競争激化</strong> - Intel vs AMD、オンデバイスAIが標準化</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">4</span>
                <span><strong>新フォームファクタ</strong> - 3つ折りスマホ、ローラブルPCなど</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">5</span>
                <span><strong>課題: AI疲れ</strong> - 実用性のないAI機能への反発も</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <div class="feature-title">NVIDIA Vera Rubin</div>
            <div class="feature-desc">前世代比5倍の推論性能、コスト劇的削減でAIインフラを強化</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🦾</span>
            <div class="feature-title">Atlas Robot</div>
            <div class="feature-desc">Hyundai×Boston Dynamics、2028年から自動車工場へ本格導入</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">💻</span>
            <div class="feature-title">AI PC時代</div>
            <div class="feature-desc">Intel Core Ultra Series 3 vs AMD Ryzen AI 400、NPU競争激化</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>NVIDIAの支配とPhysical AI</h4>
        <p>ジェンスン・フアンCEOは「Physical AI」の概念を強く提唱し、次世代プラットフォーム<strong>「Vera Rubin」</strong>を発表。前世代比5倍の推論性能を持ちながらコストを劇的に下げ、AIを「動かす」ためのインフラ整備を加速させています。物理法則を理解し、ロボットや自動車などの「身体」を持って現実世界でタスクを実行するAIが現実のものとなりました。</p>
    </div>

    <div class="card">
        <h4>ロボットが「デモ」から「労働力」へ</h4>
        <p>ヒューマノイドロボットは単なる見世物ではなく、具体的な導入計画が語られるフェーズに入りました。<strong>HyundaiとBoston Dynamics</strong>は新型「Atlas」ロボットを発表。Google DeepMindのAIを統合し、<strong>2028年から自動車工場へ本格導入</strong>される計画です。現場でタスクを学習・実行する能力を備えています。</p>
    </div>

    <div class="card">
        <h4>新フォームファクタとヘルスケアの進化</h4>
        <p>Samsungの3つ折りスマホ<strong>「Galaxy Z TriFold」</strong>や、Lenovoのローラブル（画面が伸びる）PCなど、AIによるマルチタスクを前提としたデバイスが登場。ヘルスケアはスマートウォッチから<strong>体液分析</strong>へと深化し、スマートトイレや尿検査デバイスで生活導線の中で健康データを取得する流れが強まりました。</p>
    </div>

    <div class="card">
        <h4>課題：「AI疲れ」とエネルギー問題</h4>
        <p>一方で、実用性のないAI機能への反発も起きています。SamsungのAI冷蔵庫が消費者団体から<strong>「最悪の製品」</strong>と評されるなど、単にAIを搭載するだけでは評価されない時代になりました。また、AIの大規模化に伴う<strong>電力消費の増大</strong>も大きな議論のテーマとなっています。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0110_slides"
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
        <img src="../../input/day/0110.png" alt="01/10 Visual" onerror="this.src='https://placehold.co/1200x600?text=0110+AI+News'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🌐</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>主要トピック</h3>
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
          {"".join([f'<img src="../../input/day/0110_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{main_title} - {date_slash}")
    # Fix broken CSS_VARS_BLOCK placeholder (it's split across multiple lines in the template)
    final_html = re.sub(r'\{\s*\{\s*CSS_VARS_BLOCK\s*\}\s*\}', css_vars, final_html)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🌐 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2026_01_10.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0110()
