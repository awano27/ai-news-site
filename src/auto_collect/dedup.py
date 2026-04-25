"""URL canonicalisation + fuzzy title clustering for collected articles.

Replaces the naive URL-exact-match dedup in `main.py`. Two articles are
treated as the same story if either:
  * canonical URLs match, or
  * normalised titles have SequenceMatcher ratio >= TITLE_THRESHOLD.

The article with the highest pre-existing score (or most informative
content if none have a score yet) survives; others are discarded but
their sources are merged into a `merged_from` list so the LLM step can
optionally use the extra context.
"""

from __future__ import annotations

import difflib
import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

TITLE_THRESHOLD = 0.85

_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "referrer", "ref_src",
    "igshid", "spm", "from", "_hsenc", "_hsmi",
}


def canonical_url(url: str) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
    except Exception:
        return url.strip().lower()
    if not p.scheme:
        return url.strip().lower()
    netloc = p.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = p.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    query = "&".join(
        f"{k}={v}"
        for k, v in parse_qsl(p.query, keep_blank_values=False)
        if k.lower() not in _TRACKING_PARAMS
    )
    return urlunparse((p.scheme.lower(), netloc, path, "", query, ""))


def _norm_title(t: str) -> str:
    t = (t or "").lower()
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[\W_]+", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def _score_for_priority(article: Dict) -> Tuple[int, int, int]:
    """Sort key that picks the best representative within a cluster."""
    score = int(article.get("score", 0) or 0)
    src_rank = -int(article.get("source_rank", 99) or 99)  # smaller = better
    desc_len = len(article.get("description", "") or article.get("tagline", "") or "")
    return (score, src_rank, desc_len)


def deduplicate(articles: List[Dict], title_threshold: float = TITLE_THRESHOLD) -> List[Dict]:
    """Return articles with duplicates collapsed.

    Order of input is preserved among survivors (the kept article keeps the
    position of the first one encountered in its cluster). `merged_from` on
    each survivor lists the sources of the duplicates that were dropped.
    """
    if not articles:
        return []

    seen_urls: Dict[str, int] = {}      # canonical url -> index in `survivors`
    survivors: List[Dict] = []

    for article in articles:
        canon = canonical_url(article.get("links", {}).get("official", ""))
        idx = None

        if canon and canon in seen_urls:
            idx = seen_urls[canon]
        else:
            # Title fuzzy match against existing survivors
            title_norm = _norm_title(article.get("name", ""))
            if title_norm:
                for i, s in enumerate(survivors):
                    s_norm = _norm_title(s.get("name", ""))
                    if not s_norm:
                        continue
                    if difflib.SequenceMatcher(None, title_norm, s_norm).ratio() >= title_threshold:
                        idx = i
                        break

        if idx is None:
            new_idx = len(survivors)
            survivors.append(dict(article))
            if canon:
                seen_urls[canon] = new_idx
            continue

        # Merge into existing survivor; pick the better representative.
        existing = survivors[idx]
        better = max(existing, article, key=_score_for_priority)
        loser = existing if better is article else article
        merged_sources = better.get("merged_from", [])[:]
        loser_src = loser.get("rss_source") or loser.get("source") or ""
        if loser_src and loser_src not in merged_sources:
            merged_sources.append(loser_src)
        new_record = dict(better)
        new_record["merged_from"] = merged_sources
        survivors[idx] = new_record
        if canon:
            seen_urls[canon] = idx

    return survivors
