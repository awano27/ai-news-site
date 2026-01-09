#!/usr/bin/env python3
"""Convert PPTX to PDF using comtypes (Windows COM)"""
import sys
import os
from pathlib import Path

def convert_pptx_to_pdf(pptx_path, pdf_path):
    """Convert PPTX to PDF using PowerPoint COM interface"""
    try:
        import comtypes.client
    except ImportError:
        print("Error: comtypes module not found. Install with: pip install comtypes")
        return False

    pptx_path = str(Path(pptx_path).absolute())
    pdf_path = str(Path(pdf_path).absolute())

    try:
        print(f"Opening PowerPoint...")
        powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
        powerpoint.Visible = 1

        print(f"Opening presentation: {pptx_path}")
        presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)

        print(f"Saving as PDF: {pdf_path}")
        presentation.SaveAs(pdf_path, 32)  # 32 = ppSaveAsPDF

        print("Closing presentation...")
        presentation.Close()
        powerpoint.Quit()

        print(f"Success! PDF created: {pdf_path}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        print("PowerPoint may not be installed or COM automation failed.")
        return False

def main():
    pptx_file = "D:/ai-news-site-main/input/day/0106-2.pptx"
    pdf_file = "D:/ai-news-site-main/workspace/0106.pdf"

    if not Path(pptx_file).exists():
        print(f"Error: {pptx_file} not found")
        return 1

    success = convert_pptx_to_pdf(pptx_file, pdf_file)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
