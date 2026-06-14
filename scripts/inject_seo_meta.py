#!/usr/bin/env python3
"""Inject missing SEO meta tags (description / canonical / OG / Twitter Card).

Idempotent: each HTML file gets a single marker comment
``<!-- SEO_META_INJECTED v1 -->``; subsequent runs skip unless
``--force`` is provided.

Targets by default: the day_slides dir + root static pages. Pass paths
to restrict scope.

Usage:
    python scripts/inject_seo_meta.py --dry-run
    python scripts/inject_seo_meta.py
    python scripts/inject_seo_meta.py presentations/day_slides/day_slide_2026_04_18.html
    python scripts/inject_seo_meta.py --force           # re-inject everywhere
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from inject._framework import HEAD_CLOSE_RE, ROOT, Injector, iter_targets, strip_marker_block

BASE_URL = "https://visionhub.jp"
SITE_NAME = "AI Intelligence Hub"
DEFAULT_OG_IMAGE = f"{BASE_URL}/assets/og/default.png"

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_DESC_RE = re.compile(r'<meta\s+[^>]*name=["\']description["\']', re.IGNORECASE)
CANONICAL_RE = re.compile(r'<link\s+[^>]*rel=["\']canonical["\']', re.IGNORECASE)
OG_TITLE_RE = re.compile(r'<meta\s+[^>]*property=["\']og:title["\']', re.IGNORECASE)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
DAY_SLIDE_DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")


def extract_title(text: str, fallback: str) -> str:
    m = TITLE_RE.search(text)
    if not m:
        return fallback
    title = html.unescape(m.group(1)).strip()
    return WS_RE.sub(" ", title) or fallback


def extract_description(text: str, max_len: int = 150) -> str:
    """Pull a plain-text description from the body, skipping scripts/styles."""
    body_m = re.search(r"<body[^>]*>(.*)</body>", text, re.IGNORECASE | re.DOTALL)
    body = body_m.group(1) if body_m else text
    body = SCRIPT_STYLE_RE.sub(" ", body)
    body = TAG_RE.sub(" ", body)
    body = html.unescape(body)
    body = WS_RE.sub(" ", body).strip()
    if len(body) <= max_len:
        return body
    cut = body[:max_len].rstrip()
    for sep in ("。", "、", " ", "　"):
        idx = cut.rfind(sep)
        if idx > max_len * 0.6:
            cut = cut[:idx]
            break
    return cut.rstrip() + "…"


def canonical_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return f"{BASE_URL}/"
    return f"{BASE_URL}/{rel}"


def og_image_for(path: Path) -> str:
    name = path.name
    m = DAY_SLIDE_DATE_RE.search(name)
    if m:
        return f"{BASE_URL}/assets/og/day_slide_{m.group(1)}_{m.group(2)}_{m.group(3)}.png"
    return DEFAULT_OG_IMAGE


def build_meta_block(path: Path, text: str) -> str:
    title = extract_title(text, fallback=SITE_NAME)
    desc = extract_description(text) or f"{SITE_NAME} — AIの最前線を5分で。"
    canon = canonical_for(path)
    og_image = og_image_for(path)
    title_attr = html.escape(title, quote=True)
    desc_attr = html.escape(desc, quote=True)

    lines = ["<!-- SEO_META_INJECTED v1 -->"]

    if not META_DESC_RE.search(text):
        lines.append(f'<meta name="description" content="{desc_attr}" />')
    if not CANONICAL_RE.search(text):
        lines.append(f'<link rel="canonical" href="{canon}" />')
    if not OG_TITLE_RE.search(text):
        lines.append('<meta property="og:type" content="article" />')
        lines.append(f'<meta property="og:site_name" content="{SITE_NAME}" />')
        lines.append(f'<meta property="og:title" content="{title_attr}" />')
        lines.append(f'<meta property="og:description" content="{desc_attr}" />')
        lines.append(f'<meta property="og:url" content="{canon}" />')
        lines.append(f'<meta property="og:image" content="{og_image}" />')
        lines.append('<meta property="og:locale" content="ja_JP" />')
        lines.append('<meta name="twitter:card" content="summary_large_image" />')
        lines.append(f'<meta name="twitter:title" content="{title_attr}" />')
        lines.append(f'<meta name="twitter:description" content="{desc_attr}" />')
        lines.append(f'<meta name="twitter:image" content="{og_image}" />')
    if "max-image-preview" not in text:
        lines.append('<meta name="robots" content="index,follow,max-image-preview:large" />')

    return "\n".join(lines) + "\n"


class SeoMetaInjector(Injector):
    MARKER = "<!-- SEO_META_INJECTED v1 -->"
    DESCRIPTION = "Inject missing SEO meta tags site-wide."
    TAG = "inject_seo_meta"
    RECURSIVE = False
    END_PATTERN = r"(?=</head>)"
    DEFAULT_TARGETS = [
        ROOT / "index.html",
        ROOT / "about.html",
        ROOT / "contact.html",
        ROOT / "privacy-policy.html",
        ROOT / "presentations" / "day_slides",
        ROOT / "presentations" / "hubs",
        ROOT / "presentations" / "digests",
    ]

    def build_block(self, path: Path, text: str) -> str | None:
        if "<head" not in text.lower():
            return None
        return build_meta_block(path, text)

    def process_file(self, path: Path, force: bool, dry_run: bool) -> str:
        # seo_meta has an extra "no head" check separate from "no </head>"
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return "skip (non-utf8)"
        if self.MARKER in text and not force:
            return "skip (already injected)"
        if "<head" not in text.lower():
            return "skip (no head)"
        if not HEAD_CLOSE_RE.search(text):
            return "skip (no head)"
        if force and self.MARKER in text:
            text = strip_marker_block(text, self.MARKER, self.END_PATTERN)
        block = build_meta_block(path, text)
        new_text = HEAD_CLOSE_RE.sub(block + "</head>", text, count=1)
        if dry_run:
            return f"would inject ({len(block)} bytes)"
        path.write_text(new_text, encoding="utf-8")
        return "injected"

    def run(self, argv: list[str] | None = None) -> int:
        args = self._parse_args(argv)

        raw = args.paths
        targets = (
            [Path(p) if Path(p).is_absolute() else (ROOT / p) for p in raw]
            if raw
            else self.DEFAULT_TARGETS
        )
        files = iter_targets(targets, self.EXCLUSION_PATTERNS, self.RECURSIVE)

        stats = {"injected": 0, "skip (already injected)": 0, "skip (no head)": 0,
                 "skip (non-utf8)": 0, "would inject": 0}
        for f in files:
            result = self.process_file(f, args.force, args.dry_run)
            key = result if result in stats else ("would inject" if result.startswith("would") else result)
            stats[key] = stats.get(key, 0) + 1
            if result.startswith(("injected", "would")):
                print(f"  {result}: {f.relative_to(ROOT)}")
        print(f"[inject_seo_meta] {sum(stats.values())} files processed: {stats}")
        return 0


def main() -> int:
    return SeoMetaInjector().run()


if __name__ == "__main__":
    sys.exit(main())
