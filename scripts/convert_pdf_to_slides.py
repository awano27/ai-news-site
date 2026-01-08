#!/usr/bin/env python3
"""
汎用的なPDF→画像変換スクリプト
使用方法: python scripts/convert_pdf_to_slides.py MMDD

例: python scripts/convert_pdf_to_slides.py 0108
"""

import sys
import os
import glob
import fitz  # PyMuPDF

def convert_pdf_to_images(date_mmdd):
    """指定された日付のPDFを画像に変換"""

    # PDFファイルを検索
    pdf_pattern = f"input/day/{date_mmdd}-*.pdf"
    pdf_files = glob.glob(pdf_pattern)

    if not pdf_files:
        print(f"Error: No PDF file found matching {pdf_pattern}")
        return False

    pdf_path = pdf_files[0]
    print(f"Found PDF: {pdf_path}")

    # 出力フォルダ
    output_folder = f"input/day/{date_mmdd}_slides"

    # フォルダが存在しない場合は作成
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # PDFを開く
    doc = fitz.open(pdf_path)

    print(f"Converting {pdf_path} to images...")
    print(f"Total pages: {len(doc)}")

    for i, page in enumerate(doc):
        # 高解像度でレンダリング (zoom=2で2倍の解像度)
        zoom = 2
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # 画像を保存 (slide_001.jpg, slide_002.jpg...)
        output_filename = f"slide_{i+1:03d}.jpg"
        output_path = os.path.join(output_folder, output_filename)
        pix.save(output_path)
        print(f"Saved {output_path}")

    print(f"Conversion complete! {len(doc)} slides saved to {output_folder}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/convert_pdf_to_slides.py MMDD")
        print("Example: python scripts/convert_pdf_to_slides.py 0108")
        sys.exit(1)

    date_mmdd = sys.argv[1]

    # 日付形式のバリデーション
    if len(date_mmdd) != 4 or not date_mmdd.isdigit():
        print("Error: Date must be in MMDD format (e.g., 0108)")
        sys.exit(1)

    success = convert_pdf_to_images(date_mmdd)
    sys.exit(0 if success else 1)
