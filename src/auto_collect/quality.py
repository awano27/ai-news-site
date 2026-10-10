"""Conservative publication gates; heuristic fallbacks are never a full success."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

KANA = re.compile(r'[ぁ-ゖァ-ヺー]')
JAPANESE = re.compile(r'[ぁ-ゖァ-ヺー一-鿿]')


def is_japanese_summary(value: object) -> bool:
    if not isinstance(value, str):
        return False
    text = re.sub(r'https?://\S+', '', value).strip()
    visible = re.sub(r'[\W_\d]', '', text)
    # Kana prevents a Chinese-only response passing on shared Han characters;
    # the ratio rejects an English paragraph with a decorative Japanese suffix.
    return (len(text) >= 12 and len(KANA.findall(text)) >= 3
            and len(JAPANESE.findall(text)) >= max(8, len(visible) * 0.25))


def valid_article_url(value: object) -> bool:
    if not isinstance(value, str) or re.search(r'[\s\x00-\x1f\x7f\\]', value):
        return False
    try:
        parts = urlsplit(value)
        _ = parts.port
        return parts.scheme in ('http', 'https') and bool(parts.hostname) and not parts.username and not parts.password
    except ValueError:
        return False


def article_source(article: dict) -> str:
    return str(article.get('source_attribution') or article.get('rss_source') or article.get('source') or '').strip()


def article_errors(article) -> list[str]:
    """Per-article problems. Empty means the article may be published."""
    if not isinstance(article, dict):
        return ['invalid object']
    errors: list[str] = []
    if not valid_article_url(article.get('url')):
        errors.append('invalid URL')
    if not article_source(article):
        errors.append('missing source')
    if not str(article.get('title') or '').strip():
        errors.append('missing title')
    if not is_japanese_summary(article.get('summary')):
        errors.append('Japanese summary missing or invalid')
    if article.get('processing_status') not in ('llm', 'source_japanese'):
        errors.append('fallback or unverified processing')
    return errors


def validate_articles(articles: list[dict], *, min_articles: int = 1, min_sources: int = 1) -> dict:
    errors: list[str] = []
    japanese = 0
    sources: set[str] = set()
    if not articles:
        errors.append('no articles')
    for i, article in enumerate(articles, 1):
        for err in article_errors(article):
            errors.append(f'article {i}: {err}')
        if isinstance(article, dict):
            source = article_source(article)
            if source:
                sources.add(source)
            if is_japanese_summary(article.get('summary')):
                japanese += 1
    if len(articles) < min_articles:
        errors.append(f'below minimum article count: {len(articles)} < {min_articles}')
    if len(sources) < min_sources:
        errors.append(f'below minimum source coverage: {len(sources)} < {min_sources}')
    return {'status': 'failed' if errors else 'passed',
            'article_count': len(articles), 'japanese_count': japanese,
            'sources': sorted(sources), 'errors': errors}


MAX_EXCLUDED_RATIO = 0.20


def filter_publishable(articles: list, *, min_articles: int = 1, min_sources: int = 1,
                       max_excluded_ratio: float = MAX_EXCLUDED_RATIO) -> tuple[list, dict]:
    """Drop unverified articles, then apply the day-level gate to what remains.

    A few bad summaries no longer fail the day. The day still fails when the
    kept set misses the article or source minimum, or when exclusions exceed
    max_excluded_ratio (the boundary itself is still publishable).
    """
    kept: list = []
    excluded: list[dict] = []
    total = len(articles)
    for index, article in enumerate(articles, 1):
        errs = article_errors(article)
        if errs:
            excluded.append({
                'index': index,
                'title': article.get('title') if isinstance(article, dict) else None,
                'url': article.get('url') if isinstance(article, dict) else None,
                'errors': errs,
            })
        else:
            kept.append(article)
    quality = validate_articles(kept, min_articles=min_articles, min_sources=min_sources)
    ratio = (len(excluded) / total) if total else 1.0
    if ratio > max_excluded_ratio:
        quality['status'] = 'failed'
        quality['errors'].append(
            f'too many excluded articles: {len(excluded)}/{total} > {max_excluded_ratio:.0%}')
    quality.update({
        'input_count': total,
        'excluded_count': len(excluded),
        'excluded_ratio': round(ratio, 3),
        'excluded': excluded,
    })
    return kept, quality


TRANSIENT_ERRORS = {
    'network_error', 'http_429', 'http_500', 'http_502', 'http_503', 'http_504',
    'wait_budget_exceeded',
}
_HARD_TOKENS = ('URL', 'missing title', 'invalid object', 'missing source')


def failure_reason(articles: list[dict], quality: dict) -> str:
    failed = [row for row in articles if isinstance(row, dict) and row.get('processing_status') not in ('llm', 'source_japanese')]
    blobs = list(quality.get('errors') or [])
    for row in quality.get('excluded') or []:
        blobs.extend(row.get('errors') or [])
    structural = any(any(token in error for token in _HARD_TOKENS) for error in blobs)
    # Minimum-count failures on a filtered day are the result of dropping
    # articles. They stay retryable when every drop was a transient provider error.
    if not quality.get('excluded_count'):
        structural = structural or any('minimum' in error for error in quality.get('errors') or [])
    if failed and not structural and all(row.get('processing_error') in TRANSIENT_ERRORS for row in failed):
        return 'transient_generation_failed'
    return 'japanese_quality_failed'
