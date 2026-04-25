"""arXiv collector — recent submissions in cs.AI / cs.CL / cs.LG.

Uses the public ATOM API (no auth, no rate-limit on small queries). Returns
articles in the same shape the rest of the pipeline expects, so they pass
through `LLMProcessor` unchanged.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Dict, List
from urllib.parse import urlencode

import feedparser

logger = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"
DEFAULT_CATEGORIES = ("cs.AI", "cs.CL", "cs.LG")


def _strip_arxiv_meta(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:600]


class ArxivCollector:
    """Collect arXiv preprints submitted in the last `lookback_hours`."""

    def __init__(self, categories=DEFAULT_CATEGORIES, max_results: int = 20, lookback_hours: int = 28):
        self.categories = categories
        self.max_results = max_results
        self.lookback_hours = lookback_hours

    def collect(self, target_date: date) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(hours=self.lookback_hours)
        cat_query = "+OR+".join(f"cat:{c}" for c in self.categories)
        params = {
            "search_query": cat_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(self.max_results),
        }
        url = f"{ARXIV_API}?{urlencode(params, safe='+:')}"
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.warning(f"[arXiv] parse failed: {e}")
            return []

        out: List[Dict] = []
        for entry in feed.entries:
            try:
                published = datetime(*entry.published_parsed[:6])
            except Exception:
                continue
            if published < cutoff:
                continue
            title = (entry.title or "").strip().replace("\n", " ")
            summary = _strip_arxiv_meta(getattr(entry, "summary", ""))
            authors = ", ".join(a.get("name", "") for a in entry.get("authors", [])[:3])
            primary_cat = ""
            if entry.get("arxiv_primary_category"):
                primary_cat = entry["arxiv_primary_category"].get("term", "")
            out.append({
                "name": title,
                "tagline": summary,
                "description": summary,
                "rss_source": f"arXiv ({primary_cat})" if primary_cat else "arXiv",
                "source": "arXiv",
                "links": {"official": entry.link},
                "source_rank": 2,
                "authors": authors,
            })
        logger.info(f"[arXiv] collected {len(out)} preprints across {self.categories}")
        return out
