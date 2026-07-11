#!/usr/bin/env python3
"""Build the deterministic browser search index for the news archive."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEWS = ROOT / "public-pages" / "news"
OUTPUT = NEWS / "search_index.json"
SKIP = {"archive_index.json", "daily_index.json", "daily_latest.json", "version.json", "search_index.json"}


def iter_articles(data):
    if isinstance(data, list):
        return data
    for key in ("articles", "items", "news"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


def main() -> int:
    rows = {}
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
            row = {"date": date, "title": title, "category": str(article.get("category") or article.get("tag_group") or "その他"), "source": str(article.get("source") or article.get("rss_source") or ""), "url": url}
            summary = str(article.get("summary") or article.get("description") or "").strip()
            if summary:
                row["summary"] = summary[:120]
            rows[(date, url)] = row
    result = sorted(rows.values(), key=lambda row: (row["date"], row["title"], row["url"]), reverse=True)
    payload = json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n"
    if len(payload.encode("utf-8")) > 2_000_000:
        result = [{k: v for k, v in row.items() if k != "summary"} for row in result]
        payload = json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n"
    OUTPUT.write_text(payload, encoding="utf-8", newline="\n")
    print(f"[build_search_index] {len(result)} entries, {len(payload.encode('utf-8'))} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
