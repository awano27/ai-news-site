#!/usr/bin/env python3
"""
Validation script for tool data.

Validates:
- JSON schema compliance
- Required fields presence
- URL format validity
- No duplicate IDs
- Category validity

Usage:
    python scripts/validate.py [--strict]

Exit codes:
    0: All validations passed
    1: Validation errors found
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.config import TOOLS_FILE, INDEX_FILE, DAILY_DIR, LOG_FORMAT, LOG_LEVEL

# Setup logging
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Valid categories
VALID_CATEGORIES = {"meeting", "docs", "pm", "automation", "ai", "dev", "ph", "other"}

# Valid sources
VALID_SOURCES = {"producthunt", "hn", "github", "manual", "rss"}

# ID pattern
ID_PATTERN = re.compile(r'^[a-z0-9-]+$')

# URL pattern (basic)
URL_PATTERN = re.compile(r'^https?://')


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False
    if not URL_PATTERN.match(url):
        return False
    try:
        result = urlparse(url)
        return bool(result.netloc)
    except:
        return False


def validate_tool(tool: Dict, strict: bool = False) -> List[str]:
    """
    Validate a single tool.

    Returns list of error messages (empty if valid).
    """
    errors = []
    tool_name = tool.get("name", tool.get("id", "unknown"))

    # Required fields
    required = ["id", "name", "tagline", "categories", "links", "first_seen_at", "source"]
    for field in required:
        if field not in tool:
            errors.append(f"[{tool_name}] Missing required field: {field}")

    # ID format
    tool_id = tool.get("id", "")
    if tool_id and not ID_PATTERN.match(tool_id):
        errors.append(f"[{tool_name}] Invalid ID format: {tool_id}")

    # Categories
    categories = tool.get("categories", [])
    if not isinstance(categories, list) or len(categories) == 0:
        errors.append(f"[{tool_name}] Categories must be non-empty array")
    else:
        for cat in categories:
            if cat not in VALID_CATEGORIES:
                errors.append(f"[{tool_name}] Invalid category: {cat}")

    # Source
    source = tool.get("source", "")
    if source and source not in VALID_SOURCES:
        errors.append(f"[{tool_name}] Invalid source: {source}")

    # Links
    links = tool.get("links", {})
    if not isinstance(links, dict):
        errors.append(f"[{tool_name}] Links must be an object")
    elif "official" not in links:
        errors.append(f"[{tool_name}] Missing official link")
    else:
        official = links.get("official", "")
        if not validate_url(official):
            errors.append(f"[{tool_name}] Invalid official URL: {official}")

        # Validate other URLs if present
        for key in ["producthunt", "hn", "github"]:
            url = links.get(key, "")
            if url and not validate_url(url):
                if strict:
                    errors.append(f"[{tool_name}] Invalid {key} URL: {url}")

    # Date format
    first_seen = tool.get("first_seen_at", "")
    if first_seen:
        try:
            from datetime import date
            date.fromisoformat(first_seen)
        except ValueError:
            errors.append(f"[{tool_name}] Invalid date format: {first_seen}")

    # Score range
    score = tool.get("score")
    if score is not None:
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            errors.append(f"[{tool_name}] Score must be 0-100: {score}")

    # String length limits
    if len(tool.get("name", "")) > 100:
        errors.append(f"[{tool_name}] Name too long (max 100)")

    if len(tool.get("tagline", "")) > 200:
        errors.append(f"[{tool_name}] Tagline too long (max 200)")

    if len(tool.get("description", "")) > 2000:
        errors.append(f"[{tool_name}] Description too long (max 2000)")

    return errors


def validate_tools_file() -> Tuple[int, int, List[str]]:
    """
    Validate tools.json file.

    Returns (total_count, error_count, error_messages).
    """
    errors = []

    if not TOOLS_FILE.exists():
        return 0, 1, ["tools.json does not exist"]

    try:
        with open(TOOLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return 0, 1, [f"Invalid JSON in tools.json: {e}"]

    tools = data.get("tools", [])

    if not isinstance(tools, list):
        return 0, 1, ["'tools' must be an array"]

    # Check for duplicate IDs
    seen_ids = set()
    for tool in tools:
        tool_id = tool.get("id", "")
        if tool_id in seen_ids:
            errors.append(f"Duplicate ID: {tool_id}")
        seen_ids.add(tool_id)

    # Validate each tool
    for tool in tools:
        tool_errors = validate_tool(tool)
        errors.extend(tool_errors)

    return len(tools), len(errors), errors


def validate_index_file() -> List[str]:
    """Validate index.json file."""
    errors = []

    if not INDEX_FILE.exists():
        return ["index.json does not exist"]

    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON in index.json: {e}"]

    # Check required fields
    required = ["total_count", "categories", "sources", "updated_at"]
    for field in required:
        if field not in data:
            errors.append(f"index.json missing field: {field}")

    # Check category keys
    categories = data.get("categories", {})
    for cat in VALID_CATEGORIES:
        if cat not in categories:
            errors.append(f"index.json missing category: {cat}")

    return errors


def validate_daily_files() -> List[str]:
    """Validate daily/*.json files."""
    errors = []

    if not DAILY_DIR.exists():
        return []  # OK if no daily files yet

    for daily_file in DAILY_DIR.glob("*.json"):
        try:
            with open(daily_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check structure
            if "date" not in data:
                errors.append(f"{daily_file.name}: missing 'date' field")
            if "tools" not in data:
                errors.append(f"{daily_file.name}: missing 'tools' field")

            # Validate date in filename matches content
            filename_date = daily_file.stem
            content_date = data.get("date", "")
            if filename_date != content_date:
                errors.append(f"{daily_file.name}: date mismatch (file: {filename_date}, content: {content_date})")

        except json.JSONDecodeError as e:
            errors.append(f"{daily_file.name}: invalid JSON - {e}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate tool data files")
    parser.add_argument("--strict", action="store_true", help="Enable strict validation")
    args = parser.parse_args()

    logger.info("Starting validation...")

    all_errors = []
    total_tools = 0

    # Validate tools.json
    logger.info("Validating tools.json...")
    count, error_count, errors = validate_tools_file()
    total_tools = count
    all_errors.extend(errors)

    if count > 0:
        logger.info(f"  Found {count} tools, {error_count} errors")
    else:
        logger.warning("  No tools found (file may be empty or missing)")

    # Validate index.json
    logger.info("Validating index.json...")
    errors = validate_index_file()
    all_errors.extend(errors)
    logger.info(f"  {len(errors)} errors")

    # Validate daily files
    logger.info("Validating daily/*.json files...")
    errors = validate_daily_files()
    all_errors.extend(errors)
    daily_count = len(list(DAILY_DIR.glob("*.json"))) if DAILY_DIR.exists() else 0
    logger.info(f"  Checked {daily_count} files, {len(errors)} errors")

    # Summary
    print()
    if all_errors:
        logger.error(f"Validation FAILED with {len(all_errors)} errors:")
        for error in all_errors[:20]:  # Limit output
            logger.error(f"  - {error}")
        if len(all_errors) > 20:
            logger.error(f"  ... and {len(all_errors) - 20} more errors")
        sys.exit(1)
    else:
        logger.info(f"Validation PASSED: {total_tools} tools, {daily_count} daily files")
        sys.exit(0)


if __name__ == "__main__":
    main()
