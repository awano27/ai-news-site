#!/usr/bin/env python3
"""Fetch ai-news-radar daily-brief.json and convert to local news/{date}.json format.

Source: https://github.com/LearnPrompt/ai-news-radar
Data:   https://raw.githubusercontent.com/LearnPrompt/ai-news-radar/master/data/daily-brief.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

RADAR_URL = (
    "https://raw.githubusercontent.com/LearnPrompt/ai-news-radar/master/data/daily-brief.json"
)

# Map radar categories → our site categories
CATEGORY_MAP = {
    "model": "tools",
    "agent": "tools",
    "product": "tools",
    "industry": "business",
    "research": "research",
    "policy": "business",
    "infrastructure": "tools",
    "open_source": "tools",
}

STARS_BY_SCORE = [(0.85, 5), (0.75, 4), (0.60, 3), (0.45, 2)]


def score_to_stars(score: float) -> int:
    for threshold, stars in STARS_BY_SCORE:
        if score >= threshold:
            return stars
    return 1


def convert_item(story: dict[str, Any], today: str) -> dict[str, Any]:
    category = CATEGORY_MAP.get(story.get("category", ""), "tools")
    source_url = story.get("primary_url") or story.get("url", "")
    source_name = story.get("source_name", "")
    score = story.get("score") or story.get("importance", 0.5)

    blurb_parts = []
    if story.get("source_count", 1) > 1:
        names = "、".join(story.get("source_names", [source_name])[:3])
        blurb_parts.append(f"【{story['source_count']}ソース報道】{names}")
    blurb_parts.append(f"スコア: {score:.2f}")
    if story.get("reasons"):
        blurb_parts.append(" / ".join(story["reasons"]))

    return {
        "title": story.get("title", ""),
        "blurb": " | ".join(blurb_parts),
        "category": category,
        "date": today,
        "stars": score_to_stars(score),
        "source": {"url": source_url, "name": source_name},
    }


def group_by_category(items: list[dict]) -> dict[str, list]:
    result: dict[str, list] = {}
    for item in items:
        result.setdefault(item["category"], []).append(item)
    return result


def fetch_and_convert(output_dir: Path, date_str: str | None = None) -> Path:
    print(f"Fetching {RADAR_URL} ...")
    resp = requests.get(RADAR_URL, timeout=30)
    resp.raise_for_status()
    radar = resp.json()

    generated_at = radar.get("generated_at", "")
    print(f"  ai-news-radar generated_at: {generated_at}")
    print(f"  total_items: {radar.get('total_items', 0)}")

    if date_str is None:
        # Use the date embedded in generated_at or today
        if generated_at:
            dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        else:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    today = date_str
    items = [convert_item(s, today) for s in radar.get("items", [])]
    sections = group_by_category(items)

    # Identify top story for highlight
    highlight: dict = {}
    if items:
        top = max(items, key=lambda x: x["stars"])
        highlight = {"title": top["title"], "source": top["source"]}

    out_doc = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "ai-news-radar",
        "source_url": RADAR_URL,
        "highlight": highlight,
        "sections": sections,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{today}.json"
    out_path.write_text(json.dumps(out_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Wrote {out_path}  ({len(items)} items across {len(sections)} categories)")
    return out_path


def main() -> None:
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "news"
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    out_path = fetch_and_convert(output_dir, date_arg)

    # Pretty-print summary
    doc = json.loads(out_path.read_text(encoding="utf-8"))
    print("\n=== Summary ===")
    for cat, entries in doc["sections"].items():
        print(f"  [{cat}] {len(entries)} items")
        for e in entries[:2]:
            print(f"    ★{'★' * (e['stars'] - 1)}{'☆' * (5 - e['stars'])} {e['title'][:60]}")


if __name__ == "__main__":
    main()
