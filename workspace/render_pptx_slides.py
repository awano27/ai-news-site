#!/usr/bin/env python3
"""
Render PPTX slides to images using Aspose.Slides (trial version)
Alternative: Use online conversion or manual export
"""
import sys
from pathlib import Path

def try_aspose_conversion(pptx_path, output_dir):
    """Try using Aspose.Slides to convert PPTX to images"""
    try:
        import aspose.slides as slides

        prs = slides.Presentation(str(pptx_path))
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        for i, slide in enumerate(prs.slides, 1):
            output_file = output_dir / f"slide_{i:03d}.jpg"

            # Get slide as image
            with slide.get_thumbnail(2, 2) as img:
                img.save(str(output_file), slides.ImageFormat.JPEG)

            print(f"Created: {output_file}")

        print(f"\nTotal slides rendered: {len(prs.slides)}")
        return True

    except ImportError:
        print("Aspose.Slides not installed.")
        print("Install with: pip install aspose-slides")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    pptx_file = Path("D:/ai-news-site-main/input/day/0106-2.pptx")
    output_dir = Path("D:/ai-news-site-main/input/day/0106_slides")

    if not pptx_file.exists():
        print(f"Error: {pptx_file} not found")
        return 1

    print(f"Attempting to convert: {pptx_file}")
    print(f"Output directory: {output_dir}")
    print()

    success = try_aspose_conversion(pptx_file, output_dir)

    if not success:
        print("\n" + "="*60)
        print("Alternative methods:")
        print("1. Use PowerPoint: File → Export → Create Handouts → PDF")
        print("   Then use: pdftoppm -jpeg -r 150 file.pdf output")
        print()
        print("2. Use online converter:")
        print("   - https://www.ilovepdf.com/powerpoint_to_pdf")
        print("   - Upload PPTX, download PDF, then convert with pdftoppm")
        print("="*60)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
