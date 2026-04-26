"""URL canonicalisation + fuzzy title clustering for collected articles.

Replaces the naive URL-exact-match dedup in `main.py`. Two articles are
treated as the same story if either:
  * canonical URLs match, or
  * normalised titles have SequenceMatcher ratio >= TITLE_THRESHOLD
    (or >= SAME_DOMAIN_THRESHOLD when both come from the same domain).

The article with the highest pre-existing score (or most informative
content if none have a score yet) survives; others are discarded but
their sources are merged into a `merged_from` list so the LLM step can
optionally use the extra context.

`dedup_across_sections` runs AFTER the LLM rewrite/section-split step
to catch:
  * the same story published by multiple outlets (entity-Jaccard match)
  * HuggingFace base model + community quantizations (Qwen/X + foo/X-GGUF)
  * cross-section URL leakage (Bloomberg -> headlines + funding).
"""

from __future__ import annotations

import difflib
import re
from typing import Dict, List, Tuple, Optional, Set
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

TITLE_THRESHOLD = 0.85
SAME_DOMAIN_THRESHOLD = 0.78
ENTITY_JACCARD_THRESHOLD = 0.45
ENTITY_MIN_SHARED = 2
CROSS_SECTION_TITLE_THRESHOLD = 0.78

_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "referrer", "ref_src",
    "igshid", "spm", "from", "_hsenc", "_hsmi",
}

_PROPER_NOUN_RE = re.compile(
    r"[A-Za-z][A-Za-z0-9]{2,}"  # English/alphanumeric tokens (>=3 chars)
    r"|[一-鿿]{2,}"      # Kanji runs (>=2 chars)
    r"|[゠-ヿー]{3,}"  # Katakana runs (>=3 chars)
)

_STOP_TOKENS = {
    # Common Japanese filler that appears in many headlines
    "について", "ました", "という", "として", "こと", "ため", "もの",
    "発表", "公開", "リリース", "ニュース", "提供", "登場", "新しい",
    "向け", "場合", "可能", "可能性", "対応", "対応中",
    # Generic English / brand-agnostic tech jargon
    "the", "and", "for", "from", "with", "that", "this", "into", "what",
    "ai", "llm", "api", "open", "model", "data",
}

_HF_QUANT_SUFFIX_RE = re.compile(
    r"[-._](GGUF|AWQ|GPTQ|EXL2|MLX|FP16|FP8|INT8|INT4|GPTQ-Int[48]|bnb[-_]?\w*)"
    r"(?:[-._]\S*)?$",
    re.IGNORECASE,
)


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


def _domain_of(url: str) -> str:
    if not url:
        return ""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return ""
    return host[4:] if host.startswith("www.") else host


def _content_tokens(title: str) -> Set[str]:
    if not title:
        return set()
    tokens = {tok.lower() for tok in _PROPER_NOUN_RE.findall(title)}
    return {t for t in tokens if t not in _STOP_TOKENS and not t.isdigit()}


def _entity_jaccard(a: str, b: str) -> Tuple[float, int]:
    """Return (jaccard, shared_count) over content tokens of two titles."""
    ta, tb = _content_tokens(a), _content_tokens(b)
    if not ta or not tb:
        return (0.0, 0)
    inter = ta & tb
    if not inter:
        return (0.0, 0)
    return (len(inter) / len(ta | tb), len(inter))


def huggingface_model_key(url: str) -> str:
    """Collapse HuggingFace base model + community quantizations into one key.

    Examples:
        Qwen/Qwen3.6-35B-A3B           -> qwen3.6-35b-a3b
        unsloth/Qwen3.6-35B-A3B-GGUF   -> qwen3.6-35b-a3b
        bartowski/Qwen3.6-35B-A3B-AWQ  -> qwen3.6-35b-a3b
        Qwen/Qwen3.6-35B-A3B-Instruct  -> qwen3.6-35b-a3b-instruct  (kept distinct)
    """
    if not url or "huggingface.co/" not in url:
        return ""
    try:
        path = urlparse(url).path.strip("/")
    except Exception:
        return ""
    parts = path.split("/")
    if len(parts) < 2:
        return ""
    repo = parts[1]
    repo = _HF_QUANT_SUFFIX_RE.sub("", repo)
    return repo.lower()


def deduplicate(
    articles: List[Dict],
    title_threshold: float = TITLE_THRESHOLD,
    same_domain_threshold: float = SAME_DOMAIN_THRESHOLD,
) -> List[Dict]:
    """Return articles with duplicates collapsed.

    Order of input is preserved among survivors (the kept article keeps the
    position of the first one encountered in its cluster). `merged_from` on
    each survivor lists the sources of the duplicates that were dropped.

    Title fuzzy match uses `same_domain_threshold` (default 0.78) when the
    two articles share a hostname, and `title_threshold` (default 0.85)
    otherwise. The relaxed same-domain threshold catches feed-burst
    duplicates where one outlet republishes the same story with a slightly
    edited headline.
    """
    if not articles:
        return []

    seen_urls: Dict[str, int] = {}      # canonical url -> index in `survivors`
    survivors: List[Dict] = []

    for article in articles:
        a_url = article.get("links", {}).get("official", "") or article.get("url", "")
        canon = canonical_url(a_url)
        a_domain = _domain_of(a_url)
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
                    s_url = s.get("links", {}).get("official", "") or s.get("url", "")
                    threshold = (
                        same_domain_threshold
                        if a_domain and a_domain == _domain_of(s_url)
                        else title_threshold
                    )
                    if difflib.SequenceMatcher(None, title_norm, s_norm).ratio() >= threshold:
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


def dedup_across_sections(
    *,
    headlines: Optional[List[Dict]] = None,
    funding: Optional[List[Dict]] = None,
    models: Optional[List[Dict]] = None,
    github: Optional[List[Dict]] = None,
) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    """Post-LLM cross-section dedup. Section priority: headlines > funding > models > github.

    Catches three cases the in-section dedup cannot:
      1. Canonical-URL match across sections (Bloomberg story landing in
         both `headlines` and `funding`).
      2. Same story published by different outlets — entity-token Jaccard
         >= 0.45 with at least 2 shared content tokens.
      3. HuggingFace base model + community quantizations
         (Qwen/Qwen3-X + unsloth/Qwen3-X-GGUF -> drop the latter).

    Returns the four lists in the same order: (headlines, funding, models, github).
    Order within each section is preserved.
    """
    sections = [
        ("headlines", headlines or []),
        ("funding", funding or []),
        ("models", models or []),
        ("github", github or []),
    ]

    # Title-fuzzy and entity-Jaccard only apply to journalistic sections —
    # `models` (HuggingFace) and `github` use machine-generated titles like
    # "Qwen/Qwen3.6-27B" or "f/prompts.chat" where token overlap with a
    # related model (e.g. Qwen 35B) creates false positives. They are
    # deduped purely via canonical URL + HF base-model key.
    TITLE_DEDUP_SECTIONS = {"headlines", "funding"}

    seen_urls: Dict[str, str] = {}      # canonical_url -> section name where kept
    seen_hf: Dict[str, str] = {}        # hf_model_key -> section name
    kept_titles: List[str] = []         # titles from headlines/funding only

    out: Dict[str, List[Dict]] = {name: [] for name, _ in sections}

    for sec_name, items in sections:
        title_dedup_active = sec_name in TITLE_DEDUP_SECTIONS
        for item in items:
            if not item:
                continue
            url = item.get("url", "") or ""
            cu = canonical_url(url)
            hk = huggingface_model_key(url)
            title = item.get("title") or item.get("name") or ""

            # Layer A: canonical URL across sections
            if cu and cu in seen_urls:
                continue

            # Layer B: HuggingFace base/quant collapse
            if hk and hk in seen_hf:
                continue

            # Layer C: cross-section title fuzzy + entity-Jaccard.
            # Only runs for journalistic sections — both the candidate and
            # the kept-title pool are restricted to headlines/funding.
            drop = False
            if title_dedup_active and title:
                tnorm = _norm_title(title)
                t_tokens = _content_tokens(title)
                for prev_title in kept_titles:
                    pn = _norm_title(prev_title)
                    if pn and tnorm and difflib.SequenceMatcher(
                        None, tnorm, pn
                    ).ratio() >= CROSS_SECTION_TITLE_THRESHOLD:
                        drop = True
                        break
                    if t_tokens:
                        ratio, shared = _entity_jaccard(title, prev_title)
                        if shared >= ENTITY_MIN_SHARED and ratio >= ENTITY_JACCARD_THRESHOLD:
                            drop = True
                            break
            if drop:
                continue

            out[sec_name].append(item)
            if cu:
                seen_urls[cu] = sec_name
            if hk:
                seen_hf[hk] = sec_name
            if title_dedup_active and title:
                kept_titles.append(title)

    return out["headlines"], out["funding"], out["models"], out["github"]
