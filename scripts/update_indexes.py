#!/usr/bin/env python3
"""
汎用的なインデックス更新スクリプト
使用方法: python scripts/update_indexes.py MMDD "タイトル" "説明文"

例: python scripts/update_indexes.py 0108 "ChatGPTヘルスケア" "健康・ウェルネス分野に特化した新機能の発表"
"""

import sys
import re
from pathlib import Path

def update_daily_slides_index(date_mmdd, title, description):
    """daily_slides_index.htmlに新しいエントリを追加"""
    index_path = "daily_slides_index.html"

    # 日付変換
    month = date_mmdd[:2]
    day = date_mmdd[2:4]
    date_jp = f"2026年{int(month)}月{int(day)}日"
    date_slash = f"2026/{month}/{day}"

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 既に存在するかチェック
    if f"day_slide_2026_{month}_{day}.html" in content:
        print(f"Entry for {date_mmdd} already exists in daily_slides_index.html")
        return

    # 新しいエントリHTML
    new_entry = f'''        <div class="slide-card">
          <div class="slide-date">{date_jp}</div>
          <div class="slide-title">{title}</div>
          <div class="slide-desc">{description}</div>
          <div class="slide-actions">
            <a href="presentations/day_slides/day_slide_2026_{month}_{day}.html" class="btn btn-primary">
              🎯 スライドを開く
            </a>
            <a href="input/day/{date_mmdd}.txt" class="btn btn-secondary" download>
              📄 テキスト
            </a>
          </div>
        </div>'''

    # slides-gridの開始タグの直後に挿入
    grid_pattern = r'(<div class="slides-grid">)'
    content = re.sub(
        grid_pattern,
        r'\1\n' + new_entry,
        content,
        count=1
    )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated {index_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python scripts/update_indexes.py MMDD \"タイトル\" \"説明文\"")
        print("Example: python scripts/update_indexes.py 0108 \"ChatGPTヘルスケア\" \"健康・ウェルネス分野に特化した新機能\"")
        sys.exit(1)

    date_mmdd = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3]

    # 日付形式のバリデーション
    if len(date_mmdd) != 4 or not date_mmdd.isdigit():
        print("Error: Date must be in MMDD format (e.g., 0108)")
        sys.exit(1)

    update_daily_slides_index(date_mmdd, title, description)
    print("Index update complete!")
