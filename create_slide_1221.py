import re
from pathlib import Path
import json

def create_slide_1221():
    # Load base_template.html
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-21
    date_jp = "2025年12月21日"
    date_slash = "2025/12/21"
    
    # Define content variables
    short_title = "FunctionGemma" 
    main_title = "FunctionGemma：実用的なオンデバイスAIエージェントの夜明け"
    subtitle = "Google発表、2.7億パラメータの超軽量モデルが「思考」を即座に「行動」へ変える"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #0f9d58, #0b8043); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            AIは「応答」から「実行」のフェーズへ
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            Googleが公開したFunctionGemmaは、API呼び出し（ツール利用）に特化した2.7億パラメータの超小型モデルです。スマートフォン上での完全オフライン動作と、人間の読解速度を超える圧倒的な応答性能を両立します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🚀</span>
            戦略的な3つの核心価値
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>完全なプライバシー</strong>: データがデバイスの外に出ず、オフラインで動作可能。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>ゼロレイテンシ</strong>: 最初の応答まで0.3秒。クラウド通信不要で物理的遅延を克服。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>ミドルウェア税の撤廃</strong>: 単純タスクでのクラウドAI依存を排除し、運用コストを劇的に削減。</span>
            </li>
        </ul>
    </div>
    """

    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">驚異のパフォーマンス</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>出力速度：毎秒125.9 トークン</li>
                <li>RAM使用量：わずか 550 MB</li>
                <li>ファイルサイズ：288 MB</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">特化型の設計思想</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>関数呼び出し（ツール利用）に特化</li>
                <li>ファインチューニング前提の設計</li>
                <li>堅牢なエスケープ機構（<escape>トークン）</li>
            </ul>
        </div>
    </div>
    """

    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: #0f9d58; color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem; color: white;">展望：エッジAIが拓く実務の自律化</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">ファインチューニングによる高精度化</h4>
                <p style="margin: 0; color: var(--text-light);">特定の業務に特化させることで、正解率が10%から80%へ劇的に向上する事例も報告されています。</p>
            </div>
            <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">エンジニアの必須スキルへ</h4>
                <p style="margin: 0; color: var(--text-light);">モデルの「規模」から「技能（スキル）」への転換。特定ユースケースに最適化する開発力が差別化要因になります。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト
    slides_list = []
    slide_dir = Path(f"input/day/1221_slides")
    if slide_dir.exists():
        count = len(list(slide_dir.glob("slide_*.jpg")))
        for i in range(1, count + 1):
            slides_list.append(f'<img src="../../input/day/1221_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    else:
        slides_list.append('<p style="text-align: center; color: var(--text-light);">スライド画像がまだ準備されていません。</p>')
    
    slides_html = "\n".join(slides_list)
    
    # 配色設定 (Gemma Green theme)
    css_vars_block = """
    :root {
      --primary: #0f9d58;
      --accent: #34a853;
      --accent2: #188038;
      --bg-dark: #202124;
      --bg-light: #f8f9fa;
      --border: #dadce0;
      --text: #202124;
      --text-light: #5f6368;
      --tron-black: #000000;
    }
    header {
        background: linear-gradient(135deg, #0f9d58 0%, #34a853 100%);
    }
    h3::before {
        background: var(--primary);
    }
    .section-header {
        border-bottom: 3px solid var(--primary);
    }
    """
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 (TODO: ファイル配置後にリンク) -->')
    content_parts.append('  <div class="top-image-container">')
    content_parts.append('    <img src="../../input/day/1221.jpg" alt="Agentic AI Foundation Visual" onerror="this.src=\'https://via.placeholder.com/1200x600?text=1221+Agentic+AI+Foundation\'">')
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🔗</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>業界横断の標準化イニシアチブ</h3>')
    content_parts.append(highlight_box)
    content_parts.append(feature_grid)
    content_parts.append(detail_card)
    content_parts.append('  </section>')
  
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">📖</span>')
    content_parts.append('      <h2>スライド資料 (全ページ)</h2>')
    content_parts.append('    </div>')
    content_parts.append('    <div class="slides-container">')
    content_parts.append(slides_html)
    content_parts.append('    </div>')
    content_parts.append('  </section>')
    content_parts.append('</main>')

    main_content_html = "\n".join(content_parts)

    # プレースホルダーを置換
    html = template_html_content.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    html = html.replace("{{CSS_VARS_BLOCK}}", css_vars_block)
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}最新動向 | {short_title}")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_21.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    import os
    create_slide_1221()
