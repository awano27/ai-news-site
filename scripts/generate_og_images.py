#!/usr/bin/env python3
"""Generate OG images (1200x630 PNG) for visionhub.jp pages.

Uses Pillow + Noto Sans JP — no browser needed, so it scales to all
278 slides in under a minute. For each ``presentations/day_slides/
day_slide_YYYY_MM_DD.html`` we emit ``assets/og/day_slide_YYYY_MM_DD.png``.
Also creates ``assets/og/default.png`` (used by non-slide pages).

Re-running is idempotent: the image is regenerated only when the slide's
<title> changes relative to the previous run (hash cache), or when
``--force`` is passed.

Usage:
    python scripts/generate_og_images.py                # generate missing/changed
    python scripts/generate_og_images.py --force        # regenerate all
    python scripts/generate_og_images.py --latest 10    # only last 10 slides
    python scripts/generate_og_images.py --default-only # just default.png
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SLIDE_DIR = ROOT / "presentations" / "day_slides"
OG_DIR = ROOT / "assets" / "og"
OG_DIR.mkdir(parents=True, exist_ok=True)

CACHE_PATH = OG_DIR / ".og-cache.json"

WIDTH, HEIGHT = 1200, 630
MARGIN = 72

BG = (7, 15, 38)          # #070F26 - navy
PANEL = (18, 30, 66)      # #121E42 - slight glow
ACCENT = (255, 204, 0)    # #FFCC00 - brand yellow
INK = (237, 242, 255)     # #EDF2FF - main text
MUTE = (138, 154, 191)    # #8A9ABF - muted text
RULE = (255, 255, 255, 40)

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
WS_RE = re.compile(r"\s+")
DAY_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")

# Common Windows font locations; fall back to PIL default if missing.
FONT_CANDIDATES = [
    "C:/Windows/Fonts/NotoSansJP-VF.ttf",
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
]


def load_font(size: int):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def get_title(html_text: str, fallback: str) -> str:
    m = TITLE_RE.search(html_text)
    if not m:
        return fallback
    t = html.unescape(m.group(1))
    return WS_RE.sub(" ", t).strip() or fallback


def wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Japanese-aware greedy wrap: break on any char boundary if needed."""
    lines: list[str] = []
    current = ""
    for ch in text:
        candidate = current + ch
        w = draw.textlength(candidate, font=font)
        if w <= max_width or current == "":
            current = candidate
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def render(title: str, kicker: str, out_path: Path) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # Left yellow accent strip
    draw.rectangle([(0, 0), (16, HEIGHT)], fill=ACCENT)

    # Subtle panel glow at upper right
    for i in range(0, 360, 8):
        alpha = 60 - i // 6
        if alpha <= 0:
            break
        draw.ellipse(
            [(WIDTH - 500 - i, -300 - i), (WIDTH + 150 + i, 240 + i)],
            outline=(24 + i // 18, 40 + i // 12, 90 + i // 10),
            width=1,
        )

    # Brand header
    brand_font = load_font(30)
    small_font = load_font(20)
    draw.text((MARGIN, MARGIN - 12), "AI INTELLIGENCE HUB", font=brand_font, fill=ACCENT)
    draw.text(
        (MARGIN, MARGIN + 26),
        "visionhub.jp  /  AIの最前線を5分で",
        font=small_font,
        fill=MUTE,
    )

    # Divider
    draw.rectangle([(MARGIN, MARGIN + 70), (WIDTH - MARGIN, MARGIN + 71)], fill=RULE[:3])

    # Kicker (date or category)
    kicker_font = load_font(26)
    draw.text((MARGIN, MARGIN + 96), kicker.upper(), font=kicker_font, fill=ACCENT)

    # Title (wrapped)
    title_font = load_font(56)
    max_w = WIDTH - MARGIN * 2
    lines = wrap_text(title, title_font, max_w, draw)
    # Limit to 4 lines with ellipsis
    if len(lines) > 4:
        lines = lines[:4]
        last = lines[-1]
        while draw.textlength(last + "…", font=title_font) > max_w and len(last) > 1:
            last = last[:-1]
        lines[-1] = last + "…"

    y = MARGIN + 150
    line_h = 72
    for ln in lines:
        draw.text((MARGIN, y), ln, font=title_font, fill=INK)
        y += line_h

    # Footer
    foot_font = load_font(22)
    draw.text(
        (MARGIN, HEIGHT - MARGIN - 24),
        "awano27 (Claudian)  ·  https://visionhub.jp",
        font=foot_font,
        fill=MUTE,
    )

    img.save(out_path, "PNG", optimize=True)


def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def content_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def iso_date_from_name(name: str) -> str | None:
    m = DAY_RE.search(name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--latest", type=int, default=0, help="Only process N most-recent slides")
    ap.add_argument("--default-only", action="store_true")
    args = ap.parse_args()

    # Always ensure default.png exists / up-to-date
    default_out = OG_DIR / "default.png"
    if args.force or not default_out.exists():
        render(
            "毎日更新のAIニュースとスライド — AI Intelligence Hub",
            "VISIONHUB.JP",
            default_out,
        )
        print(f"[og] wrote {default_out.relative_to(ROOT)}")

    if args.default_only:
        return 0

    slides = sorted(
        SLIDE_DIR.glob("day_slide_????_??_??.html"),
        key=lambda p: p.name,
        reverse=True,
    )
    if args.latest > 0:
        slides = slides[: args.latest]

    cache = load_cache()
    produced = 0
    skipped = 0

    for slide in slides:
        try:
            text = slide.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        title = get_title(text, fallback="AI Intelligence Hub")
        h = content_hash(title)

        key = slide.name
        out = OG_DIR / slide.with_suffix(".png").name  # day_slide_YYYY_MM_DD.png

        if not args.force and cache.get(key, {}).get("hash") == h and out.exists():
            skipped += 1
            continue

        date = iso_date_from_name(slide.name) or ""
        kicker = date if date else "DAILY"
        render(title, kicker, out)
        cache[key] = {"hash": h, "title": title}
        produced += 1

    save_cache(cache)
    print(f"[og] produced {produced}, skipped {skipped} (cache hits), total slides {len(slides)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
