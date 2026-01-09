#!/usr/bin/env python3
"""Render PPTX slides to images using Aspose.Slides"""
import sys
from pathlib import Path

def render_pptx_slides(pptx_path, output_dir):
    """Convert PPTX to images"""
    try:
        import aspose.slides as slides

        prs = slides.Presentation(str(pptx_path))
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        # Set output dimensions (scale for better quality)
        scale_x = 2.0
        scale_y = 2.0

        for i, slide in enumerate(prs.slides, 1):
            output_file = output_dir / f"slide_{i:03d}.jpg"

            # Render slide to bitmap
            with slide.get_image(scale_x, scale_y) as bmp:
                # Save directly to file
                bmp.save(str(output_file))

            print(f"Created: {output_file}")

        print(f"\nTotal slides rendered: {len(prs.slides)}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    pptx_file = Path("D:/ai-news-site-main/input/day/0106-2.pptx")
    output_dir = Path("D:/ai-news-site-main/input/day/0106_slides")

    if not pptx_file.exists():
        print(f"Error: {pptx_file} not found")
        return 1

    print(f"Converting: {pptx_file}")
    print(f"Output: {output_dir}\n")

    success = render_pptx_slides(pptx_file, output_dir)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
