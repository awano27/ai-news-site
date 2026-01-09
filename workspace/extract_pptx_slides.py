#!/usr/bin/env python3
"""
Extract slide images from PPTX file
Uses python-pptx to read PPTX and Pillow to create thumbnails
"""
import os
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
from PIL import Image, ImageDraw, ImageFont
import io

def extract_slide_count(pptx_path):
    """Get the number of slides in PPTX"""
    prs = Presentation(pptx_path)
    return len(prs.slides)

def main():
    pptx_file = Path("D:/ai-news-site-main/input/day/0106-2.pptx")

    if not pptx_file.exists():
        print(f"Error: {pptx_file} not found")
        return 1

    try:
        slide_count = extract_slide_count(pptx_file)
        print(f"PPTX file: {pptx_file}")
        print(f"Total slides: {slide_count}")

        # Since we can't render PPTX directly to images without PowerPoint/LibreOffice,
        # we'll need to use an alternative approach
        print("\nNote: Direct PPTX to image conversion requires PowerPoint or LibreOffice.")
        print("Please convert the PPTX to PDF manually, then use pdftoppm to create images.")

    except Exception as e:
        print(f"Error reading PPTX: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
