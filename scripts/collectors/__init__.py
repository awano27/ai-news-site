"""
Tool collectors for various sources.

Each collector implements a common interface:
- collect(date: Optional[date] = None) -> List[Dict]
- Returns list of tools in normalized format
"""

from .producthunt import ProductHuntCollector
from .hn import HackerNewsCollector
from .github import GitHubCollector

__all__ = ['ProductHuntCollector', 'HackerNewsCollector', 'GitHubCollector']
