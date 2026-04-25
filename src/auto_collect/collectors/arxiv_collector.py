"""arXiv collector — recent submissions in cs.AI / cs.CL / cs.LG.

Uses the public ATOM API (no auth, no rate-limit on small queries). Returns
articles in the same shape the rest of the pipeline expects, so they pass
through `LLMProcessor` unchanged.
"""

from __future__ import annotations

import logging
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from typing import Dict, List
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"
DEFAULT_CATEGORIES = ("cs.AI", "cs.CL", "cs.LG")
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _strip_arxiv_meta(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:600]


def _text(el, tag: str) -> str:
    node = el.find(tag, _NS)
    return (node.text or "").strip() if node is not None else ""


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
            req = urllib.request.Request(url, headers={"User-Agent": "ai-news-collector/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)
        except Exception as e:
            logger.warning(f"[arXiv] fetch/parse failed: {e}")
            return []

        out: List[Dict] = []
        for entry in root.findall("atom:entry", _NS):
            published_str = _text(entry, "atom:published")
            try:
                published = datetime.fromisoformat(published_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                continue
            if published < cutoff:
                continue
            title = _text(entry, "atom:title").replace("\n", " ")
            summary = _strip_arxiv_meta(_text(entry, "atom:summary"))
            authors = ", ".join(
                _text(a, "atom:name")
                for a in entry.findall("atom:author", _NS)[:3]
            )
            link_el = entry.find("atom:link[@rel='alternate']", _NS)
            if link_el is None:
                link_el = entry.find("atom:link", _NS)
            link = link_el.get("href", "") if link_el is not None else ""
            primary_cat_el = entry.find("arxiv:primary_category", _NS)
            primary_cat = primary_cat_el.get("term", "") if primary_cat_el is not None else ""
            out.append({
                "name": title,
                "tagline": summary,
                "description": summary,
                "rss_source": f"arXiv ({primary_cat})" if primary_cat else "arXiv",
                "source": "arXiv",
                "links": {"official": link},
                "source_rank": 2,
                "authors": authors,
            })
        logger.info(f"[arXiv] collected {len(out)} preprints across {self.categories}")
        return out
