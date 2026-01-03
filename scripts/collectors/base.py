"""
Base collector class with common functionality.
"""

import time
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse
import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Base class for all collectors."""

    # Default rate limiting
    REQUEST_DELAY = 1.0  # seconds between requests
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2.0

    # User agent for requests
    USER_AGENT = "AI-News-Site-Bot/1.0 (https://awano27.github.io/ai-news-site/)"

    def __init__(self):
        self.session = self._create_session()
        self._last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json"
        })

        return session

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    @abstractmethod
    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """
        Collect tools from the source.

        Args:
            target_date: Date to collect for (default: today)

        Returns:
            List of tool dictionaries in normalized format
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the source identifier."""
        pass

    def normalize_url(self, url: str) -> str:
        """Normalize a URL for deduplication."""
        if not url:
            return ""

        parsed = urlparse(url)

        # Remove www. prefix
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Remove trailing slash
        path = parsed.path.rstrip("/")

        # Remove common tracking parameters
        # Keep only scheme, netloc, and path
        return f"{parsed.scheme}://{netloc}{path}"

    def generate_id(self, name: str) -> str:
        """Generate a slug ID from a name."""
        # Convert to lowercase
        slug = name.lower()

        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # Limit length
        if len(slug) > 50:
            slug = slug[:50].rstrip('-')

        return slug

    def create_tool_dict(
        self,
        name: str,
        tagline: str,
        official_url: str,
        categories: List[str],
        source_rank: Optional[int] = None,
        source_votes: Optional[int] = None,
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        extra_links: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Create a normalized tool dictionary."""
        tool_id = self.generate_id(name)
        today = date.today().isoformat()
        now = datetime.utcnow().isoformat() + "Z"

        links = {"official": self.normalize_url(official_url)}
        if extra_links:
            for key, url in extra_links.items():
                if url:
                    links[key] = self.normalize_url(url)

        tool = {
            "id": tool_id,
            "name": name,
            "tagline": tagline[:200] if tagline else "",
            "categories": categories,
            "links": links,
            "first_seen_at": today,
            "source": self.source_name,
            "published": False,
            "updated_at": now
        }

        if description:
            tool["description"] = description[:2000]

        if source_rank is not None:
            tool["source_rank"] = source_rank

        if source_votes is not None:
            tool["source_votes"] = source_votes

        if topics:
            tool["topics"] = topics[:20]  # Limit topics

        return tool
