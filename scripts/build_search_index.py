#!/usr/bin/env python3
"""Incrementally extend the browser search corpus without discarding history.

Legacy dated files are aggregates, not a complete recoverable source corpus.
The published index is therefore the preservation baseline. New daily capture
identities use edition date + canonical URL; legacy rows are never collapsed
or rewritten. Only explicitly managed capture/slide rows may refresh metadata.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.auto_collect.publication_priority import prefer_existing

NEWS = ROOT / "public-pages" / "news"
SLIDES = ROOT / "presentations" / "day_slides"
OUTPUT = NEWS / "search_index.json"
SKIP = {"archive_index.json", "daily_index.json", "daily_latest.json", "version.json", "search_index.json"}
DATED_FILE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\.json$")
SLIDE_DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.I | re.S)
TRAILING_DATE_RE = re.compile(r"\s*(?:\|\s*)?\d{4}-\d{2}-\d{2}\s*$")
TRACKING_PARAMS = {"fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "_ga", "_gl"}


def valid_date(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def valid_publication_date(value: object) -> bool:
    if not isinstance(value, str) or not valid_date(value[:10]):
        return False
    if len(value) == 10:
        return True
    if value[10:11] not in {"T", " "}:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def canonical_url(value: object) -> str | None:
    """Validate external links and remove only well-known tracking for identity.

    The original URL is always retained in records and used as the link target.
    """
    if not isinstance(value, str) or not value or re.search(r"[\s\x00-\x1f\x7f\\]", value):
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
            return None
        host = parts.hostname.lower()
        port = parts.port  # Reject malformed ports before storing a link.
        if ":" in host:
            host = f"[{host}]"
        if port and not ((parts.scheme.lower() == "https" and port == 443) or (parts.scheme.lower() == "http" and port == 80)):
            host += f":{port}"
        query = sorted((key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
                       if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS)
        return urlunsplit((parts.scheme.lower(), host, parts.path or "/", urlencode(query), ""))
    except ValueError:
        return None


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc


def iter_articles(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("articles", "items", "news"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("News input must contain an articles/items/news list")


def normalize_daily_payload(data: object) -> dict:
    """Validate one daily edition and retain actual per-article source metadata."""
    if not isinstance(data, dict) or not valid_date(data.get("date")) or not isinstance(data.get("items"), list):
        raise ValueError("Daily capture requires a valid YYYY-MM-DD date and items list")
    if "schema_version" in data and data["schema_version"] != 1:
        raise ValueError("Unsupported daily capture schema_version")
    day = data["date"]
    snapshot = data.get("schema_version") == 1
    items, seen = [], set()
    excluded, duplicates = 0, 0
    for article in data["items"]:
        if not isinstance(article, dict):
            raise ValueError("Daily capture items must be objects")
        for field in ("type", "summary", "description", "body", "tldr", "source", "rss_source", "category", "tag_group"):
            if article.get(field) is not None and not isinstance(article[field], str):
                raise ValueError(f"Daily article {field} must be text")
        url = article.get("url") or article.get("link") or ""
        title = article.get("title") or article.get("name") or ""
        canonical = canonical_url(url)
        if not canonical or not isinstance(title, str) or not title.strip():
            excluded += 1
            continue
        if article.get("type", "news") not in {"news", "x"}:
            excluded += 1
            continue
        published_at = article.get("published_at") or (None if snapshot else article.get("date"))
        if published_at and not valid_publication_date(published_at):
            excluded += 1
            continue
        if snapshot and article.get("date") != day:
            raise ValueError("Snapshot article date must match its edition date")
        if canonical in seen:
            duplicates += 1
            continue
        seen.add(canonical)
        item = dict(article)
        item.update(date=day, title=title.strip(), url=url, type=article.get("type", "news"),
                    category=str(article.get("category") or article.get("tag_group") or "その他"),
                    source=str(article.get("source") or article.get("rss_source") or ""))
        if published_at:
            item["published_at"] = published_at
        summary = article.get("summary") or article.get("description") or article.get("body") or article.get("tldr")
        if isinstance(summary, str) and summary.strip():
            item["summary"] = summary.strip()
        items.append(item)
    if not items:
        raise ValueError("Daily capture has no valid articles; refusing to replace published artifacts")
    payload = {"schema_version": 1, "date": day, "total": len(items),
               "news_count": sum(item["type"] == "news" for item in items),
               "x_count": sum(item["type"] == "x" for item in items),
               "sources": dict(sorted(Counter(item["source"] for item in items if item["source"]).items())),
               "items": items}
    provenance = {"source_item_count": len(data["items"]), "excluded_item_count": excluded,
                  "duplicate_item_count": duplicates}
    if snapshot and "source_item_count" in data:
        provenance = {key: data.get(key) for key in provenance}
        if any(type(value) is not int or value < 0 for value in provenance.values()) or (
                provenance["source_item_count"] != len(items) + provenance["excluded_item_count"] + provenance["duplicate_item_count"]):
            raise ValueError("Snapshot capture count provenance is inconsistent")
    payload.update(provenance)
    if data.get("generated_iso"):
        payload["generated_iso"] = data["generated_iso"]
    return payload


def _plain_text(html_fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html_fragment or "")
    return " ".join(unescape(text).split())


class _SlideDescriptionParser(HTMLParser):
    """Read description metadata independent of HTML attribute order/casing."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.description = ""

    def handle_starttag(self, tag, attrs):
        if tag != "meta" or self.description:
            return
        attributes = dict(attrs)
        if (attributes.get("name") or "").lower() == "description":
            self.description = (attributes.get("content") or "").strip()


def extract_slide_record(path: Path) -> dict | None:
    """Title + description only. Body text is intentionally omitted."""
    match = SLIDE_DATE_RE.fullmatch(path.name)
    if not match:
        return None
    day = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    if not valid_date(day):
        return None
    html = path.read_text(encoding="utf-8")
    title_m = TITLE_RE.search(html)
    title = TRAILING_DATE_RE.sub("", _plain_text(title_m.group(1) if title_m else "")).strip()
    if not title:
        return None
    row = {"date": day, "title": title, "category": "スライド", "source": "AI Intelligence Hub",
           "url": f"/presentations/day_slides/{path.name}", "type": "slide"}
    description = _SlideDescriptionParser()
    description.feed(html)
    description.close()
    if description.description:
        row["summary"] = description.description[:240]
    return row


def is_legacy_daily_aggregate(data: object) -> bool:
    """Recognize update_news_archive.py's one-bulletin-per-day transport.

    Its URL is merely the first link in a complete dayfile, not an individual
    article identity. Never infer new article coverage from these aggregates.
    Existing corpus entries are retained independently of this source reader.
    """
    if not isinstance(data, dict) or data.get("count") != 1:
        return False
    items, source = data.get("items"), data.get("source")
    if not isinstance(items, list) or len(items) != 1 or not isinstance(source, str):
        return False
    source = source.replace("\\", "/")
    return not source.lower().startswith(("https://", "http://")) and bool(
        re.search(r"(?:^|/)input/day/[^/]+\.txt$", source, re.I))


def collect_news_rows(news: Path | None = None) -> dict[tuple[str, str], dict]:
    """Read legacy sources only as additive candidates, never as a full rebuild."""
    rows = {}
    for path in sorted((news or NEWS).glob("*.json")):
        if path.name in SKIP or not DATED_FILE_RE.fullmatch(path.name) or not valid_date(path.stem):
            continue
        data = load_json(path)
        if is_legacy_daily_aggregate(data):
            continue
        for article in iter_articles(data):
            if not isinstance(article, dict):
                raise ValueError(f"Invalid article object in {path}")
            url = article.get("url") or article.get("link") or ""
            title = article.get("title") or article.get("name") or ""
            day = article.get("date") or article.get("published_at") or path.stem
            canonical = canonical_url(url)
            if not canonical or not isinstance(title, str) or not title.strip() or not valid_publication_date(day):
                continue
            row = {"date": day[:10], "title": title.strip(),
                   "category": str(article.get("category") or article.get("tag_group") or "その他"),
                   "source": str(article.get("source") or article.get("rss_source") or ""), "url": url}
            summary = article.get("summary") or article.get("description") or ""
            if isinstance(summary, str) and summary.strip():
                row["summary"] = summary.strip()[:120]
            rows.setdefault((row["date"], canonical), row)
    return rows


def collect_slide_rows(slides: Path | None = None) -> dict[tuple[str, str], dict]:
    rows = {}
    for path in sorted((slides or SLIDES).glob("day_slide_????_??_??.html")):
        row = extract_slide_record(path)
        if row:
            rows[(row["date"], row["url"])] = row
    return rows


def _daily_rows(payload: dict) -> list[dict]:
    result = []
    for item in payload["items"]:
        row = {key: item[key] for key in ("date", "title", "category", "source", "url", "type")}
        row["capture_schema"] = 1
        if item.get("published_at"):
            row["published_at"] = item["published_at"]
        if item.get("summary"):
            row["summary"] = item["summary"][:240]
        result.append(row)
    return result


def build_index(root: Path = ROOT, *, daily_payload: dict | None = None) -> list[dict]:
    """Plan a complete incremental index in memory; do not modify any files."""
    root = Path(root)
    news = root / "public-pages/news"
    output = news / "search_index.json"
    existing = load_json(output) if output.exists() else []
    if not isinstance(existing, list) or any(not isinstance(row, dict) or any(
        not isinstance(row.get(key), str) or not row[key] for key in ("date", "title", "url")) for row in existing):
        raise ValueError("Existing search index must be a list of date/title/url records")
    # Keep every stored identity, duplicate and field. Never run historical data
    # through new canonicalization/deduplication or size-driven summary removal.
    result = [dict(row) for row in existing]
    seen = {(row["date"], canonical_url(row["url"]) or row["url"]) for row in result}
    legacy_candidates = list(collect_news_rows(news).values())
    candidates = []
    editions = {}
    for path in sorted((news / "daily").glob("*.json")):
        if not DATED_FILE_RE.fullmatch(path.name) or not valid_date(path.stem):
            raise ValueError(f"Invalid daily snapshot filename: {path}")
        payload = normalize_daily_payload(load_json(path))
        if payload["date"] != path.stem:
            raise ValueError(f"Snapshot date does not match filename: {path}")
        editions[payload["date"]] = payload
    current = root / "daily-news/data.json"
    if daily_payload is not None or current.exists():
        payload = normalize_daily_payload(daily_payload if daily_payload is not None else load_json(current))
        prior = editions.get(payload["date"])
        if prior is None or not prefer_existing(prior, payload):
            editions[payload["date"]] = payload
    for day in sorted(editions):
        candidates.extend(_daily_rows(editions[day]))
    # Only explicitly managed daily records are eligible for metadata refresh.
    # Do not deduplicate an already-published corpus or replace legacy rows.
    managed = {}
    for row in result:
        if row.get("capture_schema") == 1 and row.get("type") != "slide":
            managed.setdefault((row["date"], canonical_url(row["url"]) or row["url"]), []).append(row)
    candidates.extend(legacy_candidates)
    for row in candidates:
        key = (row["date"], canonical_url(row["url"]) or row["url"])
        if row.get("capture_schema") == 1 and key in managed:
            for stored in managed[key]:
                stored.pop("summary", None)
                stored.pop("published_at", None)
                stored.update(row)
        elif key not in seen:
            result.append(row)
            seen.add(key)
    slides = collect_slide_rows(root / "presentations/day_slides")
    present_slides = set()
    for row in result:
        key = (row["date"], row["url"])
        if row.get("type") == "slide" and key in slides:
            if row.get("slide_schema") == 1:
                if "summary" not in slides[key]:
                    row.pop("summary", None)
                row.update(slides[key])
            present_slides.add(key)
    for key, row in slides.items():
        if key not in present_slides and key not in seen:
            result.append({**row, "slide_schema": 1})
    return sorted(result, key=lambda row: (row["date"], row["title"], row["url"]), reverse=True)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> bool:
    """Replace complete files only, and preserve unchanged file bytes/mtime."""
    if path.exists() and path.read_bytes() == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        return True
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_index(root: Path = ROOT) -> list[dict]:
    result = build_index(root)
    atomic_write(Path(root) / "public-pages/news/search_index.json", json_bytes(result))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        result = write_index(args.root)
    except (ValueError, OSError) as exc:
        print(f"[build_search_index] ERROR: {exc}", file=sys.stderr)
        return 1
    slide_n = sum(row.get("type") == "slide" for row in result)
    print(f"[build_search_index] {len(result)} entries (slides={slide_n}), {len(json_bytes(result))} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
