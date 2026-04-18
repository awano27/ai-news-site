#!/usr/bin/env python3
"""Dynamic sitemap.xml generator for visionhub.jp.

Scans the repository for HTML pages and emits a valid sitemap.xml
under the repo root. Safe to rerun — overwrites sitemap.xml only
if content changes.

Usage:
    python scripts/build_sitemap.py             # write sitemap.xml
    python scripts/build_sitemap.py --dry-run   # print to stdout
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

BASE_URL = "https://visionhub.jp"
ROOT = Path(__file__).resolve().parent.parent

ROOT_PAGES: list[tuple[str, str, float]] = [
    ("index.html", "daily", 1.0),
    ("about.html", "monthly", 0.8),
    ("contact.html", "yearly", 0.5),
    ("privacy-policy.html", "yearly", 0.5),
    ("credits.html", "yearly", 0.3),
]

PRESENTATION_DIRS = [
    ("presentations", "weekly", 0.7),
    ("presentations/hubs", "weekly", 0.9),
    ("presentations/digests", "monthly", 0.8),
    ("presentations/day_slides", "monthly", 0.6),
    ("presentations/antigravity-guide", "monthly", 0.6),
    ("presentations/claude-code-guide", "monthly", 0.6),
    ("presentations/codex-guide", "monthly", 0.6),
    ("presentations/copilot-guide", "monthly", 0.6),
]

DAY_SLIDE_DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
DIGEST_DATE_RE = re.compile(r"(\d{4})-(\d{2})\.html$")

# Files to exclude from sitemap (test/temp/backup/generator utilities).
EXCLUDE_PATTERNS = (
    re.compile(r"^test_"),
    re.compile(r"^tmp_"),
    re.compile(r"^_"),
    re.compile(r"\.bak\."),
    re.compile(r"backup"),
    re.compile(r"og-image-generator"),
)

# Upper bound: do not list more than this many day slides (most-recent-first).
DAY_SLIDE_LIMIT = 365


def should_skip(name: str) -> bool:
    lower = name.lower()
    return any(p.search(lower) for p in EXCLUDE_PATTERNS)


def iso_mtime(path: Path) -> str:
    ts = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    return ts.strftime("%Y-%m-%d")


def day_slide_lastmod(path: Path) -> str:
    m = DAY_SLIDE_DATE_RE.search(path.name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return iso_mtime(path)


def url_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    return f"{BASE_URL}/{rel}"


def collect_urls() -> list[dict]:
    today = dt.date.today().isoformat()
    urls: list[dict] = []

    # Root pages
    for name, freq, prio in ROOT_PAGES:
        p = ROOT / name
        if p.exists():
            urls.append({
                "loc": f"{BASE_URL}/" if name == "index.html" else f"{BASE_URL}/{name}",
                "lastmod": iso_mtime(p),
                "changefreq": freq,
                "priority": prio,
            })

    # Presentation pages (non-recursive per directory)
    for rel_dir, freq, prio in PRESENTATION_DIRS:
        d = ROOT / rel_dir
        if not d.exists():
            continue
        entries: list[tuple[Path, str]] = []
        for p in sorted(d.glob("*.html")):
            if should_skip(p.name):
                continue
            if rel_dir.endswith("day_slides"):
                lm = day_slide_lastmod(p)
            else:
                lm = iso_mtime(p)
            entries.append((p, lm))

        # For day_slides, keep most recent N
        if rel_dir.endswith("day_slides"):
            entries.sort(key=lambda t: t[1], reverse=True)
            entries = entries[:DAY_SLIDE_LIMIT]

        for p, lm in entries:
            urls.append({
                "loc": url_for(p),
                "lastmod": lm,
                "changefreq": freq,
                "priority": prio,
            })

    # Deduplicate by loc (first occurrence wins)
    seen: set[str] = set()
    unique: list[dict] = []
    for u in urls:
        if u["loc"] in seen:
            continue
        seen.add(u["loc"])
        unique.append(u)

    # Sort: homepage first, then by priority desc, then by lastmod desc
    unique.sort(key=lambda u: (-u["priority"], u["lastmod"]), reverse=False)

    return unique


def build_xml(urls: list[dict]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(u['loc'])}</loc>")
        lines.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        lines.append(f"    <priority>{u['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing")
    ap.add_argument("--out", default=str(ROOT / "sitemap.xml"), help="Output file path")
    args = ap.parse_args()

    urls = collect_urls()
    xml = build_xml(urls)

    print(f"[build_sitemap] {len(urls)} URLs collected", file=sys.stderr)

    if args.dry_run:
        sys.stdout.write(xml)
        return 0

    out = Path(args.out)
    prev = out.read_text(encoding="utf-8") if out.exists() else ""
    if prev == xml:
        print("[build_sitemap] no changes", file=sys.stderr)
        return 0

    out.write_text(xml, encoding="utf-8")
    print(f"[build_sitemap] wrote {out} ({len(xml)} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
