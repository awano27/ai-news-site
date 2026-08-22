#!/usr/bin/env python3
"""Idempotent JSON-LD enrichment for dated day slides.

Rewrites existing application/ld+json article blocks so they are both
PresentationDigitalDocument and NewsArticle, filling only missing
author / publisher / image / mainEntityOfPage / inLanguage.
Does not insert a block when none exists.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "presentations" / "day_slides"
ORG = {
    "@type": "Organization",
    "name": "AI Intelligence Hub",
    "url": "https://visionhub.jp/",
}
ARTICLE_TYPES = {"PresentationDigitalDocument", "NewsArticle"}
KEEP_FIELDS = ("headline", "description", "datePublished", "dateModified", "articleSection")
InjectionStatus = Literal["changed", "unchanged", "skipped"]

SCRIPT_RE = re.compile(
    r'(<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.I | re.S,
)


def meta_content(html: str, attr: str) -> str | None:
    named = re.search(
        rf'<meta\b[^>]*\b(?:property|name)=["\']{re.escape(attr)}["\'][^>]*\bcontent=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    if named:
        return named.group(1).strip() or None
    reversed_ = re.search(
        rf'<meta\b[^>]*\bcontent=["\']([^"\']+)["\'][^>]*\b(?:property|name)=["\']{re.escape(attr)}["\']',
        html,
        re.I,
    )
    return reversed_.group(1).strip() or None if reversed_ else None


def canonical_url(html: str, path: Path) -> str:
    href = re.search(
        r'<link\b[^>]*\brel=["\']canonical["\'][^>]*\bhref=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    if href:
        return href.group(1).strip()
    href = re.search(
        r'<link\b[^>]*\bhref=["\']([^"\']+)["\'][^>]*\brel=["\']canonical["\']',
        html,
        re.I,
    )
    if href:
        return href.group(1).strip()
    return f"https://visionhub.jp/presentations/day_slides/{path.name}"


def as_type_list(value: Any) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []


def is_article_block(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    return bool(ARTICLE_TYPES.intersection(as_type_list(data.get("@type"))))


def desired_payload(existing: dict, *, og_image: str | None, canonical: str) -> dict:
    out = dict(existing)
    types = as_type_list(existing.get("@type"))
    ordered: list[str] = []
    for name in ("PresentationDigitalDocument", "NewsArticle"):
        if name not in ordered:
            ordered.append(name)
    for name in types:
        if name not in ordered:
            ordered.append(name)
    out["@type"] = ordered
    if "author" not in out:
        out["author"] = dict(ORG)
    if "publisher" not in out:
        out["publisher"] = dict(ORG)
    if og_image and "image" not in out:
        out["image"] = og_image
    if "mainEntityOfPage" not in out:
        out["mainEntityOfPage"] = canonical
    if "inLanguage" not in out:
        out["inLanguage"] = "ja"
    return out


def is_complete(data: dict, og_image: str | None) -> bool:
    types = as_type_list(data.get("@type"))
    if "PresentationDigitalDocument" not in types or "NewsArticle" not in types:
        return False
    for key in ("author", "publisher", "mainEntityOfPage", "inLanguage"):
        if key not in data:
            return False
    if og_image and "image" not in data:
        return False
    return True


def serialize(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def inject_file(path: Path) -> InjectionStatus:
    text = path.read_text(encoding="utf-8")
    matches = list(SCRIPT_RE.finditer(text))
    if not matches:
        print(f"[inject_jsonld] {path.name}: skipped (no json-ld)", file=sys.stderr)
        return "skipped"

    og_image = meta_content(html=text, attr="og:image")
    canonical = canonical_url(text, path)
    updated = text
    saw_article = False
    changed = False

    for match in reversed(matches):
        raw = match.group(2).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"[inject_jsonld] {path.name}: skip unreadable json-ld ({exc})", file=sys.stderr)
            continue
        if not is_article_block(data):
            continue
        saw_article = True
        wanted = desired_payload(data, og_image=og_image, canonical=canonical)
        if is_complete(data, og_image) and data == wanted:
            continue
        dumped = serialize(wanted)
        replacement = f"{match.group(1)}\n{dumped}\n{match.group(3)}"
        updated = updated[: match.start()] + replacement + updated[match.end() :]
        changed = True

    if not saw_article:
        print(f"[inject_jsonld] {path.name}: skipped (no article json-ld)", file=sys.stderr)
        return "skipped"
    if not changed or updated == text:
        return "unchanged"
    path.write_text(updated, encoding="utf-8", newline="\n")
    return "changed"


def main(argv: list[str] | None = None) -> int:
    slides = sorted(SLIDES.glob("day_slide_????_??_??.html"))
    counts = {"changed": 0, "unchanged": 0, "skipped": 0}
    for path in slides:
        status = inject_file(path)
        counts[status] += 1
    print(
        f"[inject_jsonld] {len(slides)} files, "
        f"{counts['changed']} changed, {counts['unchanged']} unchanged, "
        f"{counts['skipped']} skipped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
