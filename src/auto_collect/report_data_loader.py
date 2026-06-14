"""
report_data_loader.py — Load daily news items from JSON archives or MMDD.txt.

Extracted from report_generator.py.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict

from .config import INPUT_DAY_DIR

logger = logging.getLogger(__name__)


def load_date_range(news_dir: Path, start: date, end: date) -> List[Dict]:
    """Load news items from JSON archives for a date range."""
    all_items: List[Dict] = []
    current = start

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")

        # Try JSON archive first
        json_path = news_dir / f"{date_str}.json"
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                items = data.get("items", [])
                for item in items:
                    item["_date"] = date_str
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"[Report] Failed to load {json_path}: {e}")

        # Also try input/day/MMDD.txt for sections
        mmdd = current.strftime("%m%d")
        txt_path = INPUT_DAY_DIR / f"{mmdd}.txt"
        if txt_path.exists() and not json_path.exists():
            try:
                content = txt_path.read_text(encoding="utf-8")
                parsed = parse_day_txt(content, date_str)
                all_items.extend(parsed)
            except Exception as e:
                logger.warning(f"[Report] Failed to parse {txt_path}: {e}")

        current += timedelta(days=1)

    return all_items


def parse_day_txt(content: str, date_str: str) -> List[Dict]:
    """Parse a day txt file into items."""
    items: List[Dict] = []
    current_title = ""
    current_score = 0
    current_category = ""
    current_lines: List[str] = []

    for line in content.split("\n"):
        if line.startswith("■ "):
            # Save previous item
            if current_title:
                items.append(
                    {
                        "title": current_title,
                        "score": current_score,
                        "category": current_category,
                        "summary": " ".join(current_lines),
                        "_date": date_str,
                    }
                )

            # Parse new item
            match = re.match(r"■ (.+?)（(.+?) / スコア: (\d+)）", line)
            if match:
                current_title = match.group(1)
                current_category = match.group(2)
                current_score = int(match.group(3))
            else:
                current_title = line[2:].strip()
                current_score = 50
                current_category = "AI Technology"
            current_lines = []
        elif (
            line.strip()
            and not line.startswith("=")
            and not line.startswith("📰")
            and not line.startswith("💰")
            and not line.startswith("🔥")
            and not line.startswith("🤗")
        ):
            current_lines.append(line.strip())

    # Save last item
    if current_title:
        items.append(
            {
                "title": current_title,
                "score": current_score,
                "category": current_category,
                "summary": " ".join(current_lines),
                "_date": date_str,
            }
        )

    return items
