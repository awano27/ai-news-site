#!/usr/bin/env python3
"""PDFをスライド画像に変換するスクリプト"""

import os
import sys
from pathlib import Path

try:
    from pdf2image import convert_from_path
except ImportError:
    print("pdf2image がインストールされていません。")
    print("実行: pip install pdf2image")
    print("また、poppler-utils も必要です:")
    print("  Windows: https://github.com/oschwartz10612/poppler-windows/releases")
    print("  Mac: brew install poppler")
    print("  Linux: apt install poppler-utils")
    sys.exit(1)

def convert_pdf_to_slides(pdf_path: str, output_dir: str = None):
    """PDFをスライド画像に変換"""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"エラー: {pdf_path} が見つかりません")
        return
    
    # 出力ディレクトリを決定
    if output_dir is None:
        # 0129-xxx.pdf -> 0129_slides/
        date_prefix = pdf_path.stem.split('-')[0]
        output_dir = pdf_path.parent / f"{date_prefix}_slides"
    else:
        output_dir = Path(output_dir)
    
    # ディレクトリ作成
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"出力先: {output_dir}")
    
    # PDF変換
    print(f"変換中: {pdf_path.name}...")
    images = convert_from_path(pdf_path, dpi=150)
    
    print(f"ページ数: {len(images)}")
    
    # 画像保存
    for i, image in enumerate(images, 1):
        output_path = output_dir / f"slide_{i:03d}.jpg"
        image.save(output_path, "JPEG", quality=90)
        print(f"  保存: {output_path.name}")
    
    print(f"\n完了！ {len(images)}枚のスライド画像を生成しました。")
    return len(images)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python pdf_to_slides.py <PDF_PATH> [OUTPUT_DIR]")
        print("例: python pdf_to_slides.py input/day/0129-Verifiable_AI_Agents.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_pdf_to_slides(pdf_path, output_dir)
