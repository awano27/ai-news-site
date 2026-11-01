"""RSS Feed auto-collector for AI news."""

import logging
from datetime import date, timedelta
from typing import List, Dict, Optional

from scripts.collectors.rss import RSSCollector, RSS_FEEDS
from ..config import EN_RSS_FEEDS, DATE_LOOKBACK_HOURS

logger = logging.getLogger(__name__)


class RSSAutoCollector(RSSCollector):
    """Extended RSS collector with additional feeds for auto-collection."""

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """Collect from the English RSS feeds.

        JP_RSS_FEEDS are left to JPCollector: it applies the JP_AI_KEYWORDS
        filter to GIGAZINE, and an unfiltered copy fetched here would survive
        dedup and publish non-AI articles.
        """
        if target_date is None:
            target_date = date.today()

        all_items = []

        for feed_config in EN_RSS_FEEDS:
            try:
                items = self._fetch_feed(feed_config, target_date)
                all_items.extend(items)
                logger.info(f"[RSS] {feed_config['name']}: {len(items)} articles")
            except Exception as e:
                logger.warning(f"[RSS] Failed {feed_config['name']}: {e}")

        logger.info(f"[RSS] Total: {len(all_items)} articles")
        return all_items
