import os
import pypdfium2 as pdfium
from PIL import Image

def convert_pdf_to_images(pdf_path, output_dir, prefix="slide"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    pdf = pdfium.PdfDocument(pdf_path)
    n_pages = len(pdf)
    
    print(f"Converting {n_pages} pages from {pdf_path}...")
    
    image_paths = []
    
    for i in range(n_pages):
        page = pdf[i]
        # Render the page to a bitmap
        # scale=2 for better quality (2x standard 72dpi = 144dpi approx, good for web)
        bitmap = page.render(scale=2) 
        pil_image = bitmap.to_pil()
        
        output_filename = f"{prefix}_{i+1:03d}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Convert to RGB to save as JPG
        pil_image = pil_image.convert("RGB")
        pil_image.save(output_path, "JPEG", quality=90)
        
        image_paths.append(output_filename)
        print(f"Saved {output_path}")
        
    return image_paths

if __name__ == "__main__":
    # 変換したいPDFファイルのパス
    pdf_path = r"input/day/1220-Agent_Skills_Workflow_Design.pdf"
    
    # 画像の出力先フォルダ
    output_dir = r"input/day/1220_slides"
    
    try:
        images = convert_pdf_to_images(pdf_path, output_dir)
        print(f"Successfully created {len(images)} images.")
    except Exception as e:
        print(f"Error: {e}")
