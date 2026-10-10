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


def article_errors(article: object, index: int) -> list[str]:
    """Per-article problems. Messages stay identical to validate_articles."""
    if not isinstance(article, dict):
        return [f'article {index}: invalid object']
    errors: list[str] = []
    if not valid_article_url(article.get('url')):
        errors.append(f'article {index}: invalid URL')
    if not _article_source(article):
        errors.append(f'article {index}: missing source')
    if not str(article.get('title') or '').strip():
        errors.append(f'article {index}: missing title')
    if not is_japanese_summary(article.get('summary')):
        errors.append(f'article {index}: Japanese summary missing or invalid')
    if article.get('processing_status') not in ('llm', 'source_japanese'):
        errors.append(f'article {index}: fallback or unverified processing')
    return errors


def _article_source(article: dict) -> str:
    return str(article.get('source_attribution') or article.get('rss_source') or article.get('source') or '').strip()


def validate_articles(articles: list[dict], *, min_articles: int = 1, min_sources: int = 1) -> dict:
    errors: list[str] = []
    japanese = 0
    sources: set[str] = set()
    if not articles:
        errors.append('no articles')
    for i, article in enumerate(articles, 1):
        errors.extend(article_errors(article, i))
        if isinstance(article, dict):
            source = _article_source(article)
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


def filter_publishable(articles, *, min_articles: int = 1, min_sources: int = 1,
                       max_excluded_ratio: float = MAX_EXCLUDED_RATIO) -> tuple[list[dict], dict]:
    """Drop per-article failures, then apply the whole-report gates to what remains."""
    kept: list[dict] = []
    excluded: list[dict] = []
    for index, article in enumerate(articles, 1):
        errors = article_errors(article, index)
        if errors:
            title = article.get('title') if isinstance(article, dict) else None
            url = article.get('url') if isinstance(article, dict) else None
            excluded.append({'index': index, 'title': title, 'url': url, 'errors': errors})
        else:
            kept.append(article)
    quality = validate_articles(kept, min_articles=min_articles, min_sources=min_sources)
    ratio = len(excluded) / len(articles) if articles else 1.0
    if ratio > max_excluded_ratio:
        quality['status'] = 'failed'
        quality['errors'].append(
            f'too many excluded articles: {len(excluded)}/{len(articles)} > {max_excluded_ratio:.0%}')
    quality.update({
        'input_count': len(articles),
        'excluded_count': len(excluded),
        'excluded_ratio': round(ratio, 3),
        'excluded': excluded,
    })
    return kept, quality


TRANSIENT_ERRORS = {'network_error', 'http_429', 'http_500', 'http_502', 'http_503', 'http_504', 'wait_budget_exhausted'}


def failure_reason(articles: list[dict], quality: dict) -> str:
    failed = [row for row in articles if row.get('processing_status') not in ('llm', 'source_japanese')]
    structural = any(any(token in error for token in ('URL', 'source', 'minimum', 'missing title', 'invalid object'))
                     for error in quality.get('errors', []))
    if failed and not structural and all(row.get('processing_error') in TRANSIENT_ERRORS for row in failed):
        return 'transient_generation_failed'
    return 'japanese_quality_failed'
