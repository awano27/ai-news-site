import os
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image

def convert_pdf_to_images(pdf_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pdf = pdfium.PdfDocument(pdf_path)
    n_pages = len(pdf)
    print(f"Total pages: {n_pages}")
    
    for i in range(n_pages):
        page = pdf[i]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        
        image_path = os.path.join(output_dir, f"slide_{i+1:03d}.jpg")
        pil_image.save(image_path, "JPEG", quality=85)
        print(f"Saved: {image_path}")
    
    pdf.close()

if __name__ == "__main__":
    pdf_file = "input/day/1227-The_Ultimate_Tutor_Story.pdf"
    output_folder = "input/day/1227_slides"
    
    if os.path.exists(pdf_file):
        convert_pdf_to_images(pdf_file, output_folder)
    else:
        print(f"PDF not found: {pdf_file}")
