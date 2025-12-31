import fitz  # PyMuPDF
import os
import glob

def convert_pdf_to_images(output_folder):
    # Find PDF file for 1231
    pdf_files = glob.glob("input/day/1231-*.pdf")
    if not pdf_files:
        print("Error: No PDF file found for 1231 in input/day/")
        return
    
    pdf_path = pdf_files[0]
    print(f"Found PDF: {pdf_path}")

    # 出力フォルダが存在しない場合は作成
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # PDFを開く
    doc = fitz.open(pdf_path)
    
    print(f"Converting {pdf_path} to images...")
    print(f"Total pages: {len(doc)}")

    for i, page in enumerate(doc):
        # 高解像度でレンダリング (zoom_x=2, zoom_y=2 で2倍の解像度)
        zoom = 2
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # 画像を保存 (slide_001.jpg, slide_002.jpg...)
        output_filename = f"slide_{i+1:03d}.jpg"
        output_path = os.path.join(output_folder, output_filename)
        pix.save(output_path)
        print(f"Saved {output_path}")

    print("Conversion complete!")

if __name__ == "__main__":
    # 設定
    output_dir = "input/day/1231_slides"
    
    convert_pdf_to_images(output_dir)
