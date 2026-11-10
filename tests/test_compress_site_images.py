from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from scripts.compress_site_images import MARKER, main

pptx = pytest.importorskip("pptx", reason="python-pptx exercises the deck rewrite")
from pptx.util import Inches  # noqa: E402


def _noise_image(width: int, height: int, mode: str = "RGB") -> Image.Image:
    import random

    rng = random.Random(width * height)
    image = Image.new(mode, (width, height))
    image.putdata([tuple(rng.randrange(256) for _ in range(len(mode))) for _ in range(width * height)])
    return image


def _jpeg_bytes(width: int, height: int, quality: int = 95) -> bytes:
    out = io.BytesIO()
    _noise_image(width, height).save(out, "JPEG", quality=quality)
    return out.getvalue()


def _png_bytes(width: int, height: int, mode: str = "RGB") -> bytes:
    out = io.BytesIO()
    _noise_image(width, height, mode).save(out, "PNG")
    return out.getvalue()


def _slides(tmp_path: Path) -> Path:
    slides = tmp_path / "presentations" / "day_slides"
    (slides / "images" / "0101").mkdir(parents=True)
    (slides / "downloads").mkdir()
    return slides


def test_jpeg_files_are_resized_marked_and_skipped_on_rerun(tmp_path):
    slides = _slides(tmp_path)
    cover = slides / "images" / "0101" / "cover.jpg"
    cover.write_bytes(_jpeg_bytes(400, 200))
    original_size = cover.stat().st_size

    assert main(["--root", str(tmp_path), "--max-width", "200", "--quality", "80"]) == 0

    shrunk = cover.read_bytes()
    assert len(shrunk) < original_size
    assert MARKER in shrunk
    assert Image.open(io.BytesIO(shrunk)).size == (200, 100)
    assert cover.name == "cover.jpg"

    assert main(["--root", str(tmp_path), "--max-width", "200", "--quality", "80"]) == 0
    assert cover.read_bytes() == shrunk


def test_transparent_png_keeps_alpha_and_is_only_resized(tmp_path):
    slides = _slides(tmp_path)
    logo = slides / "images" / "0101" / "logo.png"
    logo.write_bytes(_png_bytes(400, 100, "RGBA"))

    assert main(["--root", str(tmp_path), "--max-width", "200"]) == 0

    image = Image.open(logo)
    assert image.mode == "RGBA"
    assert image.size == (200, 50)


def test_inline_images_are_reencoded_without_touching_markup(tmp_path):
    slides = _slides(tmp_path)
    payload = base64.b64encode(_jpeg_bytes(600, 300)).decode()
    small = base64.b64encode(_jpeg_bytes(20, 10)).decode()
    page = slides / "day_slide_2099_01_01.html"
    page.write_text(
        "<html><body><h1>日本語の見出し</h1>"
        f'<img src="data:image/jpeg;base64,{payload}" alt="a">'
        f'<img src="data:image/jpeg;base64,{small}" alt="b"></body></html>',
        encoding="utf-8",
    )
    before = page.stat().st_size

    assert main(["--root", str(tmp_path), "--max-width", "300"]) == 0

    text = page.read_text(encoding="utf-8")
    assert page.stat().st_size < before
    assert text.startswith("<html><body><h1>日本語の見出し</h1>")
    assert text.count('<img src="data:image/jpeg;base64,') == 2
    assert small in text
    new_payload = text.split('base64,', 1)[1].split('"', 1)[0]
    assert Image.open(io.BytesIO(base64.b64decode(new_payload))).size == (300, 150)


def test_pptx_png_media_become_jpeg_and_deck_still_loads(tmp_path):
    slides = _slides(tmp_path)
    deck = pptx.Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.shapes.add_picture(io.BytesIO(_png_bytes(800, 400)), Inches(0), Inches(0), width=Inches(5))
    slide.shapes.add_picture(io.BytesIO(_png_bytes(100, 100, "RGBA")), Inches(5), Inches(0), width=Inches(1))
    path = slides / "downloads" / "deck.pptx"
    deck.save(path)
    before = path.stat().st_size

    assert main(["--root", str(tmp_path), "--max-width", "400"]) == 0

    assert path.stat().st_size < before
    with zipfile.ZipFile(path) as archive:
        media = sorted(name for name in archive.namelist() if name.startswith("ppt/media/"))
        assert [Path(name).suffix for name in media] == [".jpg", ".png"]
        assert b'Extension="jpg"' in archive.read("[Content_Types].xml")
        rels = b"".join(archive.read(name) for name in archive.namelist() if name.endswith(".rels"))
        assert b"image1.png" not in rels
    reloaded = pptx.Presentation(str(path))
    pictures = [shape for shape in reloaded.slides[0].shapes if shape.shape_type == 13]
    assert len(pictures) == 2
    assert {picture.image.content_type for picture in pictures} == {"image/jpeg", "image/png"}
    assert Image.open(io.BytesIO(pictures[0].image.blob)).size[0] <= 400
