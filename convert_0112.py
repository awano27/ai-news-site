import fitz  # PyMuPDF
import os
import glob

def convert_pdf_to_images(output_folder):
    """Convert PDF slides to images"""

    # Find the PDF file
    pdf_files = glob.glob("input/day/0112-*.pdf")
    if not pdf_files:
        print("No PDF file found matching pattern 0112-*.pdf")
        return

    pdf_path = pdf_files[0]
    print(f"Converting: {pdf_path}")

    # Create output folder
    os.makedirs(output_folder, exist_ok=True)

    # Open PDF and convert each page
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # High resolution rendering (2x zoom)
        zoom = 2
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Save as JPEG
        output_path = os.path.join(output_folder, f"slide_{page_num + 1:03d}.jpg")
        pix.save(output_path)
        print(f"Saved: {output_path}")

    doc.close()
    print(f"\nConverted {len(doc)} pages to {output_folder}")

if __name__ == "__main__":
    convert_pdf_to_images("input/day/0112_slides")
