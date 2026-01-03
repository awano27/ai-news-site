"""
GitHub collector using REST API.

API Documentation: https://docs.github.com/en/rest/search
Rate Limit: 10 req/min (unauthenticated), 30 req/min (authenticated)

Optional: GITHUB_TOKEN environment variable for higher rate limits.
"""

import os
import logging
from datetime import date, timedelta
from typing import List, Dict, Optional

from .base import BaseCollector

logger = logging.getLogger(__name__)

# GitHub API endpoints
GITHUB_API_BASE = "https://api.github.com"
SEARCH_REPOS_URL = f"{GITHUB_API_BASE}/search/repositories"


class GitHubCollector(BaseCollector):
    """Collector for GitHub trending repositories."""

    # GitHub specific settings
    REQUEST_DELAY = 6.0  # Conservative for unauthenticated
    MAX_RESULTS = 30
    MIN_STARS = 10  # Minimum stars to consider

    # Topics that indicate productivity/AI tools
    RELEVANT_TOPICS = [
        "productivity", "automation", "ai", "llm", "gpt", "chatgpt",
        "developer-tools", "devtools", "cli", "workflow", "no-code",
        "note-taking", "knowledge-base", "meeting", "documentation"
    ]

    def __init__(self):
        super().__init__()
        self.token = os.environ.get("GITHUB_TOKEN", "")

        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
            self.REQUEST_DELAY = 2.0  # Faster with auth
        else:
            self.session.headers.update({
                "Accept": "application/vnd.github.v3+json"
            })

    @property
    def source_name(self) -> str:
        return "github"

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """
        Collect trending repositories from GitHub.

        Args:
            target_date: Date to search from (default: yesterday)

        Returns:
            List of tool dictionaries
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        logger.info(f"Collecting GitHub repositories created on/after {target_date}")

        tools = []

        try:
            # Search for recently created repos with good stars
            # Focus on topics relevant to productivity tools
            query = self._build_search_query(target_date)

            self._rate_limit()

            response = self.session.get(
                SEARCH_REPOS_URL,
                params={
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": self.MAX_RESULTS
                },
                timeout=30
            )

            # Handle rate limiting
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "0")
                if remaining == "0":
                    logger.warning("GitHub rate limit exceeded, skipping")
                    return []

            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            logger.info(f"Found {len(items)} repositories from GitHub")

            for i, repo in enumerate(items, 1):
                stars = repo.get("stargazers_count", 0)

                # Skip if below threshold
                if stars < self.MIN_STARS:
                    continue

                name = repo.get("name", "")
                description = repo.get("description", "") or ""
                url = repo.get("html_url", "")
                homepage = repo.get("homepage", "")
                topics = repo.get("topics", [])

                # Use homepage as official URL if available, otherwise GitHub URL
                official_url = homepage if homepage and homepage.startswith("http") else url

                # Generate tagline from description
                tagline = description[:200] if description else f"GitHub: {name}"

                # Categorize
                categories = self._categorize_from_repo(name, description, topics)

                tool = self.create_tool_dict(
                    name=self._format_name(name),
                    tagline=tagline,
                    official_url=official_url,
                    categories=categories,
                    source_rank=i,
                    source_votes=stars,
                    description=description,
                    topics=topics,
                    extra_links={"github": url}
                )

                tools.append(tool)

            logger.info(f"Collected {len(tools)} tools from GitHub")

        except Exception as e:
            logger.error(f"Error collecting from GitHub: {e}")

        return tools

    def _build_search_query(self, target_date: date) -> str:
        """Build GitHub search query."""
        # Created on or after target date, with minimum stars
        query_parts = [
            f"created:>={target_date.isoformat()}",
            f"stars:>={self.MIN_STARS}",
            "is:public"
        ]

        # Add topic filters (OR logic)
        # Note: GitHub search limits complexity, so we use a simpler approach
        # and filter by common productivity/AI keywords
        query_parts.append("(productivity OR automation OR ai OR llm OR devtools OR cli)")

        return " ".join(query_parts)

    def _format_name(self, name: str) -> str:
        """Format repository name for display."""
        # Replace hyphens/underscores with spaces, title case
        formatted = name.replace("-", " ").replace("_", " ")

        # Handle common patterns
        formatted = formatted.replace(" ai", " AI")
        formatted = formatted.replace(" llm", " LLM")
        formatted = formatted.replace(" gpt", " GPT")
        formatted = formatted.replace(" api", " API")
        formatted = formatted.replace(" cli", " CLI")

        # Title case
        return formatted.title()

    def _categorize_from_repo(self, name: str, description: str, topics: List[str]) -> List[str]:
        """Categorize based on repo metadata."""
        categories = []
        text = (name + " " + description + " " + " ".join(topics)).lower()

        # Category detection
        if any(kw in text for kw in ["meeting", "video", "transcri", "calendar", "zoom"]):
            categories.append("meeting")

        if any(kw in text for kw in ["doc", "note", "wiki", "markdown", "knowledge", "write"]):
            categories.append("docs")

        if any(kw in text for kw in ["project", "task", "kanban", "agile", "todo"]):
            categories.append("pm")

        if any(kw in text for kw in ["automat", "workflow", "n8n", "zapier", "pipelin"]):
            categories.append("automation")

        if any(kw in text for kw in ["ai", "gpt", "llm", "claude", "openai", "machine", "ml", "neural"]):
            categories.append("ai")

        # GitHub repos default to dev category
        categories.append("dev")

        # Dedupe and return
        return list(set(categories))
