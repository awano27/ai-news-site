"""
Tool collectors for various sources.

Each collector implements a common interface:
- collect(date: Optional[date] = None) -> List[Dict]
- Returns list of tools in normalized format
"""

# Optional imports: some deployments (e.g. the cloud-fallback workflow)
# only ship a subset of the collectors. Missing modules must not break
# `from scripts.collectors.rss import RSSCollector` style sub-module imports.
__all__ = []

try:
    from .producthunt import ProductHuntCollector  # noqa: F401
    __all__.append('ProductHuntCollector')
except ImportError:
    pass

try:
    from .hn import HackerNewsCollector  # noqa: F401
    __all__.append('HackerNewsCollector')
except ImportError:
    pass

try:
    from .github import GitHubCollector  # noqa: F401
    __all__.append('GitHubCollector')
except ImportError:
    pass
