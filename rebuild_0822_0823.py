import re
import os
from pathlib import Path

def rebuild_slide(filename, input_date_str, display_date_jp, title, intro_text, summary_points):
    template_path = Path(r"C:\develop\ai-news-site\presentations\day_slides\day_slide_2025_08_27.html")
    output_path = Path(r"C:\develop\ai-news-site\presentations\day_slides") / filename
    
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Title and Date replacement
    content = re.sub(r"<title>.*?</title>", f"<title>{display_date_jp} - {title}</title>", content)
    content = re.sub(r'<div class="date-badge">.*?</div>', f'<div class="date-badge">{display_date_jp}</div>', content)
    content = re.sub(r"<h1>.*?</h1>", f"<h1>🚀 {title}</h1>", content)
    content = re.sub(r"<h2>.*?</h2>", f"<h2>{display_date_jp} AI News Analysis</h2>", content)

    # Intro Box Replacement
    # In 08/27 template, the intro box is within a div with a specific gradient.
    # We'll look for that pattern.
    intro_pattern = re.compile(r'<div style="background: linear-gradient\(135deg, #0f172a, #1e293b\);.*?<p style="font-size: 1\.1rem; opacity: 0\.95;.*?</div>', re.DOTALL)
    new_intro = f'''<div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: var(--accent-color); padding: 24px; border-radius: 16px; margin-bottom: 32px; border: 1px solid rgba(59, 130, 246, 0.2); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; color: #fff;">
                            今日の注目ニュース
                        </p>
                        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6; color: #cbd5e1;">
                            {intro_text}
                        </p>
                    </div>'''
    content = intro_pattern.sub(new_intro, content)

    # Summary Points (Highlight Box)
    # The 08/27 template might have a specific structure for highlight box.
    highlight_pattern = re.compile(r'<h4>.*?エンジニアのための3つの進化.*?</h4>.*?<ul.*?>.*?</ul>', re.DOTALL)
    
    points_html = ""
    for i, p in enumerate(summary_points[:3], 1):
        points_html += f'''<li style="display: flex; gap: 12px; align-items: start;">
                                <span style="background: var(--accent-color); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; flex-shrink: 0;">{i}</span>
                                <span style="color: #475569;">{p}</span>
                            </li>'''
    
    new_highlight = f'''<h4 style="color: var(--primary-color); margin-top: 0; margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 1.4rem;">💡</span>
                                今日の重要ポイント
                            </h4>
                            <ul style="list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;">
                                {points_html}
                            </ul>'''
    content = highlight_pattern.sub(new_highlight, content)

    # Write back
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Rebuilt {filename}")

# Fix 08/22
rebuild_slide(
    "day_slide_2025_08_22.html",
    "0822",
    "2025年08月22日",
    "AppleとGoogle、GeminiのSiri統合を検討",
    "AppleがGoogleのGemini AIを活用してSiriを大幅にアップデートする可能性についての議論が始まりました。来年のSiri刷新にGeminiをサーバー上で運用するカスタムモデルを構築する話が進んでいます。",
    [
        "Appleのプライバシー重視の姿勢とGoogleのAI統合が注目点",
        "エンジニアにとっては将来のツールとして有望だが即時性は低い",
        "ビジネスマンにとっては将来のタスク管理効率化に期待"
    ]
)

# Fix 08/23
rebuild_slide(
    "day_slide_2025_08_23.html",
    "0823",
    "2025年08月23日",
    "DeepSeek V3.1リリース：オープンソースAIの新基準",
    "研究機関DeepSeekがリリースしたDeepSeek V3.1は、671BパラメータのMoEモデルで、コーディングや数学分野でGPT-4oやClaude 3.5に匹敵する性能を示しています。",
    [
        "オープンソースとして即時利用可能で、ツール呼び出し機能が強化されている",
        "ハイスペックなハードウェアが必要だが、ローカル環境でコード生成が可能",
        "無料アクセスが可能で、商用モデルへの依存を減らす可能性"
    ]
)
