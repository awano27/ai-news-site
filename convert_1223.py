import os
import pypdfium2 as pdfium
from PIL import Image
from pathlib import Path

def convert_pdf_to_images(pdf_path, output_dir):
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    
    pdf = pdfium.PdfDocument(pdf_path)
    n_pages = len(pdf)
    print(f"Total pages: {n_pages}")

    for i in range(n_pages):
        page = pdf[i]
        # Render with high scale for better quality
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        
        # Save as JPG
        image_path = os.path.join(output_dir, f"slide_{i+1:03d}.jpg")
        pil_image.save(image_path, "JPEG", quality=85)
        print(f"Saved: {image_path}")

    pdf.close()

if __name__ == "__main__":
    pdf_file = "input/day/1223-Context_Engineering (1).pdf"
    output_folder = "input/day/1223_slides"
    convert_pdf_to_images(pdf_file, output_folder)
