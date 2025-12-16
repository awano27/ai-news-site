import re
from pathlib import Path
import json

def create_slide_1216():
    # Load base_template.html
    with open("base_template.html", "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Define date variables for 2025-12-16
    date_jp = "2025年12月16日"
    date_slash = "2025/12/16"
    date_file = "2025-12-16"
    
    # Define content variables
    short_title = "KAMUI Mobile" 
    main_title = "iOSアプリ「KAMUI Mobile」の新規性と位置づけに関する分析レポート"
    subtitle = "プロンプト入力で即座にアプリ生成：モバイル開発の民主化とAGI基盤「神威」へのゲートウェイ戦略"

    # Intro Box Content
    intro_box = """
    <div style="background: linear-gradient(135deg, #000000, #4A90E2); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            モバイルアプリ開発の民主化
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            2025年12月にリリースされた「KAMUI Mobile」は、プロンプト入力のみで即座に動作するモバイルアプリを生成する革新的なiOSアプリです。アプリ開発のあり方を変革し、AGI開発基盤「神威/KAMUI」への戦略的なゲートウェイとして機能します。
        </p>
    </div>
    """

    # Highlight Box Content
    highlight_box = """
    <div style="background: var(--bg-light); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
        <h4 style="color: var(--primary); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.4rem;">🚀</span>
            戦略的ポジショニング：2つの「KAMUI」
        </h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">1</span>
                <span><strong>AGI開発基盤「神威/KAMUI」</strong>: Webベースの包括的なプラットフォーム。高機能・高単価（サブスクリプション）。</span>
            </li>
            <li style="display: flex; gap: 12px; align-items: start;">
                <span style="background: var(--primary); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">2</span>
                <span><strong>KAMUI Mobile</strong>: iOS専用の無料アプリ。即時的なアプリ生成体験を提供し、ユーザー教育とリードジェネレーションを担う。</span>
            </li>
        </ul>
    </div>
    """

    # Feature Grid Content
    feature_grid = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">神威/KAMUI (Web)</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>AGI開発基盤</li>
                <li>Webプラットフォーム</li>
                <li>有料サブスクリプション (例: 98ドル/月)</li>
                <li>高度な開発ニーズに対応</li>
            </ul>
        </div>
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h4 style="color: var(--text); margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid var(--accent); padding-bottom: 8px;">KAMUI Mobile (iOS)</h4>
            <ul style="padding-left: 20px; margin: 0; color: var(--text-light);">
                <li>モバイルアプリ生成ツール</li>
                <li>iOS専用アプリ</li>
                <li>無料 (App Store「教育」カテゴリ)</li>
                <li>即時的な体験とエントリーポイント</li>
            </ul>
        </div>
    </div>
    """

    # Detail Card Content
    detail_card = """
    <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 32px;">
        <div style="background: var(--bg-dark); color: white; padding: 16px 24px;">
            <h3 style="margin: 0; font-size: 1.2rem;">フリーミアム戦略とゲートウェイ機能</h3>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <h4 style="color: var(--primary); margin-bottom: 8px;">二層構造のシナジー</h4>
                <p style="margin: 0; color: var(--text-light);">無料のモバイルアプリでユーザーの関心を惹きつけ（リードジェネレーション）、AIによるアプリ生成を体験させることで（ユーザー教育）、より高度な機能を求める層を有料のWebプラットフォームへと誘導する戦略的な設計。</p>
            </div>
             <div>
                <h4 style="color: var(--primary); margin-bottom: 8px;">市場へのインパクト</h4>
                <p style="margin: 0; color: var(--text-light);">「モバイル側の入口」として機能することで、AGI技術の社会実装を加速させ、開発者層の裾野を広げる役割を果たすことが期待されます。</p>
            </div>
        </div>
    </div>
    """
    
    # 5. スライド画像リスト (自動取得の方が良いが、ここでは固定で想定。枚数はconvertの結果次第だが、一旦15枚程度と仮定してリスト化。後で調整可能)
    # 実際には画像がある分だけ表示するようにしたいが、テンプレートの構造上ループで生成。
    # ここでは15枚まで対応するようにしておく。
    slides_list = []
    # 画像が存在するか確認してリストに追加するのがベストだが、簡易的に15枚分生成コードを入れる。
    # 実際には生成された画像の数に合わせるべき。
    # convert_1216.pyの出力ログを見れば枚数がわかる。
    # 一旦15枚としておく。
    for i in range(1, 16):
        slides_list.append(f'<img src="../../input/day/1216_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">')
    slides_html = "\n".join(slides_list)
    
    # 配色設定 (Blue/Tech theme)
    css_vars_block = """
    :root {
      --primary: #007AFF; /* iOS Blue */
      --accent: #000000; /* Black */
      --accent2: #4A4A4A;
      --bg-dark: #1c1c1e; /* iOS Dark Mode BG */
      --bg-light: #f2f2f7; /* iOS Light Mode BG */
      --border: #d1d1d6;
      --text: #1a1a1a;
      --text-light: #4a4a4a;
    }
    header {
        background: linear-gradient(135deg, #000000 0%, #007AFF 100%);
    }
    """
    
    # メインコンテンツの構築
    content_parts = []
    content_parts.append('<main>')
    content_parts.append('  <!-- トップ画像 -->')
    content_parts.append('  <div class="top-image-container">')
    
    # Image tag construction
    img_tag_parts = []
    img_tag_parts.append('<img src="../../input/day/1216.jpg" ')
    img_tag_parts.append('alt="KAMUI Mobile Visual">')
    content_parts.append('    ' + "".join(img_tag_parts))
    
    content_parts.append('  </div>')
    
    content_parts.append('  <section class="section">')
    content_parts.append('    <div class="section-header">')
    content_parts.append('      <span class="section-icon">📱</span>')
    content_parts.append(f'      <h2>{short_title}</h2>')
    content_parts.append('    </div>')
    content_parts.append(intro_box)
    content_parts.append('    <h3>戦略的ポジショニング</h3>')
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
    pdf_link_parts.append('<a href="../../input/day/1216-KAMUI_Mobile_分析と実務導入の評価軸.pdf" target="_blank" ')
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
    html = html.replace("{{BREAKING_BADGE_TEXT}}", f"🌏 {date_jp}レポート | {short_title}")
    html = html.replace("{{H1_TITLE}}", main_title)
    html = html.replace("{{SUBTITLE}}", subtitle)
    html = html.replace("{{DATE}}", date_jp)
    html = html.replace("{{MAIN_CONTENT_HTML}}", main_content_html)
    
    # 保存
    output_path = "presentations/day_slides/day_slide_2025_12_16.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1216()
