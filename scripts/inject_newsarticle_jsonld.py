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

import html
import json
import re
import sys
from pathlib import Path

from inject._framework import ROOT, Injector, iter_targets

BASE_URL = "https://visionhub.jp"
SITE_NAME = "AI Intelligence Hub"

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
DAY_SLIDE_DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
DIGEST_DATE_RE = re.compile(r"(\d{4})-(\d{2})\.html$")
WS_RE = re.compile(r"\s+")


def get_title(text: str, fallback: str) -> str:
    m = TITLE_RE.search(text)
    if not m:
        return fallback
    t = html.unescape(m.group(1)).strip()
    return WS_RE.sub(" ", t) or fallback


def canonical_for(path: Path) -> str:
    return f"{BASE_URL}/{path.relative_to(ROOT).as_posix()}"


def image_for(path: Path) -> str:
    m = DAY_SLIDE_DATE_RE.search(path.name)
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


class JsonLdInjector(Injector):
    MARKER = "<!-- JSONLD_INJECTED v1 -->"
    DESCRIPTION = "Inject schema.org JSON-LD into HTML pages."
    TAG = "inject_newsarticle_jsonld"
    RECURSIVE = False
    END_PATTERN = r"(?=</head>)"
    DEFAULT_TARGETS = [
        ROOT / "presentations" / "day_slides",
        ROOT / "presentations" / "hubs",
        ROOT / "presentations" / "digests",
    ]

    def build_block(self, path: Path, text: str) -> str | None:
        payload = build_payload(path, text)
        if not payload:
            return None
        return (
            self.MARKER
            + '\n<script type="application/ld+json">\n'
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n</script>\n"
        )

    def run(self, argv: list[str] | None = None) -> int:
        args = self._parse_args(argv)

        raw = args.paths
        targets = (
            [Path(p) if Path(p).is_absolute() else (ROOT / p) for p in raw]
            if raw
            else self.DEFAULT_TARGETS
        )
        files = iter_targets(targets, self.EXCLUSION_PATTERNS, self.RECURSIVE)

        stats: dict[str, int] = {}
        for f in files:
            result = self.process_file(f, args.force, args.dry_run)
            key = "would inject" if result.startswith("would") else result
            stats[key] = stats.get(key, 0) + 1
            if result.startswith(("injected", "would")):
                print(f"  {result}: {f.relative_to(ROOT)}")
        print(f"[inject_newsarticle_jsonld] {sum(stats.values())} files: {stats}")
        return 0


def main() -> int:
    return JsonLdInjector().run()


if __name__ == "__main__":
    sys.exit(main())
