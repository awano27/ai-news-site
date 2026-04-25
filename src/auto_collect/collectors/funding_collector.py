"""AI Funding / M&A news collector."""

import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime

import requests

logger = logging.getLogger(__name__)

# RSS feeds focused on AI funding/M&A
FUNDING_RSS_FEEDS = [
    {
        "name": "TechCrunch Venture",
        "url": "https://techcrunch.com/category/venture/feed/",
        "priority": 1,
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "priority": 2,
    },
]

AI_FUNDING_KEYWORDS = [
    "funding", "raised", "series a", "series b", "series c", "series d",
    "million", "billion", "valuation", "acquisition", "acquire", "merger",
    "ipo", "investment", "venture", "capital",
    "資金調達", "買収", "出資", "評価額", "上場",
    "ai", "artificial intelligence", "machine learning", "llm", "generative",
]


class FundingCollector:
    """Collect AI funding and M&A news."""

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """Collect AI funding/M&A news from RSS."""
        if target_date is None:
            target_date = date.today()

        all_items = []

        for feed in FUNDING_RSS_FEEDS:
            try:
                items = self._fetch_feed(feed, target_date)
                all_items.extend(items)
                logger.info(f"[Funding] {feed['name']}: {len(items)} articles")
            except Exception as e:
                logger.warning(f"[Funding] Failed {feed['name']}: {e}")

        logger.info(f"[Funding] Total: {len(all_items)} funding/M&A articles")
        return all_items

    def _fetch_feed(self, feed_config: Dict, target_date: date) -> List[Dict]:
        """Fetch and filter funding-related RSS items."""
        resp = requests.get(
            feed_config["url"],
            timeout=15,
            headers={
                "User-Agent": "AI-News-Bot/1.0",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
        )
        resp.raise_for_status()

        items = []
        try:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                date_el = item.find("pubDate")

                if title_el is None or link_el is None:
                    continue

                title = title_el.text or ""
                link = link_el.text or ""
                desc = (desc_el.text or "") if desc_el is not None else ""
                # Clean HTML from description
                desc = re.sub(r'<[^>]+>', '', desc).strip()

                # Date filter
                if date_el is not None and date_el.text:
                    try:
                        pub_date = parsedate_to_datetime(date_el.text)
                        diff = (target_date - pub_date.date()).days
                        if diff < 0 or diff > 1:
                            continue
                    except Exception:
                        pass

                # Filter for AI + funding keywords
                text_lower = (title + " " + desc).lower()
                has_ai = any(kw in text_lower for kw in [
                    "ai", "artificial intelligence", "machine learning",
                    "llm", "generative", "deep learning", "neural",
                ])
                has_funding = any(kw in text_lower for kw in [
                    "funding", "raised", "series", "million", "billion",
                    "valuation", "acquisition", "acquire", "merger", "ipo",
                    "investment", "資金調達", "買収",
                ])

                if has_ai and has_funding:
                    # Extract funding amount if present
                    amount = self._extract_amount(title + " " + desc)

                    items.append({
                        "name": title[:200],
                        "tagline": desc[:300],
                        "url": link,
                        "source": feed_config["name"],
                        "funding_amount": amount,
                        "category": "Business",
                    })

        except ET.ParseError as e:
            logger.warning(f"[Funding] XML parse error: {e}")

        return items

    def _extract_amount(self, text: str) -> Optional[str]:
        """Extract funding amount from text."""
        # Match patterns like "$100M", "$1.5 billion", "100億円"
        patterns = [
            r'\$(\d+(?:\.\d+)?)\s*(million|billion|M|B)',
            r'(\d+(?:\.\d+)?)\s*億円',
            r'\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(million|billion)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
