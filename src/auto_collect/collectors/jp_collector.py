"""Japanese AI news collector (ITmedia, GIGAZINE)."""

import logging
from datetime import date
from typing import List, Dict, Optional

from scripts.collectors.rss import RSSCollector
from ..config import JP_RSS_FEEDS, JP_AI_KEYWORDS

logger = logging.getLogger(__name__)


class JPCollector(RSSCollector):
    """Collector for Japanese AI news sources."""

    @property
    def source_name(self) -> str:
        return "jp_news"

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """Collect AI-related Japanese news."""
        if target_date is None:
            target_date = date.today()

        all_items = []

        for feed_config in JP_RSS_FEEDS:
            try:
                items = self._fetch_feed(feed_config, target_date)

                # Filter GIGAZINE by AI keywords
                if feed_config["name"] == "GIGAZINE":
                    items = [
                        item for item in items
                        if any(kw.lower() in (item.get("name", "") + " " + item.get("tagline", "")).lower()
                               for kw in JP_AI_KEYWORDS)
                    ]

                all_items.extend(items)
                logger.info(f"[JP] {feed_config['name']}: {len(items)} articles")
            except Exception as e:
                logger.warning(f"[JP] Failed {feed_config['name']}: {e}")

        logger.info(f"[JP] Total: {len(all_items)} articles")
        return all_items
