#!/usr/bin/env python3
"""
Convert PPTX slides to images using Playwright screenshot
"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def html_to_image(html_file, output_file, width=1920, height=1080):
    """Convert HTML file to image using Playwright"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': width, 'height': height})

        # Load HTML file
        file_path = Path(html_file).absolute()
        page.goto(f'file://{file_path}')

        # Wait for any animations/loading
        page.wait_for_timeout(1000)

        # Take screenshot
        page.screenshot(path=output_file, full_page=False)

        browser.close()
        print(f"Created: {output_file}")

def main():
    workspace = Path("D:/ai-news-site-main/workspace")
    output_dir = Path("D:/ai-news-site-main/input/day/0106_slides")
    output_dir.mkdir(exist_ok=True)

    # Convert each HTML slide to image
    slides = [
        workspace / "slide1.html",
        workspace / "slide2.html",
        workspace / "slide3.html",
        workspace / "slide4.html",
        workspace / "slide5.html"
    ]

    for i, slide_file in enumerate(slides, 1):
        if slide_file.exists():
            output_file = output_dir / f"slide_{i:03d}.jpg"
            html_to_image(str(slide_file), str(output_file), width=1920, height=1080)
        else:
            print(f"Warning: {slide_file} not found")

    print(f"\nAll slides converted to {output_dir}")

if __name__ == "__main__":
    main()
