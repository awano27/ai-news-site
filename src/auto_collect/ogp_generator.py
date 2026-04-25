"""1200x630 PNG generator for og:image.

Uses Pillow only — no headless browser. The card layout mirrors the
report's dark/amber theme so that a tweet preview looks coherent with the
landing site. Falls back gracefully to a no-op when Pillow is missing,
since OGP is a nice-to-have, not a blocker.
"""

from __future__ import annotations

import logging
from datetime import date as date_t
from pathlib import Path
from typing import List, Optional

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

OG_DIR = PROJECT_ROOT / "presentations" / "daily_reports" / "og"
DEFAULT_OG_PATH = OG_DIR / "default.png"

W, H = 1200, 630
BG = (8, 8, 12)
SURFACE = (14, 14, 21)
AMBER = (232, 169, 81)
CREAM = (241, 236, 217)
T1 = (242, 239, 228)
T2 = (185, 181, 196)
T3 = (106, 106, 130)


def _pick_font(size: int):
    """Best-effort cross-platform font lookup. Pillow's default font is too small."""
    from PIL import ImageFont
    candidates = [
        "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_width: int) -> List[str]:
    if not text:
        return []
    lines = []
    line = ""
    for ch in text:
        candidate = line + ch
        w = draw.textlength(candidate, font=font)
        if w <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = ch
    if line:
        lines.append(line)
    return lines


def render(report_date: str, total: int, high: int, top_titles: List[str],
           output_path: Optional[Path] = None) -> Optional[Path]:
    """Render the OGP card. Returns the path or None on failure."""
    try:
        from PIL import Image, ImageDraw  # noqa: F401
    except ImportError:
        logger.info("[ogp] Pillow not installed; skipping OGP generation")
        return None

    from PIL import Image, ImageDraw

    output_path = output_path or (OG_DIR / f"{report_date.replace('-', '_')}.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Soft amber glow at top-left
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((-200, -200, 700, 500), fill=(232, 169, 81, 38))
    img.paste(glow.convert("RGB"), mask=glow.split()[3])

    # Top rule
    draw.line([(60, 90), (W - 60, 90)], fill=AMBER, width=2)

    eyebrow_font = _pick_font(28)
    label_font = _pick_font(22)
    h1_font = _pick_font(96)
    sub_font = _pick_font(34)
    bullet_font = _pick_font(28)
    foot_font = _pick_font(22)

    # Eyebrow
    draw.text((60, 50), "AI DAILY BRIEFING", fill=AMBER, font=eyebrow_font)
    draw.text((W - 60 - draw.textlength(report_date, font=eyebrow_font), 50),
              report_date, fill=T2, font=eyebrow_font)

    # Headline
    draw.text((60, 130), "今日のAI業界", fill=CREAM, font=h1_font)
    draw.text((60, 250), f"{total} signals · {high} high-priority", fill=T2, font=sub_font)

    # Top titles bullets
    y = 330
    max_w = W - 140
    for i, title in enumerate(top_titles[:3], 1):
        prefix = f"{i:02d}  "
        prefix_w = draw.textlength(prefix, font=bullet_font)
        draw.text((60, y), prefix, fill=AMBER, font=bullet_font)
        wrapped = _wrap(draw, title, bullet_font, max_w - prefix_w)
        first = wrapped[0] if wrapped else title
        if len(wrapped) > 1:
            first = first[:-1] + "…"
        draw.text((60 + prefix_w, y), first, fill=T1, font=bullet_font)
        y += 56

    # Footer
    draw.line([(60, H - 80), (W - 60, H - 80)], fill=SURFACE, width=2)
    draw.text((60, H - 60), "visionhub.jp/presentations/auto_daily_report.html",
              fill=T3, font=foot_font)

    img.save(output_path, "PNG", optimize=True)
    logger.info(f"[ogp] saved {output_path}")
    return output_path
