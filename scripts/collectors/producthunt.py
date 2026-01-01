"""
Product Hunt collector using GraphQL API v2.

API Documentation: https://api.producthunt.com/v2/docs
Rate Limit: 200 requests/day (free tier)

Requires PH_TOKEN environment variable (API Bearer token).
"""

import os
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional

from .base import BaseCollector

logger = logging.getLogger(__name__)

# GraphQL endpoint
GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"

# Query to get posts
POSTS_QUERY = """
query GetPosts($first: Int!, $postedAfter: DateTime, $postedBefore: DateTime) {
  posts(first: $first, postedAfter: $postedAfter, postedBefore: $postedBefore, order: VOTES) {
    edges {
      node {
        id
        name
        tagline
        description
        url
        website
        votesCount
        commentsCount
        topics {
          edges {
            node {
              name
              slug
            }
          }
        }
        createdAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


class ProductHuntCollector(BaseCollector):
    """Collector for Product Hunt using GraphQL API."""

    # Product Hunt specific settings
    REQUEST_DELAY = 2.0  # Be more conservative with PH
    MAX_POSTS_PER_DAY = 50  # Limit posts to fetch

    def __init__(self):
        super().__init__()
        self.token = os.environ.get("PH_TOKEN", "")

        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })

    @property
    def source_name(self) -> str:
        return "producthunt"

    def _is_configured(self) -> bool:
        """Check if API token is available."""
        return bool(self.token)

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """
        Collect tools from Product Hunt.

        Args:
            target_date: Date to collect for (default: yesterday, to ensure full day data)

        Returns:
            List of tool dictionaries
        """
        if not self._is_configured():
            logger.warning("PH_TOKEN not set, skipping Product Hunt collection")
            return []

        # Default to yesterday for complete data
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        # Build date range (full day in UTC)
        posted_after = datetime.combine(target_date, datetime.min.time())
        posted_before = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

        logger.info(f"Collecting Product Hunt posts for {target_date}")

        tools = []

        try:
            self._rate_limit()

            response = self.session.post(
                GRAPHQL_URL,
                json={
                    "query": POSTS_QUERY,
                    "variables": {
                        "first": self.MAX_POSTS_PER_DAY,
                        "postedAfter": posted_after.isoformat() + "Z",
                        "postedBefore": posted_before.isoformat() + "Z"
                    }
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []

            posts = data.get("data", {}).get("posts", {}).get("edges", [])
            logger.info(f"Found {len(posts)} posts from Product Hunt")

            for i, edge in enumerate(posts, 1):
                node = edge.get("node", {})

                # Extract topics
                topics = []
                for topic_edge in node.get("topics", {}).get("edges", []):
                    topic_name = topic_edge.get("node", {}).get("name", "")
                    if topic_name:
                        topics.append(topic_name)

                # Determine categories based on topics
                categories = self._categorize_from_topics(topics)
                categories.append("ph")  # All PH tools get "ph" category

                # Get official website or fall back to PH URL
                official_url = node.get("website") or node.get("url", "")
                ph_url = node.get("url", "")

                tool = self.create_tool_dict(
                    name=node.get("name", ""),
                    tagline=node.get("tagline", ""),
                    official_url=official_url,
                    categories=list(set(categories)),  # Dedupe categories
                    source_rank=i,
                    source_votes=node.get("votesCount", 0),
                    description=node.get("description", ""),
                    topics=topics,
                    extra_links={"producthunt": ph_url}
                )

                tools.append(tool)

        except Exception as e:
            logger.error(f"Error collecting from Product Hunt: {e}")

        return tools

    def _categorize_from_topics(self, topics: List[str]) -> List[str]:
        """Map Product Hunt topics to our categories."""
        categories = []
        topics_lower = [t.lower() for t in topics]

        # Category mapping rules
        mapping = {
            "meeting": ["meeting", "video conferencing", "calendar", "scheduling",
                       "transcription", "note-taking"],
            "docs": ["documents", "writing", "notes", "knowledge base", "wiki",
                    "documentation", "notion", "editor"],
            "pm": ["project management", "task management", "productivity",
                  "team collaboration", "kanban", "agile"],
            "automation": ["automation", "workflow", "integrations", "zapier",
                          "no-code", "low-code", "bots"],
            "ai": ["artificial intelligence", "machine learning", "gpt", "chatgpt",
                  "ai assistant", "generative ai", "llm", "openai", "claude"],
            "dev": ["developer tools", "programming", "github", "api", "devops",
                   "code", "software engineering", "ide", "debugging"]
        }

        for category, keywords in mapping.items():
            for keyword in keywords:
                if any(keyword in t for t in topics_lower):
                    categories.append(category)
                    break

        # Default to "other" if no match
        if not categories:
            categories.append("other")

        return categories
