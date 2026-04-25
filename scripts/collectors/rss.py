"""
RSS Feed collector for AI news sources.
Collects news from OpenAI, Google AI, Hugging Face, TechCrunch, The Verge, etc.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime

from .base import BaseCollector

logger = logging.getLogger(__name__)


# RSS Feed configurations
RSS_FEEDS = [
    {
        "name": "OpenAI",
        "url": "https://openai.com/news/rss.xml",
        "category": "AI Research",
        "priority": 1
    },
    {
        "name": "Google AI",
        "url": "https://blog.google/technology/ai/rss/",
        "category": "AI Research",
        "priority": 1
    },
    {
        "name": "Hugging Face",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "Open Source",
        "priority": 2
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "AI News",
        "priority": 2
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "AI News",
        "priority": 2
    },
    {
        "name": "Ars Technica AI",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "category": "Tech News",
        "priority": 3
    },
    {
        "name": "MIT Tech Review AI",
        "url": "https://www.technologyreview.com/feed/",
        "category": "AI Research",
        "priority": 2
    }
]


class RSSCollector(BaseCollector):
    """Collector for RSS feeds from major AI news sources."""

    REQUEST_DELAY = 0.5  # Faster for RSS feeds
    
    @property
    def source_name(self) -> str:
        return "rss"

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """
        Collect AI news from RSS feeds.
        
        Args:
            target_date: Date to filter news for (default: today)
            
        Returns:
            List of news items in normalized format
        """
        if target_date is None:
            target_date = date.today()
        
        all_items = []
        
        for feed_config in RSS_FEEDS:
            try:
                items = self._fetch_feed(feed_config, target_date)
                all_items.extend(items)
                logger.info(f"Collected {len(items)} items from {feed_config['name']}")
            except Exception as e:
                logger.warning(f"Failed to fetch {feed_config['name']}: {e}")
        
        # Sort by priority and timestamp
        all_items.sort(key=lambda x: (x.get("source_rank", 99), x.get("published_at", "")), reverse=True)
        
        logger.info(f"Total RSS items collected: {len(all_items)}")
        return all_items

    def _fetch_feed(self, feed_config: Dict, target_date: date) -> List[Dict]:
        """Fetch and parse a single RSS feed."""
        self._rate_limit()
        
        url = feed_config["url"]
        source_name = feed_config["name"]
        category = feed_config["category"]
        priority = feed_config["priority"]
        
        response = self.session.get(url, timeout=30, headers={
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        })
        response.raise_for_status()
        
        items = []
        
        try:
            root = ET.fromstring(response.content)
            
            # Handle both RSS 2.0 and Atom formats
            if root.tag == "rss":
                items = self._parse_rss(root, source_name, category, priority, target_date)
            elif root.tag == "{http://www.w3.org/2005/Atom}feed":
                items = self._parse_atom(root, source_name, category, priority, target_date)
            else:
                # Try RSS anyway
                items = self._parse_rss(root, source_name, category, priority, target_date)
                
        except ET.ParseError as e:
            logger.error(f"XML parse error for {source_name}: {e}")
        
        return items

    def _parse_rss(self, root: ET.Element, source_name: str, category: str, 
                   priority: int, target_date: date) -> List[Dict]:
        """Parse RSS 2.0 format."""
        items = []
        
        for item in root.findall(".//item"):
            try:
                title = self._get_text(item, "title")
                link = self._get_text(item, "link")
                description = self._get_text(item, "description")
                pub_date_str = self._get_text(item, "pubDate")
                
                if not title or not link:
                    continue
                
                # Parse date
                pub_date = self._parse_date(pub_date_str)
                
                # Filter by target date (include today and yesterday)
                if pub_date:
                    date_diff = (target_date - pub_date.date()).days
                    if date_diff < 0 or date_diff > 1:
                        continue
                
                # Get categories from feed
                feed_categories = [category]
                for cat_elem in item.findall("category"):
                    if cat_elem.text:
                        feed_categories.append(cat_elem.text)
                
                tool = self.create_tool_dict(
                    name=title[:200],
                    tagline=self._clean_html(description)[:300] if description else "",
                    official_url=link,
                    categories=feed_categories[:5],
                    source_rank=priority,
                    description=self._clean_html(description) if description else None
                )
                
                # Add RSS-specific fields
                tool["rss_source"] = source_name
                tool["published_at"] = pub_date.isoformat() if pub_date else None
                
                items.append(tool)
                
            except Exception as e:
                logger.debug(f"Error parsing RSS item: {e}")
        
        return items

    def _parse_atom(self, root: ET.Element, source_name: str, category: str,
                    priority: int, target_date: date) -> List[Dict]:
        """Parse Atom format."""
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = []
        
        for entry in root.findall("atom:entry", ns):
            try:
                title = self._get_text(entry, "atom:title", ns)
                
                # Get link - prefer alternate
                link = None
                for link_elem in entry.findall("atom:link", ns):
                    if link_elem.get("rel") in ("alternate", None):
                        link = link_elem.get("href")
                        break
                if not link:
                    link_elem = entry.find("atom:link", ns)
                    if link_elem is not None:
                        link = link_elem.get("href")
                
                summary = self._get_text(entry, "atom:summary", ns)
                content = self._get_text(entry, "atom:content", ns)
                updated = self._get_text(entry, "atom:updated", ns)
                published = self._get_text(entry, "atom:published", ns)
                
                if not title or not link:
                    continue
                
                # Parse date
                date_str = published or updated
                pub_date = self._parse_date(date_str)
                
                # Filter by target date
                if pub_date:
                    date_diff = (target_date - pub_date.date()).days
                    if date_diff < 0 or date_diff > 1:
                        continue
                
                description = summary or content or ""
                
                # Get categories
                feed_categories = [category]
                for cat_elem in entry.findall("atom:category", ns):
                    term = cat_elem.get("term")
                    if term:
                        feed_categories.append(term)
                
                tool = self.create_tool_dict(
                    name=title[:200],
                    tagline=self._clean_html(description)[:300],
                    official_url=link,
                    categories=feed_categories[:5],
                    source_rank=priority,
                    description=self._clean_html(description)
                )
                
                tool["rss_source"] = source_name
                tool["published_at"] = pub_date.isoformat() if pub_date else None
                
                items.append(tool)
                
            except Exception as e:
                logger.debug(f"Error parsing Atom entry: {e}")
        
        return items

    def _get_text(self, elem: ET.Element, path: str, ns: Dict = None) -> Optional[str]:
        """Get text content from an element."""
        if ns:
            child = elem.find(path, ns)
        else:
            child = elem.find(path)
        
        if child is not None and child.text:
            return child.text.strip()
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse various date formats from RSS feeds."""
        if not date_str:
            return None
        
        # Try RFC 2822 (common in RSS)
        try:
            return parsedate_to_datetime(date_str)
        except:
            pass
        
        # Try ISO 8601
        try:
            # Remove timezone suffix for parsing
            clean = date_str.replace("Z", "+00:00")
            if "+" not in clean and clean.endswith(":00"):
                clean = clean[:-3]  # Remove timezone if malformed
            return datetime.fromisoformat(clean.replace("Z", "+00:00"))
        except:
            pass
        
        # Try common formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        logger.debug(f"Could not parse date: {date_str}")
        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        # Remove CDATA wrapper
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up whitespace
        text = ' '.join(text.split())
        return text.strip()
