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
        bitmap = page.render(scale=2) 
        pil_image = bitmap.to_pil()
        
        output_filename = f"{prefix}_{i+1:03d}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        pil_image = pil_image.convert("RGB")
        pil_image.save(output_path, "JPEG", quality=90)
        
        image_paths.append(output_filename)
        print(f"Saved {output_path}")
        
    return image_paths

if __name__ == "__main__":
    pdf_path = r"input/day/1222-Japan_AI_Counteroffensive_The_3_Trillion_Yen_Strategy.pdf"
    output_dir = r"input/day/1222_slides"
    
    try:
        if os.path.exists(pdf_path):
            images = convert_pdf_to_images(pdf_path, output_dir)
            print(f"Successfully created {len(images)} images.")
        else:
            print(f"File not found: {pdf_path}. Please place the PDF file.")
    except Exception as e:
        print(f"Error: {e}")
