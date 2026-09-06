#!/usr/bin/env python3
"""Render/check small evidence slots in otherwise hand-maintained static HTML.

The embedded bundle is the only source register; the displayed statement remains
bound to the existing body element. This script never creates review records or
refreshes dates/fingerprints. It does not fetch sources or regenerate a page.
"""
from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.auto_collect.claim_evidence import normalized_text, render_evidence, validate_bundle

DEFAULT_PAGES = (
    "presentations/ai_coding_agents_guide.html",
    "presentations/day_slides/day_slide_2026_09_04.html",
    "about.html",
    "articles/claim-evidence-design.html",
)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "div", "li", "br", "tr", "td", "th"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {"p", "div", "li", "tr", "td", "th"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def visible_text(html: str) -> str:
    parser = _Text()
    parser.feed(html)
    return normalized_text("".join(parser.parts))


class EvidencePage(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.offsets = [0]
        for line in text.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.stack = []
        self.claims: dict[str, list[tuple[int, int]]] = {}
        self.slots: dict[str, list[tuple[int, int]]] = {}
        self.data_spans = []
        self.stylesheet = False
        self.feed(text)

    def _offset(self):
        line, col = self.getpos()
        return self.offsets[line - 1] + col

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "stylesheet" and attrs.get("href") == "/assets/claim-evidence.css":
            self.stylesheet = True
        if tag in VOID:
            return
        start = self._offset() + len(self.get_starttag_text())
        self.stack.append((tag, attrs, start))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] != tag:
                continue
            _, attrs, start = self.stack[i]
            del self.stack[i:]
            span = (start, self._offset())
            if "data-claim-id" in attrs:
                self.claims.setdefault(attrs["data-claim-id"], []).append(span)
            if "data-evidence-for" in attrs:
                self.slots.setdefault(attrs["data-evidence-for"], []).append(span)
            if tag == "script" and attrs.get("id") == "claim-evidence-data":
                self.data_spans.append(span)
            return

    def bundle(self):
        if len(self.data_spans) != 1:
            raise ValueError("exactly one script#claim-evidence-data is required")
        start, end = self.data_spans[0]
        return json.loads(self.text[start:end])


def render_static_page(text: str) -> tuple[str, list[str]]:
    page = EvidencePage(text)
    try:
        bundle = page.bundle()
    except (ValueError, json.JSONDecodeError) as exc:
        return text, [f"embedded evidence: {exc}"]
    errors = validate_bundle(bundle)
    if errors:
        return text, errors
    if not page.stylesheet:
        errors.append("shared evidence stylesheet is missing")
    known_ids = {c["id"] for c in bundle["claims"]}
    for unknown in (set(page.claims) | set(page.slots)) - known_ids:
        errors.append(f"{unknown}: body/slot references unregistered claim")
    replacements = []
    for claim in bundle["claims"]:
        cid = claim["id"]
        bodies = page.claims.get(cid, [])
        slots = page.slots.get(cid, [])
        if len(bodies) != 1:
            errors.append(f"{cid}: exactly one bound body element required")
        elif visible_text(text[bodies[0][0]:bodies[0][1]]) != normalized_text(claim["statement"]):
            errors.append(f"{cid}: body text differs from reviewed statement")
        if len(slots) != 1:
            errors.append(f"{cid}: exactly one evidence slot required")
        else:
            start, end = slots[0]
            if len(bodies) == 1 and bodies[0][0] <= start < bodies[0][1]:
                errors.append(f"{cid}: evidence slot must not be nested in claim text")
            replacements.append((start, end, render_evidence(bundle, [cid])))
    if errors:
        return text, errors
    rendered = text
    for start, end, replacement in sorted(replacements, reverse=True):
        rendered = rendered[:start] + replacement + rendered[end:]
    return rendered, []


def check_static_page(path: Path) -> list[str]:
    original = path.read_text(encoding="utf-8")
    rendered, errors = render_static_page(original)
    if not errors and rendered != original:
        errors.append("evidence display is stale; render the existing slots with --write")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--write", action="store_true", help="replace evidence slots after validating recorded review metadata")
    args = parser.parse_args()
    failures = 0
    for path in args.paths or [ROOT / p for p in DEFAULT_PAGES]:
        try:
            original = path.read_text(encoding="utf-8")
            rendered, errors = render_static_page(original)
        except (OSError, ValueError) as exc:
            errors = [str(exc)]
        if not errors and rendered != original:
            if args.write:
                with path.open("w", encoding="utf-8", newline="") as handle:
                    handle.write(rendered)
            else:
                errors = ["evidence display is stale (run --write after reviewing source data)"]
        for error in errors:
            print(f"ERROR {path}: {error}")
        if errors:
            failures += 1
        else:
            print(f"PASS {path}: statement bindings, recorded reviews and evidence display")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
