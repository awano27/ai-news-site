#!/usr/bin/env python3
"""Inject schema.org NewsArticle / Article JSON-LD into HTML pages.

- Day slides (presentations/day_slides/day_slide_YYYY_MM_DD.html) → NewsArticle
- Hub pages (presentations/hubs/*.html) → Article with keywords
- Digests (presentations/digests/YYYY-MM.html) → CollectionPage

Idempotent via ``<!-- JSONLD_INJECTED v1 -->`` marker.

Usage:
    python scripts/inject_newsarticle_jsonld.py --dry-run
    python scripts/inject_newsarticle_jsonld.py
    python scripts/inject_newsarticle_jsonld.py --force
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://visionhub.jp"
SITE_NAME = "AI Intelligence Hub"
MARKER = "<!-- JSONLD_INJECTED v1 -->"

PUBLISHER = {
    "@type": "Organization",
    "name": SITE_NAME,
    "url": f"{BASE_URL}/",
    "logo": {
        "@type": "ImageObject",
        "url": f"{BASE_URL}/assets/og/default.png",
        "width": 1200,
        "height": 630,
    },
}

AUTHOR = {
    "@type": "Person",
    "name": "awano27",
    "alternateName": "Claudian",
    "url": f"{BASE_URL}/about.html",
}

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)
DAY_SLIDE_DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
DIGEST_DATE_RE = re.compile(r"(\d{4})-(\d{2})\.html$")
WS_RE = re.compile(r"\s+")

DEFAULT_TARGETS = [
    ROOT / "presentations" / "day_slides",
    ROOT / "presentations" / "hubs",
    ROOT / "presentations" / "digests",
]


def get_title(text: str, fallback: str) -> str:
    m = TITLE_RE.search(text)
    if not m:
        return fallback
    t = html.unescape(m.group(1)).strip()
    return WS_RE.sub(" ", t) or fallback


def canonical_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    return f"{BASE_URL}/{rel}"


def image_for(path: Path) -> str:
    name = path.name
    m = DAY_SLIDE_DATE_RE.search(name)
    if m:
        return f"{BASE_URL}/assets/og/day_slide_{m.group(1)}_{m.group(2)}_{m.group(3)}.png"
    return f"{BASE_URL}/assets/og/default.png"


def build_payload(path: Path, text: str) -> dict | None:
    name = path.name
    title = get_title(text, fallback=SITE_NAME)
    url = canonical_for(path)
    img = image_for(path)

    m = DAY_SLIDE_DATE_RE.search(name)
    if m:
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        return {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title[:110],
            "datePublished": date,
            "dateModified": date,
            "author": AUTHOR,
            "publisher": PUBLISHER,
            "image": [img],
            "mainEntityOfPage": url,
            "url": url,
            "inLanguage": "ja",
            "articleSection": "AI News",
        }

    m = DIGEST_DATE_RE.search(name)
    if m and "digests" in path.parts:
        date = f"{m.group(1)}-{m.group(2)}-01"
        return {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": url,
            "inLanguage": "ja",
            "datePublished": date,
            "publisher": PUBLISHER,
            "about": "Generative AI monthly digest",
        }

    if "hubs" in path.parts:
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title[:110],
            "author": AUTHOR,
            "publisher": PUBLISHER,
            "image": [img],
            "mainEntityOfPage": url,
            "url": url,
            "inLanguage": "ja",
            "articleSection": "Guide",
        }

    # Other presentation pages — treat as Article but skip if no date info
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "author": AUTHOR,
        "publisher": PUBLISHER,
        "image": [img],
        "mainEntityOfPage": url,
        "url": url,
        "inLanguage": "ja",
    }


def process_file(path: Path, force: bool, dry_run: bool) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "skip (non-utf8)"

    if MARKER in text and not force:
        return "skip (already injected)"

    if not HEAD_CLOSE_RE.search(text):
        return "skip (no </head>)"

    payload = build_payload(path, text)
    if not payload:
        return "skip (no payload)"

    if force and MARKER in text:
        text = re.sub(
            rf"{re.escape(MARKER)}.*?(?=</head>)",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )

    block = (
        MARKER
        + '\n<script type="application/ld+json">\n'
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n</script>\n"
    )
    new_text = HEAD_CLOSE_RE.sub(block + "</head>", text, count=1)

    if dry_run:
        return f"would inject ({len(block)} bytes)"

    path.write_text(new_text, encoding="utf-8")
    return "injected"


def iter_targets(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if not p.exists():
            continue
        if p.is_file() and p.suffix.lower() == ".html":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.glob("*.html")))
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    targets = [Path(p) if Path(p).is_absolute() else (ROOT / p) for p in args.paths] if args.paths else DEFAULT_TARGETS
    files = iter_targets(targets)

    stats: dict[str, int] = {}
    for f in files:
        result = process_file(f, args.force, args.dry_run)
        key = "would inject" if result.startswith("would") else result
        stats[key] = stats.get(key, 0) + 1
        if result.startswith(("injected", "would")):
            print(f"  {result}: {f.relative_to(ROOT)}")
    print(f"[inject_newsarticle_jsonld] {sum(stats.values())} files: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
