#!/usr/bin/env python3
"""Build the deterministic browser search index for the news archive."""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEWS = ROOT / "public-pages" / "news"
SLIDES = ROOT / "presentations" / "day_slides"
OUTPUT = NEWS / "search_index.json"
SKIP = {"archive_index.json", "daily_index.json", "daily_latest.json", "version.json", "search_index.json"}

SLIDE_DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.I | re.S)
DESC_RE = re.compile(
    r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
    re.I,
)
TRAILING_DATE_RE = re.compile(r"\s*(?:\|\s*)?\d{4}-\d{2}-\d{2}\s*$")


def iter_articles(data):
    if isinstance(data, list):
        return data
    for key in ("articles", "items", "news"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


def _plain_text(html_fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html_fragment or "")
    return " ".join(unescape(text).split())


def extract_slide_record(path: Path) -> dict | None:
    """Title + description only. Body text is intentionally omitted."""
    match = SLIDE_DATE_RE.fullmatch(path.name)
    if not match:
        return None
    try:
        html = path.read_text(encoding="utf-8")
    except OSError:
        return None
    title_m = TITLE_RE.search(html)
    title = TRAILING_DATE_RE.sub("", _plain_text(title_m.group(1) if title_m else "")).strip()
    if not title:
        return None
    date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    url = f"/presentations/day_slides/{path.name}"
    row = {
        "date": date,
        "title": title,
        "category": "スライド",
        "source": "AI Intelligence Hub",
        "url": url,
        "type": "slide",
    }
    desc_m = DESC_RE.search(html)
    if desc_m:
        summary = unescape(desc_m.group(1)).strip()
        if summary:
            row["summary"] = summary[:240]
    return row


def collect_news_rows() -> dict[tuple[str, str], dict]:
    rows: dict[tuple[str, str], dict] = {}
    for path in sorted(NEWS.glob("*.json")):
        if path.name in SKIP:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        fallback_date = path.name[:10]
        for article in iter_articles(data):
            url = str(article.get("url") or article.get("link") or "").strip()
            title = str(article.get("title") or article.get("name") or "").strip()
            if not url or not title:
                continue
            date = str(article.get("date") or article.get("published_at") or fallback_date)[:10]
            row = {
                "date": date,
                "title": title,
                "category": str(article.get("category") or article.get("tag_group") or "その他"),
                "source": str(article.get("source") or article.get("rss_source") or ""),
                "url": url,
            }
            summary = str(article.get("summary") or article.get("description") or "").strip()
            if summary:
                row["summary"] = summary[:120]
            rows[(date, url)] = row
    return rows


def collect_slide_rows() -> dict[tuple[str, str], dict]:
    rows: dict[tuple[str, str], dict] = {}
    for path in sorted(SLIDES.glob("day_slide_????_??_??.html")):
        row = extract_slide_record(path)
        if not row:
            continue
        rows[(row["date"], row["url"])] = row
    return rows


def main() -> int:
    rows = collect_news_rows()
    slides = collect_slide_rows()
    rows.update(slides)
    result = sorted(rows.values(), key=lambda row: (row["date"], row["title"], row["url"]), reverse=True)
    payload = json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n"
    if len(payload.encode("utf-8")) > 2_000_000:
        result = [
            ({k: v for k, v in row.items() if k != "summary"} if row.get("type") != "slide" else row)
            for row in result
        ]
        payload = json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n"
    OUTPUT.write_text(payload, encoding="utf-8", newline="\n")
    slide_n = sum(1 for row in result if row.get("type") == "slide")
    print(
        f"[build_search_index] {len(result)} entries "
        f"(slides={slide_n}), {len(payload.encode('utf-8'))} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
