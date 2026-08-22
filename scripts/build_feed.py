#!/usr/bin/env python3
"""Generate a 30-entry Atom 1.0 feed of day slides.

Safe to rerun — overwrites feed.xml only if content changes.
Does not embed the wall-clock time; each <updated> is the slide
date at 07:00:00+09:00 so two consecutive runs are byte-identical.

Usage:
    python scripts/build_feed.py             # write feed.xml
    python scripts/build_feed.py --dry-run   # print to stdout
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from html import unescape
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "presentations" / "day_slides"
OUTPUT = ROOT / "feed.xml"
BASE_URL = "https://visionhub.jp"
FEED_URL = f"{BASE_URL}/feed.xml"
FEED_TITLE = "AI Intelligence Hub — Day Slides"
AUTHOR = "AI Intelligence Hub"
LIMIT = 30

DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.I | re.S)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I | re.S)
DESC_RE = re.compile(
    r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
    re.I,
)
TRAILING_DATE_RE = re.compile(r"\s*(?:\|\s*)?\d{4}-\d{2}-\d{2}\s*$")


def parse_slide_date(name: str) -> date | None:
    match = DATE_RE.fullmatch(name)
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _plain_text(html_fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html_fragment or "")
    return " ".join(unescape(text).split())


def extract_slide_meta(html: str) -> tuple[str | None, str]:
    """Return (title, summary). Title prefers <title> over <h1>, date stripped."""
    title = None
    for pattern in (TITLE_RE, H1_RE):
        match = pattern.search(html or "")
        if not match:
            continue
        text = TRAILING_DATE_RE.sub("", _plain_text(match.group(1))).strip()
        if text:
            title = text
            break
    desc_match = DESC_RE.search(html or "")
    summary = unescape(desc_match.group(1)).strip() if desc_match else ""
    return title, summary


def atom_updated(day: date) -> str:
    return f"{day.isoformat()}T07:00:00+09:00"


def slide_url(day: date) -> str:
    return f"{BASE_URL}/presentations/day_slides/day_slide_{day:%Y_%m_%d}.html"


def collect_entries(slides_dir: Path) -> list[dict]:
    found: list[tuple[date, Path]] = []
    for path in slides_dir.glob("day_slide_????_??_??.html"):
        day = parse_slide_date(path.name)
        if day is None:
            continue
        if not path.is_file():
            print(f"[build_feed] skip missing {path.name}", file=sys.stderr)
            continue
        found.append((day, path))
    found.sort(key=lambda item: item[0], reverse=True)

    entries: list[dict] = []
    for day, path in found:
        if not path.is_file():
            print(f"[build_feed] skip missing {path.name}", file=sys.stderr)
            continue
        try:
            html = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[build_feed] skip unreadable {path.name}: {exc}", file=sys.stderr)
            continue
        title, summary = extract_slide_meta(html)
        if not title:
            print(f"[build_feed] skip untitled {path.name}", file=sys.stderr)
            continue
        entries.append(
            {
                "title": title,
                "summary": summary,
                "url": slide_url(day),
                "updated": atom_updated(day),
            }
        )
        if len(entries) >= LIMIT:
            break
    return entries


def build_feed_xml(entries: list[dict]) -> str:
    updated = entries[0]["updated"] if entries else "1970-01-01T07:00:00+09:00"
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{escape(FEED_TITLE)}</title>",
        f'  <link href="{escape(FEED_URL)}" rel="self" type="application/atom+xml"/>',
        f'  <link href="{escape(BASE_URL + "/")}" rel="alternate" type="text/html"/>',
        f"  <id>{escape(FEED_URL)}</id>",
        f"  <updated>{escape(updated)}</updated>",
        "  <author>",
        f"    <name>{escape(AUTHOR)}</name>",
        "  </author>",
        "  <subtitle>Daily AI slides from visionhub.jp</subtitle>",
    ]
    for entry in entries:
        lines.append("  <entry>")
        lines.append(f"    <title>{escape(entry['title'])}</title>")
        lines.append(
            f'    <link href="{escape(entry["url"])}" rel="alternate" type="text/html"/>'
        )
        lines.append(f"    <id>{escape(entry['url'])}</id>")
        lines.append(f"    <updated>{escape(entry['updated'])}</updated>")
        if entry.get("summary"):
            lines.append(f'    <summary type="text">{escape(entry["summary"])}</summary>')
        lines.append("  </entry>")
    lines.append("</feed>")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing")
    parser.add_argument("--out", default=str(OUTPUT), help="Output file path")
    args = parser.parse_args([] if argv is None else argv)

    if not SLIDES.is_dir():
        print(f"[build_feed] slides dir missing: {SLIDES}", file=sys.stderr)
        return 1

    entries = collect_entries(SLIDES)
    xml = build_feed_xml(entries)
    print(f"[build_feed] {len(entries)} entries", file=sys.stderr)

    if args.dry_run:
        sys.stdout.write(xml)
        return 0

    out = Path(args.out)
    prev = out.read_text(encoding="utf-8") if out.exists() else ""
    if prev == xml:
        print("[build_feed] no changes", file=sys.stderr)
        return 0

    out.write_text(xml, encoding="utf-8", newline="\n")
    print(f"[build_feed] wrote {out} ({len(xml.encode('utf-8'))} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
