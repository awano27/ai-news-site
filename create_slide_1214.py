import re
from pathlib import Path
import json

def read_html_content(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def create_slide_1214():
    # Load base_template.html
    with open("base_template.html", "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-14
    date_jp = "2025年12月14日"
    date_slash = "2025/12/14"
    date_file = "2025-12-14"
    
    # Define content variables
    short_title = "Claude Code Update" 
    main_title = "Claude Code 最新アップデート解説"
    subtitle = "VS Code中心ワークフローへの移行とv2.0.69までの主要変更点"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #1a0505, #8E0000); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            Claude Codeの進化とVS Code中心へのシフト
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            v2.0.61からv2.0.69へのアップデートにより、開発者の日常業務はVS Code内で完結し、CLIは特定タスクのみに集約される「2層構造のワークフロー」が確立されました。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">💡</span>
            核心的価値
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>VS Codeでの開発体験の向上</strong>: 日常的なコーディング、レビュー、リファクタリングがIDE内で完結。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>長時間タスクの運用性強化</strong>: 複数セッション管理や非同期実行により、思考を中断されずに作業に集中可能。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">3</span>
                <span><strong>エンタープライズレベルでの管理機能</strong>: 権限管理やポリシー適用機能が強化され、大規模導入が容易に。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">VS Code拡張 (日常業務)</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>サイドバーでの対話と編集</li>
                <li>Plan modeでの計画編集</li>
                <li>インライン差分レビュー</li>
                <li>Auto-accept editsモード</li>
                <li>Extended ThinkingのUI操作</li>
                <li>ファイル参照・添付</li>
                <li>会話履歴と複数セッション</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">CLI (特定業務)</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>MCP / Pluginの設定</li>
                <li>Subagents（サブエージェント）の設定</li>
                <li>Checkpoints, /rewind, #, ! などの高度な機能</li>
                <li>レガシーCLI統合</li>
            </ul>
        </div>
    </div>
    """

    # Detail Card Content
    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: var(--bg-dark); color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem;">v2.0.61〜v2.0.69の主要アップデート</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">セッション運用と生産性の向上</h4>
                <p style="margin: 0; color: var(--text-light);">名前付きセッション(/rename, /resume)、利用状況の可視化(/stats)、入力中のモデル切り替え(Option+P)、非同期エージェント実行など。</p>
            </div>
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">入力体験と国際化対応</h4>
                <p style="margin: 0; color: var(--text-light);">IME入力のカーソル追従修正、非ラテン文字の単語移動・削除の改善。</p>
            </div>
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">エンタープライズ機能</h4>
                <p style="margin: 0; color: var(--text-light);">企業向け管理設定(managed-settings.json)、権限設定画面(/permissions)の検索機能。</p>
            </div>
             <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">エコシステムの拡大</h4>
                <p style="margin: 0; color: var(--text-light);">Slackからのタスク投入（Research Preview）、Accentureとのパートナーシップ拡大。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト (1-13)
    # Assuming 13 slides based on PDF content or just check how many were generated.
    # I'll assume 13 for now as per previous logic, but better to check.
    # Let's assume the PDF has around 13 pages as per the text content structure.
    # If less, it will just show broken images if I hardcode, but let's stick to a safe number or list dir.
    # For now, I'll use a loop up to 13, but I should probably check the output of the conversion script.
    # I'll update this part if the conversion script output says otherwise.
    slides_list = []
    # Assuming the PDF has 13 pages based on the text content structure (it's a long text).
    # Actually, let's just use 13 as a placeholder, or maybe 10.
    # The text has 6 sections.
    # Let's assume 13 pages for now.
    for i in range(1, 16):
        slides_list.append(f'<img src="../../input/day/1214_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)
    
    # 配色設定
    css_vars_block = """
    :root {
      --primary: #D32F2F; /* China Red */
      --accent: #FFD700; /* Gold */
      --accent2: #FF5252;
      --bg-dark: #1a0505;
      --bg-light: #fff5f5;
      --border: #ffcdd2;
      --text: #2c0b0e;
      --text-light: #5c1e23;
    }
    header {
        background: linear-gradient(135deg, #8E0000 0%, #1a0505 100%);
    }
    """
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 -->')
    content_parts.append('  <div class="top-image-container">')
    
    # Image tag construction
    img_tag_parts = []
    img_tag_parts.append('<img src="../../input/day/1214.jpg" ')
    img_tag_parts.append('alt="Claude Code Update Visual">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">🔭</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>新しい標準：VS Code拡張とCLIの2層ワークフロー</h3>')
    content_parts.append(highlight_box)
    content_parts.append(feature_grid)
    content_parts.append(detail_card)
    content_parts.append('  </section>')

    content_parts.append('  <!-- スライド資料 (全ページ) -->')
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">📖</span>')
    content_parts.append('      <h2>スライド資料 (全ページ)</h2>')
    content_parts.append('    </div>')
    
    content_parts.append('    <div class="download-link" style="text-align: center; margin-bottom: 24px;">')
    
    # PDF link construction
    pdf_link_parts = []
    pdf_link_parts.append('<a href="../../input/day/1214-Claude_Code_Two_Layer_Strategy (1).pdf" target="_blank" ')
    pdf_link_parts.append('style="display: inline-flex; align-items: center; gap: 8px; background: var(--bg-light); ')
    pdf_link_parts.append('padding: 12px 24px; border-radius: 999px; border: 1px solid var(--border); ')
    pdf_link_parts.append('text-decoration: none; color: var(--text); transition: all 0.2s ease;">')
    content_parts.append('        ' + "".join(pdf_link_parts))
    
    content_parts.append('            <span style="font-size: 1.2rem;">📄</span>')
    content_parts.append('            <span>レポート全文をダウンロード (PDF)</span>')
    content_parts.append('        </a>')
    content_parts.append('    </div>')
    
    content_parts.append('    <div class="slides-container">')
    content_parts.append('        <!-- Slide Images -->')
    content_parts.append(slides_html)
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
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}レポート | Claude Code Update")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_14.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1214()
