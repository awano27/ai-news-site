#!/usr/bin/env python3
"""Bring back the images that old day slides load from input/day/.

input/ left the public repository on 2026-04-18 and is denied from the Pages
artifact, so every <img src="../../input/day/..."> in a day slide is a 404.
This copies each image out of a checkout that still has input/day/, re-encoded
small, to presentations/day_slides/images/legacy/, and points the slide at it,
in src and in onerror fallbacks alike.
A PDF download link into input/day/ is removed unless the PDF is in the
repository: the missing PDFs total 670 MB and do not fit in the 1 GB artifact.

A slide with no input/day/ reference is left alone, so rerunning is a no-op
and needs no source checkout.

Usage:
    python scripts/restore_day_slide_legacy_images.py --source C:/develop/ai-news-site
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.compress_site_images import _encode_jpeg  # noqa: E402

SLIDES_DIR = ROOT / "presentations" / "day_slides"
LEGACY_DIR = SLIDES_DIR / "images" / "legacy"
MAX_WIDTH = 1600
QUALITY = 80

IMAGE_REF_RE = re.compile(r"\.\./\.\./input/day/([A-Za-z0-9_\-/]+\.(?:jpe?g|png))", re.IGNORECASE)
PDF_LINK_RE = re.compile(
    r"""<a\b[^>]*?\bhref=["']\.\./\.\./(input/day/[^"']+\.pdf)["'][^>]*>.*?</a>""",
    re.DOTALL | re.IGNORECASE,
)


def restore(slide: Path, source_input: Path | None, unresolved: list[str]) -> tuple[int, int]:
    html = slide.read_text(encoding="utf-8")

    def repoint(match: re.Match[str]) -> str:
        rel = match.group(1)
        published = Path(rel).with_suffix(".jpg")
        target = LEGACY_DIR / published
        if not target.exists():
            origin = source_input / rel if source_input else None
            if origin is None or not origin.is_file():
                unresolved.append(f"{slide.name}: input/day/{rel}")
                return match.group(0)
            target.parent.mkdir(parents=True, exist_ok=True)
            image = Image.open(io.BytesIO(origin.read_bytes()))
            target.write_bytes(_encode_jpeg(image, MAX_WIDTH, QUALITY))
        return f"images/legacy/{published.as_posix()}"

    html, images = IMAGE_REF_RE.subn(repoint, html)
    pdf_links = 0

    def drop_dead_link(match: re.Match[str]) -> str:
        nonlocal pdf_links
        if (ROOT / unquote(match.group(1))).is_file():
            return match.group(0)
        pdf_links += 1
        return ""

    html = PDF_LINK_RE.sub(drop_dead_link, html)
    if images or pdf_links:
        slide.write_text(html, encoding="utf-8", newline="")
    return images, pdf_links


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, help="Checkout that still has input/day/")
    args = ap.parse_args(argv)
    source_input = args.source / "input" / "day" if args.source else None

    unresolved: list[str] = []
    images = pdf_links = slides = 0
    for slide in sorted(SLIDES_DIR.glob("*.html")):
        found_images, found_links = restore(slide, source_input, unresolved)
        images += found_images
        pdf_links += found_links
        slides += bool(found_images or found_links)
    images -= len(unresolved)
    print(f"[restore_day_slide_legacy_images] {slides} slides touched, "
          f"{images} images repointed, {pdf_links} PDF links removed, {len(unresolved)} unresolved")
    for line in unresolved:
        print(f"  unresolved {line}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
