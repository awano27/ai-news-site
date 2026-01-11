import re
from pathlib import Path
import json
import os
import glob

def create_slide_0111():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables
    date_jp = "2026年1月11日"
    date_slash = "2026/01/11"

    # Define content variables
    short_title = "MiroThinker v1.5"
    main_title = "MiroThinker: AIスケーリングの「第3の軸」へ"
    subtitle = "インタラクティブ・スケーリングが切り拓く、オープンソース・リサーチエージェントの新時代"

    # CSS Variables (MiroMind theme - teal & dark blue)
    css_vars = """
    :root {
      --primary: #0d9488;
      --accent: #134e4a;
      --bg-light: #f0fdfa;
      --bg-dark: #042f2e;
      --text: #0f172a;
      --text-light: #6b7280;
      --border: #99f6e4;
      --tron-black: #000000;
    }
    """

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #0d9488, #134e4a); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(13, 148, 136, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            30Bパラメータの「小さな巨人」が1Tモデルに匹敵する理由
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            MiroMindがリリースしたMiroThinker v1.5は、従来の「モデルサイズ」「コンテキスト長」に続く第3の軸「インタラクティブ・スケーリング」を提唱。AIは思考の長さ（CoT）だけでなく、環境との試行錯誤（Action）の回数で賢くなります。GAIAベンチマークで80.8%、BrowseCompで69.8%を記録し、GPT-5級の商用モデルに肉薄しています。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🔑</span>
            MiroThinker v1.5 の特徴
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>GAIA 80.8%</strong> - GPT-5級の商用モデルに肉薄するベンチマーク結果</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>コスト1/20</strong> - エンタープライズ向けDeep Researchツールの約1/20で運用可能</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>256Kトークン</strong> - 大規模なコンテキストウィンドウでDeep Diveが可能</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">4</span>
                <span><strong>MITライセンス</strong> - オープンソースでローカル実行可能（ただしAPI依存あり）</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div class="feature-grid">
        <div class="feature-item">
            <span class="feature-icon">🔄</span>
            <div class="feature-title">インタラクティブ・スケーリング</div>
            <div class="feature-desc">仮説→ツール実行→観察→修正のループで、行動するほど賢くなる</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔍</span>
            <div class="feature-title">Dynamic Research Agent</div>
            <div class="feature-desc">「記憶」するAIから「調査」するAIへ。答えを見つける方法を知っている</div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔗</span>
            <div class="feature-title">MCP対応</div>
            <div class="feature-desc">Model Context Protocolで検索・コンテンツ・実行ツールを標準化</div>
        </div>
    </div>
    """

    # Detail Cards Content
    detail_cards = """
    <div class="card accent">
        <h4>3段階のトレーニングパイプライン</h4>
        <p>MiroThinkerは<strong>Agentic SFT → DPO → Agentic RL (GRPO)</strong>の3段階で訓練されています。専門家の行動軌跡（Trajectory）を模倣学習し、正解への道筋を整列させ、大規模な試行錯誤（Rollout）による「粘り強さ」と「探索能力」を獲得。時間的感受性トレーニングにより、未来情報のリーク（予測タスクでのカンニング）を防止しています。</p>
    </div>

    <div class="card">
        <h4>ベンチマーク：巨人殺しの証明</h4>
        <p>パラメータ数が少なくても、インタラクションの質と量で「賢さ」は逆転します。<strong>GAIA 80.8%</strong>（GPT-5 level）、<strong>BrowseComp 69.8%</strong>（オープンソーストップクラス）、<strong>HLE 39.2%</strong>（1Tモデル級の推論能力）を達成。ツール呼び出し回数が増えるほど精度が向上し、Step 50で75.0%に到達します。</p>
    </div>

    <div class="card">
        <h4>「完全オープンソース」の落とし穴</h4>
        <p>モデルとコードはMITライセンスでローカル実行可能ですが、推奨される最小構成には<strong>商用API（Serper、E2B、Jina）が必要</strong>です。検索結果や実行環境が外部サービスに依存するため、完全な監査や再現性の担保が難しい場合があります。導入前にAPIコストの試算と依存サービスのSLA確認が必須です。</p>
    </div>

    <div class="card">
        <h4>リサーチAI競合比較</h4>
        <p><strong>MiroThinker v1.5</strong>：検証の深さ、透明性（ログ）、カスタマイズ性が強み。技術調査、複雑な裏取り、社内データ統合に最適。<strong>OpenAI/Gemini Deep Research</strong>：セットアップ不要、UI体験、一般知識が強み。<strong>Perplexity</strong>：速さとニュース検索が強み。用途に応じた使い分けが重要です。</p>
    </div>
    """

    # Count slides
    slide_dir = "input/day/0111_slides"
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
        <img src="../../input/day/0111.png" alt="01/11 Visual" onerror="this.src='https://placehold.co/1200x600?text=0111+AI+News'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🧠</span>
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
          {"".join([f'<img src="../../input/day/0111_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
        </div>
      </section>
    </main>
    """

    # Replace placeholders in template
    final_html = template_html_content
    final_html = final_html.replace("{{FULL_TITLE}}", f"{main_title} - {date_slash}")
    # Fix broken CSS_VARS_BLOCK placeholder (it's split across multiple lines in the template)
    final_html = re.sub(r'\{\s*\{\s*CSS_VARS_BLOCK\s*\}\s*\}', css_vars, final_html)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"🧠 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # Write output file
    output_path = f"presentations/day_slides/day_slide_2026_01_11.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_0111()
