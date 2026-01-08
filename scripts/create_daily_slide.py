#!/usr/bin/env python3
"""
汎用的な日次スライド生成スクリプト
使用方法: python scripts/create_daily_slide.py MMDD

例: python scripts/create_daily_slide.py 0108
"""

import sys
import os
import glob
import json
from pathlib import Path

def create_slide(date_mmdd):
    """指定された日付のスライドを生成"""

    # 基本情報の取得
    txt_file = f"input/day/{date_mmdd}.txt"
    if not os.path.exists(txt_file):
        print(f"Error: {txt_file} not found")
        return False

    # テキストファイルから内容を読み込み
    with open(txt_file, "r", encoding="utf-8") as f:
        content_lines = f.readlines()

    # 日付の変換
    month = date_mmdd[:2]
    day = date_mmdd[2:4]
    date_jp = f"2026年{int(month)}月{int(day)}日"
    date_slash = f"2026/{month}/{day}"

    # タイトルと説明を抽出（1行目がタイトル、3行目以降が説明）
    if len(content_lines) < 3:
        print("Error: Content file must have at least 3 lines")
        return False

    # タイトルを生成（1行目から）
    raw_title = content_lines[0].strip()
    # コロンや記号を削除してクリーンなタイトルに
    main_title = raw_title.replace("：概要と分析", "").replace(":概要と分析", "").strip()
    short_title = main_title.split("：")[0].split(":")[0].strip()

    # 説明文（エグゼクティブサマリーの最初の文）
    subtitle = None
    for line in content_lines[2:]:
        line = line.strip()
        if line and not line.startswith("エグゼクティブサマリー"):
            # 最初の100文字程度を抜粋
            subtitle = line[:150] + "..." if len(line) > 150 else line
            break

    if not subtitle:
        subtitle = f"{short_title}の詳細分析"

    # テーマに応じたカラーパレットを選択
    color_themes = {
        "health": {"primary": "#10b981", "accent": "#059669", "bg_light": "#d1fae5"},
        "tech": {"primary": "#76b900", "accent": "#1E5128", "bg_light": "#f0f8f0"},
        "ai": {"primary": "#7c3aed", "accent": "#14b8a6", "bg_light": "#f5f3ff"},
        "default": {"primary": "#3b82f6", "accent": "#1e40af", "bg_light": "#dbeafe"},
    }

    # テーマ判定
    theme_key = "default"
    title_lower = main_title.lower()
    if "health" in title_lower or "医療" in main_title or "健康" in main_title:
        theme_key = "health"
    elif "nvidia" in title_lower or "chip" in title_lower or "gpu" in title_lower:
        theme_key = "tech"
    elif "ai" in title_lower or "agent" in title_lower or "agi" in title_lower:
        theme_key = "ai"

    colors = color_themes[theme_key]

    # テンプレートの読み込み
    template_path = "base_template.html"
    if not os.path.exists(template_path):
        print(f"Error: {template_path} not found")
        return False

    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    # CSS変数
    css_vars = f"""
    :root {{
      --primary: {colors['primary']};
      --accent: {colors['accent']};
      --bg-light: {colors['bg_light']};
      --bg-dark: #0f1419;
      --text: #0f1419;
      --text-light: #6b7280;
      --border: #e2e8f0;
      --tron-black: #000000;
    }}
    """

    # イントロボックス（エグゼクティブサマリーから）
    intro_text = ""
    for line in content_lines[2:]:
        line = line.strip()
        if line and not line.startswith("エグゼクティブサマリー"):
            intro_text = line
            break

    intro_box = f"""
    <div style="background: linear-gradient(135deg, {colors['primary']}, {colors['accent']}); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.5; letter-spacing: 0.05em;">
            {short_title}
        </p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            {intro_text}
        </p>
    </div>
    """

    # スライド数のカウント
    slide_dir = f"input/day/{date_mmdd}_slides"
    slide_count = 0
    if os.path.exists(slide_dir):
        slides = [f for f in os.listdir(slide_dir) if f.endswith(".jpg")]
        slide_count = len(slides)

    # メインコンテンツ
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/{date_mmdd}.png" alt="{date_mmdd} Visual" onerror="this.src='https://placehold.co/1200x600?text={date_mmdd}+AI+News'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📰</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全{slide_count}ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/{date_mmdd}_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, slide_count + 1)])}
        </div>
      </section>
    </main>
    """

    # プレースホルダーの置換
    final_html = template_html
    final_html = final_html.replace("{{FULL_TITLE}}", f"{main_title} - {date_slash}")
    final_html = final_html.replace("{{CSS_VARS_BLOCK}}", css_vars)
    final_html = final_html.replace("{{BREAKING_BADGE_TEXT}}", f"📰 {date_jp}レポート | {short_title}")
    final_html = final_html.replace("{{H1_TITLE}}", main_title)
    final_html = final_html.replace("{{SUBTITLE}}", subtitle)
    final_html = final_html.replace("{{DATE}}", date_jp)
    final_html = final_html.replace("{{MAIN_CONTENT_HTML}}", main_content)

    # 出力
    output_path = f"presentations/day_slides/day_slide_2026_{month}_{day}.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Generated {output_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_daily_slide.py MMDD")
        print("Example: python scripts/create_daily_slide.py 0108")
        sys.exit(1)

    date_mmdd = sys.argv[1]

    # 日付形式のバリデーション
    if len(date_mmdd) != 4 or not date_mmdd.isdigit():
        print("Error: Date must be in MMDD format (e.g., 0108)")
        sys.exit(1)

    success = create_slide(date_mmdd)
    sys.exit(0 if success else 1)
