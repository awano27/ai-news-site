#!/usr/bin/env python3
"""
Extract images from PPTX file
PPTX files are ZIP archives - we can extract media directly
"""
import zipfile
import shutil
from pathlib import Path

def extract_pptx_media(pptx_path, output_dir):
    """Extract all media files from PPTX"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    count = 0
    try:
        with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
            # List all files in the archive
            for file_info in zip_ref.filelist:
                # Extract files from ppt/media/ folder
                if file_info.filename.startswith('ppt/media/'):
                    filename = Path(file_info.filename).name
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.emf', '.wmf')):
                        # Extract the file
                        source = zip_ref.open(file_info)
                        target_path = output_dir / filename
                        with open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        print(f"Extracted: {filename}")
                        count += 1

        print(f"\nTotal images extracted: {count}")
        print(f"Output directory: {output_dir}")

    except Exception as e:
        print(f"Error: {e}")
        return False

    return True

def main():
    pptx_file = "D:/ai-news-site-main/input/day/0106-2.pptx"
    output_dir = "D:/ai-news-site-main/workspace/pptx_media"

    if not Path(pptx_file).exists():
        print(f"Error: {pptx_file} not found")
        return 1

    extract_pptx_media(pptx_file, output_dir)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
