import fitz  # PyMuPDF
import os

def convert_pdf_to_images(pdf_path, output_folder):
    # PDFファイルが開けるか確認
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return

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
    pdf_file = "input/day/1228-Code_Is_Written_While_You_Sleep.pdf"
    output_dir = "input/day/1228_slides"
    
    convert_pdf_to_images(pdf_file, output_dir)
