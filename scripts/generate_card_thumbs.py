#!/usr/bin/env python3
"""Generate hero-card thumbnail PNGs for the index.html 3-card hub.

Produces three 800x450 (16:9) PNGs under assets/cards/:
  - slide.png       — stylised "today's slide" visual
  - report.png      — stylised "daily report" chart visual
  - daily-news.png  — stylised "daily news feed" visual

All thumbnails share the visionhub.jp palette (navy + yellow accent +
cyan highlights) so the three cards read as a set.

Usage:
    python scripts/generate_card_thumbs.py
    python scripts/generate_card_thumbs.py --force
"""
from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "cards"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 800, 450

# Palette (matches index.html CSS vars)
NAVY = (7, 15, 38)
NAVY_2 = (13, 23, 51)
NAVY_3 = (18, 30, 66)
INK = (237, 242, 255)
MUTE = (138, 154, 191)
YELLOW = (255, 204, 0)
CYAN = (94, 231, 223)
MAGENTA = (190, 120, 255)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/NotoSansJP-VF.ttf",
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]


def font(size: int):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def base_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    # Vignette gradient
    for y in range(H):
        t = y / H
        r = int(NAVY[0] + (NAVY_2[0] - NAVY[0]) * t)
        g = int(NAVY[1] + (NAVY_2[1] - NAVY[1]) * t)
        b = int(NAVY[2] + (NAVY_2[2] - NAVY[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    # Subtle dot grid (22px spacing)
    for x in range(20, W, 26):
        for y in range(20, H, 26):
            draw.point((x, y), fill=(30, 44, 80))
    return img, draw


def draw_badge(draw, xy, text, bg=YELLOW, fg=(20, 20, 20)):
    x, y = xy
    f = font(16)
    tw = int(draw.textlength(text, font=f))
    pad_x, pad_y = 12, 6
    w, h = tw + pad_x * 2, 26 + pad_y
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=h // 2, fill=bg)
    draw.text((x + pad_x, y + pad_y - 2), text, font=f, fill=fg)
    return x + w


# ---------------- Slide thumbnail ----------------
def make_slide() -> Image.Image:
    img, d = base_canvas()
    # Big yellow side ribbon
    d.rectangle([(0, 0), (12, H)], fill=YELLOW)
    # Soft cyan glow in upper right
    glow = Image.new("RGB", (W, H), NAVY)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([(W - 320, -160), (W + 120, 260)], fill=(24, 64, 110))
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    img = Image.blend(img, glow, 0.45)
    d = ImageDraw.Draw(img)

    # Badge
    draw_badge(d, (40, 36), "SLIDE · 今日の1枚")

    # Slide title (largest)
    ft_title = font(44)
    d.text((40, 88), "今日イチの", font=ft_title, fill=INK)
    d.text((40, 140), "AIニュース", font=ft_title, fill=YELLOW)

    # Subtitle
    ft_sub = font(22)
    d.text((40, 208), "1トピックをビジュアルで深掘り", font=ft_sub, fill=MUTE)

    # Abstract slide mini-mock at lower right
    box = (430, 240, 740, 410)
    d.rounded_rectangle(box, radius=14, fill=NAVY_3, outline=(50, 72, 120), width=1)
    # Header bar
    d.rectangle([(box[0] + 16, box[1] + 20), (box[0] + 120, box[1] + 34)], fill=YELLOW)
    # Title line
    d.rectangle([(box[0] + 16, box[1] + 50), (box[2] - 16, box[1] + 68)], fill=(220, 228, 255))
    # Body lines
    for i, w in enumerate([0.85, 0.72, 0.58, 0.80]):
        y = box[1] + 88 + i * 18
        d.rounded_rectangle(
            [(box[0] + 16, y), (box[0] + 16 + int((box[2] - box[0] - 32) * w), y + 6)],
            radius=3, fill=(90, 110, 150),
        )
    # Chart bars
    chart_left = box[0] + 16
    chart_base = box[3] - 22
    for i, h in enumerate([18, 34, 50, 28, 44]):
        x = chart_left + i * 22
        d.rectangle([(x, chart_base - h), (x + 14, chart_base)], fill=CYAN if i == 2 else (80, 120, 180))

    # Footer tick (date-like)
    ft_tick = font(14)
    d.text((40, H - 46), "VISIONHUB.JP  /  AIの最前線を 5 分で", font=ft_tick, fill=MUTE)
    return img


# ---------------- Report thumbnail ----------------
def make_report() -> Image.Image:
    img, d = base_canvas()
    d.rectangle([(0, 0), (12, H)], fill=CYAN)
    # Glow
    glow = Image.new("RGB", (W, H), NAVY)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([(-120, H - 200), (360, H + 220)], fill=(32, 88, 130))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.blend(img, glow, 0.45)
    d = ImageDraw.Draw(img)

    draw_badge(d, (40, 36), "REPORT · 今日の全体像", bg=CYAN, fg=(12, 28, 50))

    ft_title = font(42)
    d.text((40, 90), "1日の動向を", font=ft_title, fill=INK)
    d.text((40, 140), "1枚で俯瞰", font=ft_title, fill=CYAN)

    ft_sub = font(20)
    d.text((40, 204), "複数ソースから自動収集した分析レポート", font=ft_sub, fill=MUTE)

    # Mini chart (bars + line)
    panel = (40, 258, 760, 412)
    d.rounded_rectangle(panel, radius=14, fill=NAVY_3, outline=(50, 72, 120), width=1)
    # Grid
    for i in range(1, 5):
        gy = panel[1] + 30 * i
        d.line([(panel[0] + 20, gy), (panel[2] - 20, gy)], fill=(32, 48, 84))

    # Bars (category values)
    random.seed(3)
    bar_vals = [78, 62, 91, 45, 83, 55, 72, 88, 60, 95]
    bw = (panel[2] - panel[0] - 40) // len(bar_vals) - 6
    for i, v in enumerate(bar_vals):
        x = panel[0] + 20 + i * (bw + 6)
        h = int((panel[3] - panel[1] - 24) * (v / 100))
        top = panel[3] - 12 - h
        colour = YELLOW if v == max(bar_vals) else CYAN if v > 70 else (70, 100, 150)
        d.rounded_rectangle([(x, top), (x + bw, panel[3] - 12)], radius=4, fill=colour)

    # Trend line on top
    pts = [
        (panel[0] + 20 + i * (bw + 6) + bw // 2, panel[3] - 12 - int((panel[3] - panel[1] - 24) * (v / 100)))
        for i, v in enumerate(bar_vals)
    ]
    d.line(pts, fill=MAGENTA, width=3)
    for p in pts:
        d.ellipse([(p[0] - 4, p[1] - 4), (p[0] + 4, p[1] + 4)], fill=MAGENTA, outline=INK)

    return img


# ---------------- Daily News thumbnail ----------------
def make_daily_news() -> Image.Image:
    img, d = base_canvas()
    d.rectangle([(0, 0), (12, H)], fill=MAGENTA)
    # Glow
    glow = Image.new("RGB", (W, H), NAVY)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([(W // 2 - 300, -200), (W // 2 + 300, 240)], fill=(64, 36, 96))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.blend(img, glow, 0.38)
    d = ImageDraw.Draw(img)

    draw_badge(d, (40, 36), "DAILY NEWS · 今日の全記事", bg=MAGENTA, fg=(28, 10, 50))

    ft_title = font(42)
    d.text((40, 92), "X / RSS / 公式を", font=ft_title, fill=INK)
    d.text((40, 142), "横断して一覧化", font=ft_title, fill=MAGENTA)

    ft_sub = font(20)
    d.text((40, 206), "重要度順・カテゴリ別・検索フィルタ付き", font=ft_sub, fill=MUTE)

    # News feed mock — 2 rows × 3 cols
    margin = 40
    grid_top = 258
    card_w = (W - margin * 2 - 20) // 3
    card_h = 72
    rows = 2
    cols = 3
    for r in range(rows):
        for c in range(cols):
            x = margin + c * (card_w + 10)
            y = grid_top + r * (card_h + 14)
            d.rounded_rectangle(
                [(x, y), (x + card_w, y + card_h)],
                radius=10, fill=NAVY_3, outline=(50, 72, 120), width=1,
            )
            # Rank number
            ft_rank = font(18)
            rank = r * cols + c + 1
            d.text((x + 12, y + 8), f"#{rank:02d}", font=ft_rank, fill=YELLOW)
            # Priority dot
            pri_color = [MAGENTA, YELLOW, CYAN][(r * cols + c) % 3]
            d.ellipse([(x + card_w - 22, y + 12), (x + card_w - 10, y + 24)], fill=pri_color)
            # Title line
            d.rounded_rectangle(
                [(x + 12, y + 38), (x + card_w - 12, y + 46)],
                radius=3, fill=(200, 210, 240),
            )
            # Short line
            d.rounded_rectangle(
                [(x + 12, y + 52), (x + 12 + int((card_w - 24) * (0.55 + 0.1 * ((r + c) % 3))), y + 58)],
                radius=3, fill=(90, 110, 150),
            )
    return img


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    targets = [
        ("slide.png", make_slide),
        ("report.png", make_report),
        ("daily-news.png", make_daily_news),
    ]
    for name, fn in targets:
        out = OUT / name
        if out.exists() and not args.force:
            print(f"skip (exists): {out.relative_to(ROOT)}  (use --force to regenerate)")
            continue
        img = fn()
        img.save(out, "PNG", optimize=True)
        print(f"wrote: {out.relative_to(ROOT)}  ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
