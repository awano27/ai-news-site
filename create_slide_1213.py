import re
from pathlib import Path
import json

def create_slide_1213():
    # Load base_template.html
    try:
        with open("base_template.html", "r", encoding="utf-8") as f:
            template_html_content = f.read()
    except FileNotFoundError:
        print("Error: base_template.html not found.")
        return

    # Define date variables for 2025-12-13
    date_jp = "2025年12月13日"
    date_slash = "2025/12/13"
    
    # Define content variables from 1213.txt
    short_title = "Cursor 未来開発体験" 
    main_title = "Cursorが描く「未来の開発体験」：思考とコードの直結"
    subtitle = "デザインと実装の境界を溶かし、開発の「抽象レベル」を引き上げる"

    # HTML Parts Construction
    
    # Intro Box
    intro_box = """
    <div style=\"background: linear-gradient(135deg, #1e1e2e, #3b3b4f); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);\">
        <p style=\"font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;\">
            「ツール」から「思考の拡張」へ
        </p>
        <p style=\"font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;\">
            Cursorは単なるAIコードエディタではありません。「デザインとコードのギャップを埋める」こと、そして「開発作業の抽象レベルを引き上げる」ことを通じて、開発者が「How（方法）」ではなく「What（目的）」に集中できる未来を目指しています。
        </p>
    </div>
    """

    # Highlight Box (2つの核心)
    highlight_box = """
    <div class="highlight-box" style="background-color: #f3f4f6; border-left: 5px solid #6366f1; padding: 24px; margin-bottom: 32px; border-radius: 8px;">
      <h3 style="color: #4f46e5; margin-top: 0; margin-bottom: 12px; display: flex; align-items: center; font-size: 1.4rem;">
         <span style="font-size: 1.8rem; margin-right: 10px;">✨</span>
         Cursorの2つの核心コンセプト
      </h3>
      <ul style="font-size: 1.1rem; line-height: 1.8; color: #1f2937; list-style: none; padding: 0;">
        <li style="margin-bottom: 12px;"><strong>1. デザインとコードの融合：</strong> 中核機能「Visual Editor」により、Webアプリ、コード、ビジュアルツールをシームレスに操作。Figmaのような直感操作がコードに直結します。</li>
        <li><strong>2. 抽象レベルの向上：</strong> 複雑な実装手順（How）はAIに任せ、開発者は本質的な目的（What）の表現に集中。「デバッグ」「計画」「判断」のあり方を再定義します。</li>
      </ul>
    </div>
    """

    # Feature Grid (具体的な進化)
    feature_grid = """
    <div class="card accent" style="background: white; border: 1px solid var(--border); border-top: 4px solid var(--primary); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <h4 style="margin-bottom: 20px; font-size: 1.3rem; color: var(--text); border-bottom: 1px solid var(--border); padding-bottom: 10px;">抽象化された新しい開発体験</h4>
      
      <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">🐛</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">Debug Mode</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                「推測」での試行錯誤は終了。バグを言葉で説明するだけで、ログ収集・分析から修正案の提示までAIが完遂。
            </div>
        </div>
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">🗺️</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">Plan Mode</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                複雑なタスクを自動でフローチャート化し、実装計画を立案。タスクを分割して並列実行も可能に。
            </div>
        </div>
        <div class="feature-item" style="padding: 20px; background: var(--bg-light); border-radius: 12px; text-align: center; border: 1px solid var(--border);">
            <span class="feature-icon" style="font-size: 2.5rem; display: block; margin-bottom: 12px;">🎨</span>
            <div class="feature-title" style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">Visual Editor</div>
            <div class="feature-desc" style="font-size: 0.95rem; line-height: 1.5; color: var(--text-light); text-align: left;">
                UI要素をクリックして「赤にして」と言うだけ。CSSプロパティを覚えなくても、直感的にデザイン調整が可能。
            </div>
        </div>
      </div>
    </div>
    """

    # Detail Card (Before/After)
    detail_card = """
    <div class="card" style="background: white; border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <h3 style="margin-bottom: 20px; color: var(--text); display: flex; align-items: center;">
            <span style="width: 6px; height: 24px; background: var(--primary); margin-right: 10px; border-radius: 3px;"></span>
            開発プロセスのBefore / After
        </h3>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 1rem; min-width: 600px;">
                <thead>
                    <tr style="background: #f3f4f6; border-bottom: 2px solid #e5e7eb;">
                        <th style="padding: 12px; text-align: left; color: #4b5563; width: 25%;">フェーズ</th>
                        <th style="padding: 12px; text-align: left; color: #4b5563; width: 35%;">これまで (従来)</th>
                        <th style="padding: 12px; text-align: left; color: #6366f1; font-weight: bold; width: 40%;">Cursorが描く未来</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 12px; font-weight: bold;">デザイン調整</td>
                        <td style="padding: 12px; color: #6b7280;">コード修正 ⇄ ブラウザ確認の往復。<br>CSSプロパティの手探り。</td>
                        <td style="padding: 12px; color: #1f2937;"><strong>Visual Editor</strong>で直接操作。<br>自然言語で「見た目」を指示。</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 12px; font-weight: bold;">デバッグ</td>
                        <td style="padding: 12px; color: #6b7280;">「たぶんここ？」と推測し、大量のログを目視確認。</td>
                        <td style="padding: 12px; color: #1f2937;"><strong>Debug Mode</strong>が原因特定。<br>クリーンな修正コードを即提示。</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold;">意思決定</td>
                        <td style="padding: 12px; color: #6b7280;">どの実装が良いか、自分で調べて試して悩む。</td>
                        <td style="padding: 12px; color: #1f2937;"><strong>Multi-agent Judging</strong>が<br>複数案から最適解を理由付きで推奨。</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <p style="margin-top: 20px; font-size: 0.95rem; background: #eef2ff; padding: 12px; border-radius: 6px; color: #4338ca; border: 1px solid #c7d2fe;">
            💡 <strong>Vision:</strong> 人間は「思考」そのものに時間を使う。これがAI支援開発のあるべき姿です。
        </p>
    </div>
    """
    
    # 配色設定 (Cursor Purple/Blue Theme)
    css_vars_block = """
    :root {
      --primary: #6366f1; /* Indigo */
      --accent: #1e1e2e; /* Dark Cursor-like bg */
      --accent2: #a5b4fc; /* Light Indigo */
      --bg-dark: #1e1e2e;
      --bg-light: #f8fafc;
      --border: #e2e8f0;
      --text: #1f2937;
      --text-light: #6b7280;
    }
    header {
      background: linear-gradient(135deg, #1e1e2e 0%, #4338ca 100%);
    }
    .breaking-badge {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
    }
    .subtitle {
        color: #e0e7ff;
    }
    """
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 -->')
    content_parts.append('  <div class="top-image-container">')
    
    # Image tag construction
    img_tag_parts = []
    img_tag_parts.append('<img src="../../input/day/1213.jpg" ')
    img_tag_parts.append('alt="Cursor Vision Visual" style="width: 100%; max-width: 800px; border-radius: 12px; display: block; margin: 0 auto 32px auto;">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🖱️</span>')
    content_parts.append(f'      <h2>{main_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append('    ' + intro_box)
    content_parts.append('    ' + highlight_box)
    content_parts.append('    ' + feature_grid)
    content_parts.append('    ' + detail_card)
    content_parts.append('  </section>')

    content_parts.append('  <!-- スライド資料 (全ページ) -->')
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">📖</span>')
    content_parts.append('      <h2>レポート全文 (PDF)</h2>')
    content_parts.append('    </div>')
    
    content_parts.append('    <div class="download-link" style="text-align: center; margin-bottom: 24px;">')
    
    # PDF link construction
    pdf_link_parts = []
    # Using ASCII filename as per previous instruction to prevent GH Pages issues
    pdf_link_parts.append('<a href="../../input/day/1213-Workflow_Redefined.pdf" target="_blank" ')
    pdf_link_parts.append('style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); ')
    pdf_link_parts.append('padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); ')
    pdf_link_parts.append('text-decoration: none; color: var(--text); transition: all 0.2s ease;">')
    content_parts.append('        ' + "".join(pdf_link_parts))
    
    content_parts.append('            <span style="font-size: 1.2rem;">📄</span>')
    content_parts.append('            <span>レポート全文をダウンロード (PDF)</span>')
    content_parts.append('        </a>')
    content_parts.append('    </div>')
    
    # Slides construction (15 pages)
    slides_list = []
    for i in range(1, 16):
        slides_list.append(f'<img src="../../input/day/1213_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)

    content_parts.append('    <div class="slides-container">')
    content_parts.append('        <!-- Slide Images -->')
    content_parts.append('        ' + slides_html)
    content_parts.append('    </div>')
    
    content_parts.append('    <style>')
    content_parts.append('        .slide-img {')
    content_parts.append('            width: 100%;')
    content_parts.append('            max-width: 1000px;')
    content_parts.append('            height: auto;')
    content_parts.append('            border-radius: 12px;')
    content_parts.append('            box-shadow: 0 4px 20px rgba(0,0,0,0.15);')
    content_parts.append('            border: 1px solid var(--border);')
    content_parts.append('            transition: transform 0.3s ease;')
    content_parts.append('        }')
    content_parts.append('        .slide-img:hover {')
    content_parts.append('            transform: scale(1.01);')
    content_parts.append('            box-shadow: 0 8px 30px rgba(0,0,0,0.2);')
    content_parts.append('        }')
    content_parts.append('        .slides-container {')
    content_parts.append('            display: flex;')
    content_parts.append('            flex-direction: column;')
    content_parts.append('            align-items: center;')
    content_parts.append('            gap: 24px;')
    content_parts.append('            width: 100%;')
    content_parts.append('        }')
    content_parts.append('    </style>')
    
    content_parts.append('  </section>')
    content_parts.append('</main>')

    main_content_html = "\n".join(content_parts)

    # プレースホルダーを置換
    html = template_html_content.replace("{{FULL_TITLE}}", f"{short_title}: {main_title} - {date_slash}")
    html = html.replace("{{CSS_VARS_BLOCK}}", css_vars_block)
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"⚡ {date_jp}レポート | Cursor Future Vision")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_13.html"
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1213()
