#!/usr/bin/env python3
"""Shrink published slide images without renaming or deleting anything.

The GitHub Pages artifact must stay under 1 GB. Day-slide covers and page
images are committed at generator resolution (often 2752px wide), and many
slide pages inline the same kind of image as base64. This script rewrites both
in place:

* ``*.jpg`` / ``*.jpeg`` under the image roots: resize to ``--max-width`` and
  re-encode as progressive JPEG at ``--quality``.
* ``*.png`` under the image roots: resize to ``--max-width`` and re-save with
  PNG optimisation. PNG stays PNG, so transparency survives.
* ``data:image/jpeg;base64`` and alpha-free ``data:image/png;base64`` payloads
  inside ``*.html`` under the slide root: decoded, re-encoded the same way, and
  re-embedded as ``data:image/jpeg``.
* ``downloads/*.pptx``: alpha-free PNG media become JPEG media (relationship
  targets and content types updated), JPEG media are re-encoded. The result is
  written only when python-pptx, if installed, can read every picture back.

Every re-encoded JPEG carries the comment ``MARKER`` so a second run skips it.
File names, URLs, and HTML structure do not change.

Run:
    python scripts/compress_site_images.py            # presentations/day_slides
    python scripts/compress_site_images.py --dry-run  # report only
"""
from __future__ import annotations

import argparse
import base64
import io
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageOps

MARKER = b"visionhub-opt:v1"
DEFAULT_MAX_WIDTH = 2560
DEFAULT_QUALITY = 80
MIN_INLINE_BYTES = 100_000
DATA_URI_RE = re.compile(rb"data:image/(jpeg|png);base64,([A-Za-z0-9+/=]+)")
JPEG_SUFFIXES = frozenset({".jpg", ".jpeg"})


@dataclass
class Stats:
    files: int = 0
    before: int = 0
    after: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def add(self, before: int, after: int) -> None:
        self.files += 1
        self.before += before
        self.after += after


def _is_marked(data: bytes) -> bool:
    return MARKER in data[:4096]


def _encode_jpeg(image: Image.Image, max_width: int, quality: int) -> bytes:
    image = ImageOps.exif_transpose(image)
    if image.size[0] > max_width:
        height = round(image.size[1] * max_width / image.size[0])
        image = image.resize((max_width, height), Image.LANCZOS)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    out = io.BytesIO()
    image.save(
        out,
        "JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        comment=MARKER,
        icc_profile=image.info.get("icc_profile"),
    )
    return out.getvalue()


def _encode_png(image: Image.Image, max_width: int) -> bytes:
    image = ImageOps.exif_transpose(image)
    if image.size[0] > max_width:
        height = round(image.size[1] * max_width / image.size[0])
        image = image.resize((max_width, height), Image.LANCZOS)
    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


def _has_alpha(image: Image.Image) -> bool:
    return image.mode in ("RGBA", "LA", "PA") or (
        image.mode == "P" and "transparency" in image.info
    )


def compress_image_file(path: Path, max_width: int, quality: int, dry_run: bool, stats: Stats) -> None:
    original = path.read_bytes()
    suffix = path.suffix.lower()
    try:
        if suffix in JPEG_SUFFIXES:
            if _is_marked(original):
                stats.skipped += 1
                return
            encoded = _encode_jpeg(Image.open(io.BytesIO(original)), max_width, quality)
        elif suffix == ".png":
            image = Image.open(io.BytesIO(original))
            if image.size[0] <= max_width:
                stats.skipped += 1
                return
            encoded = _encode_png(image, max_width)
        else:
            return
    except Exception as exc:  # noqa: BLE001 - report and keep going
        stats.errors.append(f"{path}: {exc}")
        return
    if len(encoded) >= len(original) and suffix == ".png":
        stats.skipped += 1
        return
    stats.add(len(original), len(encoded))
    if not dry_run:
        path.write_bytes(encoded)


def compress_inline_images(path: Path, max_width: int, quality: int, dry_run: bool, stats: Stats) -> None:
    original = path.read_bytes()
    changed = False
    before = after = 0

    def replace(match: re.Match[bytes]) -> bytes:
        nonlocal changed, before, after
        payload = match.group(2)
        if len(payload) < MIN_INLINE_BYTES:
            return match.group(0)
        try:
            raw = base64.b64decode(payload, validate=True)
        except ValueError:
            return match.group(0)
        if _is_marked(raw):
            return match.group(0)
        try:
            image = Image.open(io.BytesIO(raw))
            if _has_alpha(image):
                return match.group(0)
            encoded = _encode_jpeg(image, max_width, quality)
        except Exception as exc:  # noqa: BLE001
            stats.errors.append(f"{path} inline image: {exc}")
            return match.group(0)
        replacement = b"data:image/jpeg;base64," + base64.b64encode(encoded)
        if len(replacement) >= len(match.group(0)):
            return match.group(0)
        changed = True
        before += len(match.group(0))
        after += len(replacement)
        return replacement

    updated = DATA_URI_RE.sub(replace, original)
    if not changed:
        return
    stats.add(before, after)
    if not dry_run:
        path.write_bytes(updated)


CONTENT_TYPES_PART = "[Content_Types].xml"
JPEG_DEFAULT = b'<Default Extension="jpg" ContentType="image/jpeg"/>'


def _rewrite_pptx(original: bytes, max_width: int, quality: int, stats: Stats) -> bytes | None:
    """Return the pptx with alpha-free PNG media re-encoded as JPEG, or None if unchanged.

    Media parts are renamed ``imageN.png`` -> ``imageN.jpg``; every ``.rels``
    part and ``[Content_Types].xml`` are updated to match. JPEG media are
    re-encoded in place. PNG media with transparency only get resized.
    """
    renamed: dict[str, str] = {}
    parts: list[tuple[str, bytes]] = []
    changed = False
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        names = set(archive.namelist())
        for info in archive.infolist():
            data = archive.read(info)
            name = info.filename
            suffix = Path(name).suffix.lower()
            if name.startswith("ppt/media/") and suffix in JPEG_SUFFIXES | {".png"}:
                try:
                    image = Image.open(io.BytesIO(data))
                    if suffix == ".png" and not _has_alpha(image):
                        target = name[: -len(suffix)] + ".jpg"
                        if target not in names:
                            data = _encode_jpeg(image, max_width, quality)
                            renamed[name] = target
                            name = target
                            changed = True
                    elif suffix == ".png":
                        if image.size[0] > max_width:
                            data = _encode_png(image, max_width)
                            changed = True
                    elif not _is_marked(data):
                        data = _encode_jpeg(image, max_width, quality)
                        changed = True
                except Exception as exc:  # noqa: BLE001
                    stats.errors.append(f"pptx media {name}: {exc}")
            parts.append((name, data))
    if not changed:
        return None
    old_basenames = {Path(old).name.encode(): Path(new).name.encode() for old, new in renamed.items()}
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in parts:
            if name.endswith(".rels") or name == CONTENT_TYPES_PART:
                for old, new in old_basenames.items():
                    data = data.replace(old, new)
                if name == CONTENT_TYPES_PART and renamed and b'Extension="jpg"' not in data:
                    data = data.replace(b"<Default ", JPEG_DEFAULT + b"<Default ", 1)
            archive.writestr(name, data, zipfile.ZIP_DEFLATED)
    return out.getvalue()


def _pptx_loads(data: bytes) -> str | None:
    """Return an error string when python-pptx cannot read every picture, else None."""
    try:
        from pptx import Presentation
    except ImportError:
        return None
    try:
        presentation = Presentation(io.BytesIO(data))
        for slide in presentation.slides:
            for shape in slide.shapes:
                if shape.shape_type == 13:
                    _ = shape.image.blob
    except Exception as exc:  # noqa: BLE001
        return str(exc)
    return None


def compress_pptx(path: Path, max_width: int, quality: int, dry_run: bool, stats: Stats) -> None:
    original = path.read_bytes()
    rewritten = _rewrite_pptx(original, max_width, quality, stats)
    if rewritten is None or len(rewritten) >= len(original):
        stats.skipped += 1
        return
    error = _pptx_loads(rewritten)
    if error:
        stats.errors.append(f"{path}: rewritten pptx does not load: {error}")
        return
    stats.add(len(original), len(rewritten))
    if not dry_run:
        path.write_bytes(rewritten)


def _mb(value: int) -> str:
    return f"{value / 1_000_000:.1f} MB"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--slides",
        default="presentations/day_slides",
        help="Directory whose *.html gets inline images re-encoded and whose images/ tree gets re-encoded",
    )
    parser.add_argument("--max-width", type=int, default=DEFAULT_MAX_WIDTH)
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    slides = (args.root / args.slides).resolve()
    if not slides.is_dir():
        print(f"slide directory does not exist: {slides}", file=sys.stderr)
        return 1

    files = Stats()
    for path in sorted((slides / "images").rglob("*")):
        if path.is_file() and path.suffix.lower() in JPEG_SUFFIXES | {".png"}:
            compress_image_file(path, args.max_width, args.quality, args.dry_run, files)

    inline = Stats()
    for path in sorted(slides.glob("*.html")):
        compress_inline_images(path, args.max_width, args.quality, args.dry_run, inline)

    decks = Stats()
    for path in sorted((slides / "downloads").glob("*.pptx")):
        compress_pptx(path, args.max_width, args.quality, args.dry_run, decks)

    mode = "would rewrite" if args.dry_run else "rewrote"
    print(
        f"image files: {mode} {files.files}, skipped {files.skipped}: "
        f"{_mb(files.before)} -> {_mb(files.after)}"
    )
    print(
        f"inline images: {mode} {inline.files} html files: "
        f"{_mb(inline.before)} -> {_mb(inline.after)}"
    )
    print(
        f"pptx downloads: {mode} {decks.files}, skipped {decks.skipped}: "
        f"{_mb(decks.before)} -> {_mb(decks.after)}"
    )
    saved = sum(s.before - s.after for s in (files, inline, decks))
    print(f"total saved: {_mb(saved)}")
    errors = files.errors + inline.errors + decks.errors
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
