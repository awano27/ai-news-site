#!/usr/bin/env python3
"""
Reveal.jsを使用しているスライドファイルからReveal.jsを削除して、
リンクがクリックできるようにするスクリプト
"""

import os
import re
import glob

def fix_slide_file(file_path):
    """個別のスライドファイルを修正"""
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # すでに修正済みかチェック
    if 'reveal.js' not in content.lower():
        print(f"  Already fixed: {file_path}")
        return False
    
    # Reveal.jsのCSS/JSを削除
    content = re.sub(r'<link rel=["\']stylesheet["\'] href=["\']https://cdn\.jsdelivr\.net/npm/reveal\.js@.*?["\']>', '', content)
    content = re.sub(r'<script.*?src=["\']https://cdn\.jsdelivr\.net/npm/reveal\.js@.*?["\'].*?></script>', '', content)
    
    # Reveal.jsのスクリプト初期化部分を削除
    content = re.sub(r'<script>.*?Reveal\.initialize.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script src=["\']https://cdn\.jsdelivr\.net/npm/reveal\.js@.*?["\']></script>', '', content)
    
    # reveal divクラスをcontainerに置換
    content = content.replace('<div class="reveal"><div class="slides">', '<div class="container">')
    content = content.replace('</div></div>', '</div>')
    
    # CSSスタイルを簡略化
    if '/* 安定表示用: スクロールレイアウトを強制 */' in content:
        # 既存の複雑なCSSを簡単な静的レイアウトに置換
        old_css = re.search(r'/\* 安定表示用: スクロールレイアウトを強制 \*/.*?\.reveal \.controls.*?display:none !important; \}', content, re.DOTALL)
        if old_css:
            new_css = '''/* シンプルな静的レイアウト */
    html, body { margin:0; padding:0; background:#fff; font-family:'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }
    .container { max-width: 1100px; margin:0 auto; padding:20px; }
    section { margin:0 auto 28px; padding:20px; background:#fff; border:1px solid #e5e7eb; border-radius:16px; box-shadow:0 8px 20px rgba(0,0,0,.08); text-align:left; }'''
            content = content.replace(old_css.group(), new_css)
    
    # 余分な改行やスペースを整理
    content = re.sub(r'\n\s*\n', '\n', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  Fixed: {file_path}")
    return True

def main():
    """メイン処理"""
    # day_slidesディレクトリ内の最新のスライドファイルを修正
    slide_dir = "presentations/day_slides"
    pattern = os.path.join(slide_dir, "day_slide_2025_09_*.html")
    
    files = glob.glob(pattern)
    files.sort(reverse=True)  # 新しい順にソート
    
    # 最新の10ファイルを修正
    recent_files = files[:10]
    
    fixed_count = 0
    for file_path in recent_files:
        if fix_slide_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files out of {len(recent_files)} processed.")

if __name__ == "__main__":
    main()