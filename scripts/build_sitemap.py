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
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

BASE_URL = "https://visionhub.jp"
ROOT = Path(__file__).resolve().parent.parent

ROOT_PAGES: list[tuple[str, str, float]] = [
    # Canonical policy: single HTML pages keep .html (about.html is canonical; /about is GH Pages alias).
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
    ("presentations/daily_reports", "monthly", 0.5),
    ("presentations/recommended_tools", "monthly", 0.7),
    ("presentations/antigravity-guide", "monthly", 0.6),
    ("presentations/claude-code-guide", "monthly", 0.6),
    ("presentations/codex-guide", "monthly", 0.6),
    ("presentations/copilot-guide", "monthly", 0.6),
]

DAILY_NEWS_DIRS = [
    ("daily-news", "daily", 0.8),
    ("daily-news/archive", "daily", 0.7),
]

DAY_SLIDE_DATE_RE = re.compile(r"^day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
DAILY_REPORT_DATE_RE = re.compile(r"^auto_daily_report_(\d{4})_(\d{2})_(\d{2})\.html$")
DAILY_NEWS_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\.html$")
DIGEST_DATE_RE = re.compile(r"(\d{4})-(\d{2})\.html$")

# Files to exclude from sitemap (test/temp/backup/generator utilities).
EXCLUDE_PATTERNS = (
    re.compile(r"^test_"),
    re.compile(r"^tmp_"),
    re.compile(r"^_"),
    re.compile(r"(^|[_-])test([_.-]|$)"),
    re.compile(r"(^|[_-])bak([_.-]|$)"),
    re.compile(r"\.bak\."),
    re.compile(r"backup"),
    re.compile(r"og-image-generator"),
)

# A dated snapshot directly under presentations/ (ai_ranking_report_20261114.html,
# auto_daily_report_2026_04_22.html) repeats the title of its *_latest page and
# nothing links to it. The latest page is the one to index.
DATED_SNAPSHOT_RE = re.compile(r"_(\d{8}|\d{4}_\d{2}_\d{2})\.html$")

# Published under presentations/ but not part of the site's subject or still a draft.
UNLISTED_PRESENTATIONS = frozenset({
    "dashboard_resn.html",
    "index_modern.html",
    "infra_plan_proposal.html",
    "sp500_trump_chart_2026v2.html",
})

NOINDEX_RE = re.compile(r"""<meta[^>]+name=["']robots["'][^>]*noindex""", re.IGNORECASE)
REFRESH_RE = re.compile(r"""<meta[^>]+http-equiv=["']refresh["']""", re.IGNORECASE)
HEAD_BYTES = 20_000


def should_skip(name: str) -> bool:
    lower = name.lower()
    # Redirect stub; canonical URL is /presentations/recommended_tools/
    if lower == "recommended_tools.html":
        return True
    return any(p.search(lower) for p in EXCLUDE_PATTERNS)


def opts_out_of_indexing(path: Path) -> bool:
    """True for a page that tells crawlers to skip it or sends them elsewhere."""
    with path.open(encoding="utf-8", errors="replace") as fh:
        head = fh.read(HEAD_BYTES)
    return bool(NOINDEX_RE.search(head) or REFRESH_RE.search(head))


def listed_in(rel_dir: str, path: Path) -> bool:
    name = path.name
    if should_skip(name) or opts_out_of_indexing(path):
        return False
    if rel_dir == "presentations":
        return name not in UNLISTED_PRESENTATIONS and not DATED_SNAPSHOT_RE.search(name)
    if rel_dir == "presentations/day_slides":
        # Variants (_fixed, _detailed, -gm, ...) duplicate the plain dated slide.
        return bool(DAY_SLIDE_DATE_RE.match(name))
    return True


def iso_mtime(path: Path) -> str:
    ts = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    return ts.strftime("%Y-%m-%d")


def latest_homepage_date() -> str | None:
    for rel in ("news/latest.json", "public-pages/news/archive_index.json"):
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            for key in ("generated_at", "news_date", "date"):
                value = data.get(key)
                if isinstance(value, str):
                    m = re.match(r"(\d{4}-\d{2}-\d{2})", value)
                    if m:
                        return m.group(1)
        if isinstance(data, list) and data:
            value = data[0].get("date") if isinstance(data[0], dict) else None
            if isinstance(value, str) and re.match(r"\d{4}-\d{2}-\d{2}$", value):
                return value
    return None


def dated_lastmod(path: Path) -> str:
    m = DAY_SLIDE_DATE_RE.match(path.name) or DAILY_REPORT_DATE_RE.match(path.name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return iso_mtime(path)


def daily_news_lastmod(path: Path) -> str:
    m = DAILY_NEWS_DATE_RE.search(path.name)
    if m:
        return m.group(1)
    return iso_mtime(path)


def url_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel.endswith("/index.html"):
        return f"{BASE_URL}/{rel[:-10]}"
    return f"{BASE_URL}/{rel}"


def collect_urls() -> list[dict]:
    today = dt.date.today().isoformat()
    urls: list[dict] = []
    homepage_lastmod = latest_homepage_date()

    # Root pages
    for name, freq, prio in ROOT_PAGES:
        p = ROOT / name
        if p.exists():
            urls.append({
                "loc": f"{BASE_URL}/" if name == "index.html" else f"{BASE_URL}/{name}",
                "lastmod": homepage_lastmod if name == "index.html" and homepage_lastmod else iso_mtime(p),
                "changefreq": freq,
                "priority": prio,
            })

    # Presentation pages (non-recursive per directory)
    for rel_dir, freq, prio in PRESENTATION_DIRS:
        d = ROOT / rel_dir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.html")):
            if not listed_in(rel_dir, p):
                continue
            urls.append({
                "loc": url_for(p),
                "lastmod": dated_lastmod(p),
                "changefreq": freq,
                "priority": prio,
            })

    for rel_dir, freq, prio in DAILY_NEWS_DIRS:
        d = ROOT / rel_dir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.html"), key=lambda x: x.name, reverse=True):
            if not listed_in(rel_dir, p):
                continue
            urls.append({
                "loc": url_for(p),
                "lastmod": latest_homepage_date() if p.name == "index.html" else daily_news_lastmod(p),
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing")
    ap.add_argument("--out", default=str(ROOT / "sitemap.xml"), help="Output file path")
    args = ap.parse_args(argv)

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
