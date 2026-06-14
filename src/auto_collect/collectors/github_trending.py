"""GitHub Trending AI/ML repos collector."""

import logging
import re
from datetime import date
from typing import List, Dict, Optional

from scripts.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# GitHub Trending page (no API needed, scrape HTML)
GITHUB_TRENDING_URL = "https://github.com/trending"
GITHUB_API_SEARCH = "https://api.github.com/search/repositories"

AI_TOPICS = [
    "machine-learning", "deep-learning", "artificial-intelligence",
    "llm", "large-language-models", "generative-ai", "transformers",
    "langchain", "rag", "agent", "diffusion", "computer-vision",
    "natural-language-processing", "reinforcement-learning",
]


class GitHubTrendingCollector(BaseCollector):
    """Collect trending AI/ML repos from GitHub."""

    REQUEST_DELAY = 1.0

    @property
    def source_name(self) -> str:
        return "github_trending"

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """Collect trending AI/ML repos via GitHub Search API."""
        if target_date is None:
            target_date = date.today()

        all_repos = []

        # Search for recently updated AI repos with high stars
        # Use 7-day window to catch trending repos
        from datetime import timedelta
        since_date = target_date - timedelta(days=7)
        queries = [
            "topic:llm stars:>50 pushed:>{since}",
            "topic:ai-agent stars:>30 pushed:>{since}",
            "topic:generative-ai stars:>50 pushed:>{since}",
            "topic:machine-learning stars:>100 pushed:>{since}",
            "(RAG OR retrieval-augmented) language:Python stars:>20 pushed:>{since}",
        ]

        since = since_date.strftime("%Y-%m-%d")

        for query_template in queries:
            query = query_template.format(since=since)
            try:
                self._rate_limit()
                resp = self.session.get(
                    GITHUB_API_SEARCH,
                    params={"q": query, "sort": "stars", "order": "desc", "per_page": 10},
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=15,
                )
                if resp.status_code == 403:
                    logger.warning("[GitHub] Rate limited, skipping remaining queries")
                    break
                resp.raise_for_status()
                data = resp.json()

                for repo in data.get("items", []):
                    repo_info = {
                        "name": repo["full_name"],
                        "tagline": repo.get("description", "")[:300],
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "language": repo.get("language", ""),
                        "topics": repo.get("topics", []),
                        "created_at": repo.get("created_at", ""),
                        "updated_at": repo.get("updated_at", ""),
                        "source": "github_trending",
                        "open_issues": repo.get("open_issues_count", 0),
                        "license": (repo.get("license") or {}).get("spdx_id", ""),
                    }
                    all_repos.append(repo_info)

            except Exception as e:
                logger.warning(f"[GitHub] Query failed: {e}")

        # Deduplicate by full_name
        seen = set()
        unique = []
        for repo in all_repos:
            if repo["name"] not in seen:
                seen.add(repo["name"])
                unique.append(repo)

        # Sort by stars
        unique.sort(key=lambda x: x["stars"], reverse=True)

        logger.info(f"[GitHub] Collected {len(unique)} trending AI repos")
        return unique[:20]
