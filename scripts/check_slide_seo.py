#!/usr/bin/env python3
"""SEO / size guard for day slides.

    py -3 scripts/check_slide_seo.py
    py -3 scripts/check_slide_seo.py presentations/day_slides/day_slide_2026_09_13.html
    py -3 scripts/check_slide_seo.py --json
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

from slide_seo_limits import MAX_DATA_IMAGE_BYTES, MAX_HTML_BYTES

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "presentations" / "day_slides"
BASE_URL = "https://visionhub.jp"
DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
CANONICAL_RE = re.compile(
    r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']',
    re.I,
)
CANONICAL_RE_REV = re.compile(
    r'<link\b[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']',
    re.I,
)
OG_IMAGE_RE = re.compile(
    r'<meta\b[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
    re.I,
)
OG_IMAGE_RE_REV = re.compile(
    r'<meta\b[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
    re.I,
)
TWITTER_CARD_RE = re.compile(
    r'<meta\b[^>]*name=["\']twitter:card["\'][^>]*content=["\']([^"\']+)["\']',
    re.I,
)
TWITTER_CARD_RE_REV = re.compile(
    r'<meta\b[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']twitter:card["\']',
    re.I,
)
LDJSON_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
ANALYTICS_RE = re.compile(
    r'<script\b[^>]*src=["\']/?/?assets/js/analytics\.js["\'][^>]*>',
    re.I,
)
ANALYTICS_DEFER_RE = re.compile(
    r'<script\b[^>]*src=["\']/?/?assets/js/analytics\.js["\'][^>]*\bdefer|'
    r'<script\b[^>]*\bdefer\b[^>]*src=["\']/?/?assets/js/analytics\.js["\']',
    re.I,
)
DATA_IMAGE_RE = re.compile(r"data:image/[^;]+;base64,([A-Za-z0-9+/=\s]+)", re.I)
DATE_PUB_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def _meta(text: str, fwd: re.Pattern, rev: re.Pattern) -> str | None:
    m = fwd.search(text) or rev.search(text)
    return m.group(1).strip() if m else None


def _local_for_url(url: str) -> Path | None:
    url = url.strip()
    if url.startswith(BASE_URL + "/"):
        rel = url[len(BASE_URL) + 1 :]
        path = ROOT / rel
        return path if path.is_file() else None
    if url.startswith("/") and not url.startswith("//"):
        path = ROOT / url.lstrip("/")
        return path if path.is_file() else None
    if "://" not in url:
        path = (SLIDES / url).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError:
            return None
        return path if path.is_file() else None
    return None


def _title_text(html: str) -> str:
    m = TITLE_RE.search(html)
    if not m:
        return ""
    t = TAG_RE.sub(" ", m.group(1))
    return WS_RE.sub(" ", t).strip()


def _newsarticle_dates(html: str) -> list[str]:
    dates: list[str] = []
    for block in LDJSON_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            if "NewsArticle" in block and DATE_PUB_RE.search(block):
                dates.append(DATE_PUB_RE.search(block).group(0))
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            types = item.get("@type")
            type_list = types if isinstance(types, list) else [types]
            if "NewsArticle" not in {str(t) for t in type_list if t}:
                continue
            pub = item.get("datePublished")
            if isinstance(pub, str):
                dates.append(pub)
    return dates


def check_file(path: Path) -> tuple[list[str], list[str]]:
    """Return (hard violations, soft size/title warnings)."""
    reasons: list[str] = []
    soft: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"unreadable: {exc}"], []

    og = _meta(text, OG_IMAGE_RE, OG_IMAGE_RE_REV)
    if not og:
        reasons.append("missing og:image")
    else:
        local = _local_for_url(og)
        if local is None:
            reasons.append(f"og:image not in repo: {og}")

    card = _meta(text, TWITTER_CARD_RE, TWITTER_CARD_RE_REV)
    if card != "summary_large_image":
        reasons.append(f"twitter:card={card!r} (want summary_large_image)")

    pubs = _newsarticle_dates(text)
    if not pubs:
        reasons.append("missing NewsArticle datePublished")
    elif not any(DATE_PUB_RE.match(p) for p in pubs):
        reasons.append(f"NewsArticle datePublished not YYYY-MM-DD: {pubs[0]!r}")

    if not ANALYTICS_RE.search(text):
        reasons.append("missing /assets/js/analytics.js")
    elif not ANALYTICS_DEFER_RE.search(text):
        reasons.append("analytics.js script is not defer")

    size = path.stat().st_size
    if size > MAX_HTML_BYTES:
        soft.append(f"html {size} bytes > {MAX_HTML_BYTES}")

    for blob in DATA_IMAGE_RE.findall(text):
        raw = re.sub(r"\s+", "", blob)
        pad = (-len(raw)) % 4
        try:
            decoded = base64.b64decode(raw + ("=" * pad), validate=False)
        except Exception:
            soft.append("invalid data:image base64")
            continue
        if len(decoded) > MAX_DATA_IMAGE_BYTES:
            soft.append(f"data:image {len(decoded)} bytes > {MAX_DATA_IMAGE_BYTES}")

    expected = f"{BASE_URL}/presentations/day_slides/{path.name}"
    canon = _meta(text, CANONICAL_RE, CANONICAL_RE_REV)
    if canon != expected:
        reasons.append(f"canonical={canon!r} (want {expected})")

    title = _title_text(text)
    n = len(title)
    if n < 25 or n > 70:
        soft.append(f"title length {n} (want 25-70): {title[:80]!r}")

    return reasons, soft


def iter_slides(paths: list[str]) -> list[Path]:
    if not paths:
        return sorted(SLIDES.glob("day_slide_????_??_??.html"))
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = ROOT / p
        if p.is_dir():
            out.extend(sorted(p.glob("day_slide_????_??_??.html")))
        elif p.is_file():
            out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="also fail on html/base64 size and title length (P1/P2)",
    )
    args = ap.parse_args(argv)

    files = iter_slides(args.paths)
    violations: list[dict] = []
    warnings: list[dict] = []
    for path in files:
        hard, soft = check_file(path)
        try:
            rel = path.relative_to(ROOT).as_posix()
        except ValueError:
            rel = str(path)
        for reason in hard:
            violations.append({"file": rel, "reason": reason, "level": "error"})
            if not args.json:
                print(f"{rel}: {reason}")
        for reason in soft:
            warnings.append({"file": rel, "reason": reason, "level": "warning"})
            if not args.json:
                print(f"{rel}: {reason} (warning)")

    fatal = list(violations)
    if args.strict:
        fatal.extend(warnings)
    if args.json:
        print(json.dumps(
            {
                "ok": not fatal,
                "checked": len(files),
                "violations": violations,
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print(
            f"[check_slide_seo] checked={len(files)} "
            f"errors={len(violations)} warnings={len(warnings)}"
        )
    return 1 if fatal else 0


if __name__ == "__main__":
    raise SystemExit(main())
