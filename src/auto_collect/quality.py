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


def validate_articles(articles: list[dict], *, min_articles: int = 1, min_sources: int = 1) -> dict:
    errors: list[str] = []
    japanese = 0
    sources: set[str] = set()
    if not articles:
        errors.append('no articles')
    for i, article in enumerate(articles, 1):
        if not isinstance(article, dict):
            errors.append(f'article {i}: invalid object')
            continue
        if not valid_article_url(article.get('url')):
            errors.append(f'article {i}: invalid URL')
        source = str(article.get('source_attribution') or article.get('rss_source') or article.get('source') or '').strip()
        if source:
            sources.add(source)
        else:
            errors.append(f'article {i}: missing source')
        if not str(article.get('title') or '').strip():
            errors.append(f'article {i}: missing title')
        if is_japanese_summary(article.get('summary')):
            japanese += 1
        else:
            errors.append(f'article {i}: Japanese summary missing or invalid')
        if article.get('processing_status') not in ('llm', 'source_japanese'):
            errors.append(f'article {i}: fallback or unverified processing')
    if len(articles) < min_articles:
        errors.append(f'below minimum article count: {len(articles)} < {min_articles}')
    if len(sources) < min_sources:
        errors.append(f'below minimum source coverage: {len(sources)} < {min_sources}')
    return {'status': 'failed' if errors else 'passed',
            'article_count': len(articles), 'japanese_count': japanese,
            'sources': sorted(sources), 'errors': errors}


TRANSIENT_ERRORS = {'network_error', 'http_429', 'http_500', 'http_502', 'http_503', 'http_504'}


def failure_reason(articles: list[dict], quality: dict) -> str:
    failed = [row for row in articles if row.get('processing_status') not in ('llm', 'source_japanese')]
    structural = any(any(token in error for token in ('URL', 'source', 'minimum', 'missing title', 'invalid object'))
                     for error in quality.get('errors', []))
    if failed and not structural and all(row.get('processing_error') in TRANSIENT_ERRORS for row in failed):
        return 'transient_generation_failed'
    return 'japanese_quality_failed'
