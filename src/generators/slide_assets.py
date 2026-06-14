"""slide_assets.py — shared image-extraction workflows for daily slide generation.

Replaces the per-day tmp_gen_*_images.py and tmp_gen_*_html.py one-offs.
Two public entry-points:
  - generate_slide_images()     : write JPEGs to disk, return paths
  - generate_slide_images_b64() : same conversion, return base64 strings
  - inspect_pdf()               : debug helper (replaces tmp_inspect_pdf.py)

CLI:
  python -m src.generators.slide_assets --mmdd 0615 [--pdf ...] [--cover ...]
"""
from __future__ import annotations

import argparse
import base64
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

# ── defaults (match majority-observed constants across tmp_* files) ────────────
DEFAULT_PDF_SCALE: float = 1.5          # fitz.Matrix(scale, scale)
DEFAULT_COVER_QUALITY: int = 80
DEFAULT_PAGE_QUALITY: int = 75
DEFAULT_MAX_COVER_WIDTH: int = 1600     # 0 = no cap


# ── helpers ───────────────────────────────────────────────────────────────────

def _repo_root() -> Path:
    """Return the repository root (two levels up from this file's package)."""
    return Path(__file__).resolve().parent.parent.parent


def _resolve_pdf(mmdd: str, pdf_path: Optional[str]) -> Optional[Path]:
    if pdf_path:
        return Path(pdf_path)
    # Try the canonical single-PDF pattern: input/day/{mmdd}.pdf
    candidate = _repo_root() / "input" / "day" / f"{mmdd}.pdf"
    if candidate.exists():
        return candidate
    # Glob for input/day/{mmdd}-*.pdf (common pattern for titled PDFs)
    matches = sorted((_repo_root() / "input" / "day").glob(f"{mmdd}-*.pdf"))
    if matches:
        return matches[0]
    return None


def _resolve_cover(mmdd: str, cover_png: Optional[str]) -> Optional[Path]:
    if cover_png:
        return Path(cover_png)
    candidate = _repo_root() / "input" / "day" / f"{mmdd}.png"
    if candidate.exists():
        return candidate
    # Also try glob for dated variants: 0524-*.png
    matches = sorted((_repo_root() / "input" / "day").glob(f"{mmdd}-*.png"))
    if matches:
        return matches[0]
    return None


def _convert_cover(cover_src: Path, out_path: Path, quality: int,
                   max_width: int) -> None:
    """Open cover PNG, optionally resize, save as JPEG."""
    from PIL import Image  # type: ignore

    img = Image.open(cover_src).convert("RGB")
    if max_width > 0 and img.width > max_width:
        new_h = int(img.height * max_width / img.width)
        img = img.resize((max_width, new_h), Image.LANCZOS)
    img.save(out_path, "JPEG", quality=quality, optimize=True)


def _convert_pdf_pages(pdf_src: Path, out_dir: Path, scale: float,
                       quality: int, page_prefix: str = "page_") -> list[str]:
    """Rasterise each PDF page to JPEG; return list of absolute path strings."""
    import fitz  # type: ignore
    from PIL import Image  # type: ignore

    doc = fitz.open(str(pdf_src))
    mat = fitz.Matrix(scale, scale)
    page_paths: list[str] = []
    for i in range(doc.page_count):
        page = doc[i]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        fname = out_dir / f"{page_prefix}{i + 1:02d}.jpg"
        img.save(fname, "JPEG", quality=quality, optimize=True)
        page_paths.append(str(fname.resolve()))
    doc.close()
    return page_paths


# ── public API ────────────────────────────────────────────────────────────────

def generate_slide_images(
    mmdd: str,
    *,
    pdf_path: Optional[str] = None,
    cover_png: Optional[str] = None,
    out_dir: Optional[str] = None,
    scale: float = DEFAULT_PDF_SCALE,
    cover_quality: int = DEFAULT_COVER_QUALITY,
    page_quality: int = DEFAULT_PAGE_QUALITY,
    max_cover_width: int = DEFAULT_MAX_COVER_WIDTH,
) -> dict[str, object]:
    """Cover PNG + PDF pages -> JPEGs on disk.

    Returns {"cover": "<abs>", "pages": ["<abs>", ...]}.

    Defaults:
      out_dir  = presentations/day_slides/images/{mmdd}
      pdf      = input/day/{mmdd}.pdf  (or first input/day/{mmdd}-*.pdf)
      cover    = input/day/{mmdd}.png
    Page files are named page_01.jpg .. page_NN.jpg.
    """
    root = _repo_root()
    dest = Path(out_dir) if out_dir else (
        root / "presentations" / "day_slides" / "images" / mmdd
    )
    dest.mkdir(parents=True, exist_ok=True)

    result: dict[str, object] = {"cover": None, "pages": []}

    # Cover
    cover_src = _resolve_cover(mmdd, cover_png)
    if cover_src and cover_src.exists():
        cover_out = dest / "cover.jpg"
        _convert_cover(cover_src, cover_out, cover_quality, max_cover_width)
        result["cover"] = str(cover_out.resolve())

    # PDF pages
    pdf_src = _resolve_pdf(mmdd, pdf_path)
    if pdf_src and pdf_src.exists():
        result["pages"] = _convert_pdf_pages(pdf_src, dest, scale, page_quality)

    return result


def generate_slide_images_b64(
    mmdd: str,
    *,
    pdf_path: Optional[str] = None,
    cover_png: Optional[str] = None,
    tmp_dir: Optional[str] = None,
    scale: float = DEFAULT_PDF_SCALE,
    cover_quality: int = DEFAULT_COVER_QUALITY,
    page_quality: int = DEFAULT_PAGE_QUALITY,
) -> dict[str, object]:
    """Same conversion as generate_slide_images(), but returns base64 strings.

    Returns {"cover": "<b64>", "pages": ["<b64>", ...]}.
    tmp_dir defaults to tempfile.mkdtemp() and is removed before return.
    """
    cleanup = tmp_dir is None
    work_dir = tmp_dir or tempfile.mkdtemp(prefix=f"slide_assets_{mmdd}_")
    try:
        disk = generate_slide_images(
            mmdd,
            pdf_path=pdf_path,
            cover_png=cover_png,
            out_dir=work_dir,
            scale=scale,
            cover_quality=cover_quality,
            page_quality=page_quality,
            max_cover_width=0,  # no cap — caller decides via quality
        )

        def to_b64(path: Optional[str]) -> Optional[str]:
            if not path:
                return None
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()

        return {
            "cover": to_b64(disk.get("cover")),
            "pages": [to_b64(p) for p in (disk.get("pages") or [])],
        }
    finally:
        if cleanup:
            shutil.rmtree(work_dir, ignore_errors=True)


def inspect_pdf(pdf_path: str, chars_per_page: int = 500) -> None:
    """Print page count + first N chars of text per page.

    Replaces tmp_inspect_pdf.py / tmp_inspect_0512.py / tmp_inspect_0513.py.
    """
    import fitz  # type: ignore

    doc = fitz.open(pdf_path)
    print(f"Pages: {doc.page_count}")
    for i in range(doc.page_count):
        text = doc[i].get_text()
        print(f"\n=== p{i + 1} ({len(text)} chars) ===")
        print(text[:chars_per_page])
    doc.close()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli() -> None:
    """python -m src.generators.slide_assets --mmdd 0615 [--pdf ...] [--cover ...]"""
    parser = argparse.ArgumentParser(
        description="Generate slide images (disk or base64) from PDF + PNG cover.",
        prog="python -m src.generators.slide_assets",
    )
    parser.add_argument("--mmdd", required=True, help="Date string, e.g. 0615")
    parser.add_argument("--pdf", default=None, help="Override PDF path")
    parser.add_argument("--cover", default=None, help="Override cover PNG path")
    parser.add_argument("--out-dir", default=None, help="Override output directory")
    parser.add_argument(
        "--b64", action="store_true",
        help="Return base64 strings instead of writing to disk",
    )
    parser.add_argument(
        "--inspect", action="store_true",
        help="Inspect PDF text content instead of converting images",
    )
    parser.add_argument(
        "--chars", type=int, default=500,
        help="Chars per page for --inspect (default 500)",
    )
    parser.add_argument(
        "--scale", type=float, default=DEFAULT_PDF_SCALE,
        help=f"PDF rasterise scale (default {DEFAULT_PDF_SCALE})",
    )
    parser.add_argument(
        "--cover-quality", type=int, default=DEFAULT_COVER_QUALITY,
        help=f"JPEG quality for cover (default {DEFAULT_COVER_QUALITY})",
    )
    parser.add_argument(
        "--page-quality", type=int, default=DEFAULT_PAGE_QUALITY,
        help=f"JPEG quality for pages (default {DEFAULT_PAGE_QUALITY})",
    )

    args = parser.parse_args()

    if args.inspect:
        pdf = args.pdf or str(
            _repo_root() / "input" / "day" / f"{args.mmdd}.pdf"
        )
        inspect_pdf(pdf, chars_per_page=args.chars)
        return

    if args.b64:
        result = generate_slide_images_b64(
            args.mmdd,
            pdf_path=args.pdf,
            cover_png=args.cover,
            scale=args.scale,
            cover_quality=args.cover_quality,
            page_quality=args.page_quality,
        )
        has_cover = result["cover"] is not None
        page_count = len(result.get("pages") or [])
        print(f"cover: {'ok' if has_cover else 'none'}, pages: {page_count}")
    else:
        result = generate_slide_images(
            args.mmdd,
            pdf_path=args.pdf,
            cover_png=args.cover,
            out_dir=args.out_dir,
            scale=args.scale,
            cover_quality=args.cover_quality,
            page_quality=args.page_quality,
        )
        print(f"cover: {result['cover']}")
        for p in result.get("pages") or []:
            print(f"  page: {p}")


if __name__ == "__main__":
    _cli()
