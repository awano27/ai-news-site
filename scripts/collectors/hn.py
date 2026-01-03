"""
Hacker News collector using Firebase API.

API Documentation: https://github.com/HackerNews/API
Rate Limit: No explicit limit, but be respectful (1s delay)

No authentication required.
"""

import re
import logging
from datetime import date, datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import urlparse

from .base import BaseCollector

logger = logging.getLogger(__name__)

# Firebase API endpoints
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
SHOW_STORIES_URL = f"{HN_API_BASE}/showstories.json"
TOP_STORIES_URL = f"{HN_API_BASE}/topstories.json"
ITEM_URL = f"{HN_API_BASE}/item/{{id}}.json"


class HackerNewsCollector(BaseCollector):
    """Collector for Hacker News using Firebase API."""

    # HN specific settings
    REQUEST_DELAY = 0.5  # HN API is generally fast
    MAX_STORIES = 30  # Limit stories to process
    MIN_SCORE = 10  # Minimum score to consider

    def __init__(self):
        super().__init__()

    @property
    def source_name(self) -> str:
        return "hn"

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """
        Collect tools from Hacker News Show HN.

        Args:
            target_date: Date to filter by (default: today, but checks recent posts)

        Returns:
            List of tool dictionaries
        """
        if target_date is None:
            target_date = date.today()

        # Calculate timestamp range for the target date
        start_ts = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp()
        end_ts = start_ts + 86400  # +24 hours

        logger.info(f"Collecting Hacker News Show HN stories for {target_date}")

        tools = []

        try:
            # Get Show HN story IDs
            self._rate_limit()
            response = self.session.get(SHOW_STORIES_URL, timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:self.MAX_STORIES * 2]  # Get extra for filtering

            logger.info(f"Processing {len(story_ids)} Show HN stories")

            rank = 0
            for story_id in story_ids:
                if rank >= self.MAX_STORIES:
                    break

                self._rate_limit()

                try:
                    item_response = self.session.get(
                        ITEM_URL.format(id=story_id),
                        timeout=10
                    )
                    item_response.raise_for_status()
                    item = item_response.json()

                    if not item:
                        continue

                    # Filter by date and score
                    item_time = item.get("time", 0)
                    score = item.get("score", 0)

                    # Skip if outside date range or low score
                    if not (start_ts <= item_time < end_ts):
                        continue

                    if score < self.MIN_SCORE:
                        continue

                    rank += 1

                    # Extract tool info
                    title = item.get("title", "")
                    url = item.get("url", "")

                    # Parse "Show HN: " prefix
                    name = title
                    tagline = ""

                    if title.lower().startswith("show hn:"):
                        name = title[8:].strip()

                    # Try to extract name and tagline from title
                    # Common patterns: "Name - Description" or "Name: Description"
                    for sep in [" – ", " - ", ": ", " — "]:
                        if sep in name:
                            parts = name.split(sep, 1)
                            name = parts[0].strip()
                            tagline = parts[1].strip() if len(parts) > 1 else ""
                            break

                    if not tagline:
                        tagline = name

                    # Clean up name
                    name = self._clean_name(name)

                    # Determine official URL
                    if not url:
                        # No URL means it's a text post, skip
                        continue

                    # Categorize
                    categories = self._categorize_from_content(title, url)

                    # HN discussion URL
                    hn_url = f"https://news.ycombinator.com/item?id={story_id}"

                    tool = self.create_tool_dict(
                        name=name,
                        tagline=tagline,
                        official_url=url,
                        categories=categories,
                        source_rank=rank,
                        source_votes=score,
                        extra_links={"hn": hn_url}
                    )

                    tools.append(tool)

                except Exception as e:
                    logger.warning(f"Error processing story {story_id}: {e}")
                    continue

            logger.info(f"Collected {len(tools)} tools from Hacker News")

        except Exception as e:
            logger.error(f"Error collecting from Hacker News: {e}")

        return tools

    def _clean_name(self, name: str) -> str:
        """Clean up a tool name."""
        # Remove common suffixes
        for suffix in [" (YC ", " [YC", "(Show HN)", "(beta)", "(alpha)"]:
            idx = name.find(suffix)
            if idx > 0:
                name = name[:idx].strip()

        # Remove parenthetical version info
        name = re.sub(r'\s*\([^)]*\)\s*$', '', name)

        # Limit length
        if len(name) > 50:
            name = name[:50].strip()

        return name

    def _categorize_from_content(self, title: str, url: str) -> List[str]:
        """Categorize based on title and URL content."""
        categories = []
        text = (title + " " + url).lower()

        # Category detection rules
        if any(kw in text for kw in ["meeting", "zoom", "video call", "transcri", "calendar"]):
            categories.append("meeting")

        if any(kw in text for kw in ["doc", "note", "wiki", "notion", "markdown", "write"]):
            categories.append("docs")

        if any(kw in text for kw in ["project", "task", "kanban", "agile", "sprint", "team"]):
            categories.append("pm")

        if any(kw in text for kw in ["automat", "workflow", "zapier", "n8n", "integrat"]):
            categories.append("automation")

        if any(kw in text for kw in ["ai", "gpt", "llm", "claude", "openai", "machine learn", "ml "]):
            categories.append("ai")

        if any(kw in text for kw in ["dev", "code", "api", "github", "debug", "ide", "program"]):
            categories.append("dev")

        # Check if it's a GitHub project
        if "github.com" in url:
            if "dev" not in categories:
                categories.append("dev")

        # Default to "other"
        if not categories:
            categories.append("other")

        return categories
