#!/usr/bin/env python3
"""
Main ingest script for collecting tools from multiple sources.

Usage:
    python scripts/ingest.py [--date YYYY-MM-DD] [--dry-run]

Environment variables:
    PH_TOKEN: Product Hunt API token (required for PH collection)
    GITHUB_TOKEN: GitHub API token (optional, increases rate limits)
"""

import argparse
import json
import logging
import sys
from datetime import date, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.config import (
    DATA_DIR, DAILY_DIR, TOOLS_FILE, INDEX_FILE,
    SCORING_WEIGHTS, PRIORITY_CATEGORIES, CATEGORY_KEYWORDS,
    DEDUPE_NAME_THRESHOLD, LOG_FORMAT, LOG_LEVEL
)
from scripts.collectors import ProductHuntCollector, HackerNewsCollector, GitHubCollector

# Setup logging
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def load_existing_tools() -> Dict[str, Dict]:
    """Load existing tools from tools.json."""
    if not TOOLS_FILE.exists():
        return {}

    try:
        with open(TOOLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            tools = data.get("tools", [])
            return {t["id"]: t for t in tools}
    except Exception as e:
        logger.error(f"Error loading existing tools: {e}")
        return {}


def save_tools(tools: List[Dict], updated_at: str):
    """Save tools to tools.json."""
    data = {
        "$schema": "./schema/tool.json",
        "version": "1.0.0",
        "updated_at": updated_at,
        "tools": tools
    }

    with open(TOOLS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(tools)} tools to {TOOLS_FILE}")


def save_daily(tools: List[Dict], target_date: date):
    """Save daily collection to daily/YYYY-MM-DD.json."""
    daily_file = DAILY_DIR / f"{target_date.isoformat()}.json"

    data = {
        "date": target_date.isoformat(),
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "count": len(tools),
        "tools": tools
    }

    with open(daily_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(tools)} tools to {daily_file}")


def update_index(tools: List[Dict], latest_date: date):
    """Update index.json with statistics."""
    # Count by category
    categories = {"meeting": 0, "docs": 0, "pm": 0, "automation": 0,
                  "ai": 0, "dev": 0, "ph": 0, "other": 0}
    sources = {"producthunt": 0, "hn": 0, "github": 0, "manual": 0, "rss": 0}
    published_count = 0

    for tool in tools:
        for cat in tool.get("categories", []):
            if cat in categories:
                categories[cat] += 1

        source = tool.get("source", "other")
        if source in sources:
            sources[source] += 1

        if tool.get("published", False):
            published_count += 1

    index = {
        "latest_date": latest_date.isoformat(),
        "total_count": len(tools),
        "published_count": published_count,
        "categories": categories,
        "sources": sources,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    logger.info(f"Updated index: {len(tools)} total, {published_count} published")


def normalize_domain(url: str) -> str:
    """Extract normalized domain from URL."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return ""


def calculate_score(tool: Dict) -> float:
    """Calculate a score for a tool based on various factors."""
    score = 50.0  # Base score

    # Source rank contribution (lower rank = better)
    rank = tool.get("source_rank")
    if rank:
        # Top 5 gets full points, degrades after
        rank_score = max(0, (10 - rank) / 10) * SCORING_WEIGHTS["source_rank"]
        score += rank_score

    # Votes/stars contribution (logarithmic scale)
    votes = tool.get("source_votes", 0)
    if votes > 0:
        import math
        # Log scale: 10 votes = ~7, 100 = ~14, 1000 = ~21
        vote_score = min(SCORING_WEIGHTS["source_votes"],
                        math.log10(votes + 1) * 7)
        score += vote_score

    # Has real official URL (not just GitHub/PH)
    official = tool.get("links", {}).get("official", "")
    domain = normalize_domain(official)
    if domain and domain not in ["github.com", "producthunt.com"]:
        score += SCORING_WEIGHTS["has_official_url"]

    # Has description
    if tool.get("description") and len(tool.get("description", "")) > 50:
        score += SCORING_WEIGHTS["has_description"]

    # Topic diversity
    topics = tool.get("topics", [])
    if len(topics) >= 3:
        score += SCORING_WEIGHTS["topic_diversity"]

    # Category match bonus
    categories = tool.get("categories", [])
    if any(cat in PRIORITY_CATEGORIES for cat in categories):
        score += SCORING_WEIGHTS["category_match"]

    return min(100.0, max(0.0, score))


def is_duplicate(new_tool: Dict, existing_tools: Dict[str, Dict],
                 seen_domains: Set[str]) -> bool:
    """Check if a tool is a duplicate of an existing one."""
    new_id = new_tool.get("id", "")

    # Exact ID match
    if new_id in existing_tools:
        return True

    # Domain-based deduplication
    official = new_tool.get("links", {}).get("official", "")
    domain = normalize_domain(official)

    if domain and domain in seen_domains:
        return True

    # Fuzzy name matching
    new_name = new_tool.get("name", "").lower()
    for existing in existing_tools.values():
        existing_name = existing.get("name", "").lower()
        similarity = SequenceMatcher(None, new_name, existing_name).ratio()
        if similarity >= DEDUPE_NAME_THRESHOLD:
            logger.debug(f"Duplicate by name: '{new_tool['name']}' ~ '{existing['name']}' ({similarity:.2f})")
            return True

    return False


def enhance_categories(tool: Dict) -> List[str]:
    """Enhance category classification based on content analysis."""
    categories = set(tool.get("categories", []))

    # Combine all text for analysis
    text = " ".join([
        tool.get("name", ""),
        tool.get("tagline", ""),
        tool.get("description", ""),
        " ".join(tool.get("topics", []))
    ]).lower()

    # Check each category's keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            categories.add(category)

    # Ensure at least one category
    if not categories:
        categories.add("other")

    return list(categories)


def collect_all(target_date: date) -> List[Dict]:
    """Collect from all sources."""
    all_tools = []

    collectors = [
        ("Product Hunt", ProductHuntCollector()),
        ("Hacker News", HackerNewsCollector()),
        ("GitHub", GitHubCollector()),
    ]

    for name, collector in collectors:
        logger.info(f"Collecting from {name}...")
        try:
            tools = collector.collect(target_date)
            all_tools.extend(tools)
            logger.info(f"Collected {len(tools)} from {name}")
        except Exception as e:
            logger.error(f"Error collecting from {name}: {e}")

    return all_tools


def process_tools(new_tools: List[Dict], existing_tools: Dict[str, Dict]) -> List[Dict]:
    """Process new tools: dedupe, categorize, score."""
    processed = []
    seen_domains = set()

    # Build seen domains from existing tools
    for tool in existing_tools.values():
        domain = normalize_domain(tool.get("links", {}).get("official", ""))
        if domain:
            seen_domains.add(domain)

    for tool in new_tools:
        # Skip duplicates
        if is_duplicate(tool, existing_tools, seen_domains):
            logger.debug(f"Skipping duplicate: {tool.get('name')}")
            continue

        # Enhance categories
        tool["categories"] = enhance_categories(tool)

        # Calculate score
        tool["score"] = round(calculate_score(tool), 1)

        # Add to processed
        processed.append(tool)

        # Track domain
        domain = normalize_domain(tool.get("links", {}).get("official", ""))
        if domain:
            seen_domains.add(domain)

    # Sort by score descending
    processed.sort(key=lambda t: t.get("score", 0), reverse=True)

    return processed


def main():
    parser = argparse.ArgumentParser(description="Ingest tools from multiple sources")
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD), default: yesterday")
    parser.add_argument("--dry-run", action="store_true", help="Don't save results")
    args = parser.parse_args()

    # Determine target date
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        from datetime import timedelta
        target_date = date.today() - timedelta(days=1)

    logger.info(f"Starting ingest for {target_date}")

    # Load existing tools
    existing_tools = load_existing_tools()
    logger.info(f"Loaded {len(existing_tools)} existing tools")

    # Collect from all sources
    new_tools = collect_all(target_date)
    logger.info(f"Collected {len(new_tools)} total from all sources")

    if not new_tools:
        logger.warning("No new tools collected")
        # Still update index for 0-count days
        if not args.dry_run:
            save_daily([], target_date)
        return

    # Process (dedupe, categorize, score)
    processed = process_tools(new_tools, existing_tools)
    logger.info(f"Processed {len(processed)} unique new tools")

    if args.dry_run:
        logger.info("Dry run - not saving")
        for tool in processed[:10]:
            logger.info(f"  - {tool['name']} (score: {tool['score']}, categories: {tool['categories']})")
        return

    # Merge with existing
    for tool in processed:
        existing_tools[tool["id"]] = tool

    # Convert back to list
    all_tools = list(existing_tools.values())

    # Sort by score for main file
    all_tools.sort(key=lambda t: t.get("score", 0), reverse=True)

    # Save
    now = datetime.utcnow().isoformat() + "Z"
    save_tools(all_tools, now)
    save_daily(processed, target_date)
    update_index(all_tools, target_date)

    logger.info(f"Ingest complete: {len(processed)} new, {len(all_tools)} total")


if __name__ == "__main__":
    main()
