#!/usr/bin/env python3
"""Verify linked daily outputs locally or over HTTP; never infer freshness from date alone.

Without --require-quality this is a structural legacy-compatible check, not a
certification of Japanese processing or provider availability. Slides have their
own publication cadence and are deliberately not required to share the news date.
"""
from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_search_index import canonical_url as external_url, normalize_daily_payload, _daily_rows
from src.auto_collect.quality import is_japanese_summary


class PublicationError(ValueError):
    pass


def canonical_url(value):
    return external_url(value) or str(value or '').strip()


class Page(HTMLParser):
    """Capture rendered text and source links within real cards, not script data."""
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.links = set()
        self.elements = {}
        self.stack = []
        self.nodes = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = (any(node['hidden'] for node in self.stack)
                  or tag in {'script', 'style', 'template'}
                  or 'hidden' in attrs or attrs.get('aria-hidden') == 'true'
                  or bool(re.search(r'display\s*:\s*none', attrs.get('style', ''), re.I)))
        node = {'tag': tag, 'id': attrs.get('id'), 'classes': set(attrs.get('class', '').split()),
                'hidden': hidden, 'text': '', 'links': set(), 'descendants': []}
        self.nodes.append(node)
        for ancestor in self.stack:
            ancestor['descendants'].append(node)
        if tag == 'meta':
            self.meta[attrs.get('name')] = attrs.get('content')
        if tag == 'a' and attrs.get('href') and not hidden:
            url = canonical_url(attrs['href'])
            self.links.add(url)
            node['links'].add(url)
            for ancestor in self.stack:
                ancestor['links'].add(url)
        if tag not in {'meta', 'link', 'br', 'img', 'input', 'hr', 'source', 'wbr', 'area', 'base', 'embed', 'param', 'track', 'col'}:
            self.stack.append(node)
        if attrs.get('id'):
            self.elements.setdefault(attrs['id'], '')

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]['tag'] == tag:
                del self.stack[index:]
                return

    def handle_data(self, text):
        if any(node['hidden'] for node in self.stack):
            return
        for node in self.stack:
            node['text'] += text
            if node['id']:
                self.elements[node['id']] += text


def plain(value):
    return ' '.join(str(value or '').split())


def validate_rendered(page, items, daily, section='headlines'):
    container = 'card' if daily else {'github': 'gh', 'models': 'mdl'}.get(section, 'row')
    title_class = 'card-title' if daily else ('gh-name' if section in {'github', 'models'} else 'row-title')
    for item in items:
        if daily and item.get('type') == 'x':
            continue
        url = canonical_url(item.get('url'))
        candidates = [node for node in page.nodes if container in node['classes'] and not node['hidden'] and url in node['links']]
        expected_title = plain(item.get('title'))
        expected_summary = plain(item.get('summary') or item.get('tldr'))
        if daily and len(expected_summary) > 240:
            expected_summary = expected_summary[:239] + '…'
        summary_class = 'card-body' if daily else {'github': 'gh-desc', 'models': 'mdl-summary'}.get(section, 'd-summary' if item.get('summary') else 'row-tldr')
        def has_field(node, class_name, expected):
            return any(class_name in child['classes'] and not child['hidden'] and plain(child['text']) == expected for child in node['descendants'])
        require(any(has_field(node, title_class, expected_title) and has_field(node, summary_class, expected_summary) for node in candidates),
                f"{'daily' if daily else 'report'} HTML rendered title/summary differs from the source-linked JSON item")


class Source:
    def __init__(self, root=None, base_url=None):
        self.root = Path(root) if root is not None else None
        self.base_url = base_url.rstrip('/') if base_url else None

    def read(self, relative):
        try:
            if self.base_url:
                request = Request(self.base_url + '/' + relative.lstrip('/'), headers={'Cache-Control': 'no-cache', 'User-Agent': 'VisionHub-publication-check/1.0'})
                with urlopen(request, timeout=20) as response:
                    return response.read()
            return (self.root / relative).read_bytes()
        except (OSError, UnicodeError) as error:
            raise PublicationError(f'{relative}: could not read publication ({type(error).__name__})') from error

    def text(self, relative):
        try:
            return self.read(relative).decode('utf-8')
        except UnicodeError as error:
            raise PublicationError(f'{relative}: invalid UTF-8 text') from error

    def json(self, relative):
        try:
            return json.loads(self.text(relative))
        except json.JSONDecodeError as error:
            raise PublicationError(f'{relative}: invalid JSON') from error


def require(condition, message):
    if not condition:
        raise PublicationError(message)


def rows_by_url(items):
    require(isinstance(items, list), 'items must be an array')
    rows = {}
    for item in items:
        require(isinstance(item, dict), 'item must be an object')
        url = canonical_url(item.get('url', ''))
        require(bool(url), 'item URL is missing')
        rows[url] = item
    return rows


def is_japanese(text):
    return bool(re.search(r'[\u3040-\u30ff\u3400-\u9fff]', str(text)))


def narrative_title(item):
    source = str(item.get('source', '')).lower()
    return not ('github' in source or 'huggingface' in source or 'hugging face' in source)


def validate_quality(daily):
    quality = daily.get('quality') or {}
    require(quality.get('status') == 'passed', 'quality.status must be passed; legacy/missing or degraded quality is not fresh')
    require(bool(quality.get('provider')) and bool(quality.get('model')), 'quality provider/model provenance is missing')
    articles = [item for item in daily['items'] if item.get('type') != 'x']
    require(quality.get('article_count') == len(articles), 'quality.article_count does not match daily news items')
    require(quality.get('japanese_count') == len(articles), 'quality.japanese_count does not match daily news items')
    require(sorted(quality.get('sources') or []) == sorted({str(item.get('source', '')).strip() for item in articles}), 'quality.sources does not match daily source provenance')
    for item in articles:
        require(item.get('processing_status') in {'llm', 'source_japanese'}, 'quality processing_status must be llm or source_japanese')
        require(is_japanese_summary(item.get('summary')), 'Japanese daily summary missing')
        if narrative_title(item):
            require(is_japanese(item.get('title')), 'Japanese daily headline missing')
    # excluded_item_count is the normalizer's drop count (invalid URL, title,
    # type, or date) and must stay 0. Quality-gate omissions are a different
    # record: quality.excluded. They are not copied into excluded_item_count,
    # and a listed exclusion that is still present in items fails here.
    excluded_rows = quality.get('excluded') or []
    require(isinstance(excluded_rows, list), 'quality.excluded must be a list when present')
    require(quality.get('excluded_count', len(excluded_rows)) == len(excluded_rows), 'quality.excluded_count does not match excluded entries')
    published = {canonical_url(item.get('url')) for item in articles}
    for row in excluded_rows:
        require(isinstance(row, dict), 'quality.excluded entries must be objects')
        reasons = row.get('errors')
        require(isinstance(reasons, list) and any(isinstance(reason, str) and reason.strip() for reason in reasons), 'excluded article is missing a reason')
        url = canonical_url(row.get('url') or '')
        if url:
            require(url not in published, 'excluded article was still published')


def signature(items):
    require(isinstance(items, list) and all(isinstance(row, dict) for row in items), 'report/API items must be objects')
    return sorted(json.dumps(dict(row, url=canonical_url(row.get('url', ''))), sort_keys=True, ensure_ascii=False) for row in items)


def report_sections(report):
    sections = {name: report.get(name, []) for name in ('headlines', 'funding', 'github', 'models')}
    require(all(isinstance(rows, list) and all(isinstance(row, dict) for row in rows) for rows in sections.values()), 'report sections must be arrays of item objects')
    return sections


def verify(source, expected_date, require_quality=False, expected=None, check_urls=False):
    daily = source.json('daily-news/data.json')
    report = source.json('presentations/auto_daily_report.json')
    api = source.json('public-pages/api/auto_daily_report/latest.json')
    snapshot = source.json(f'public-pages/news/daily/{expected_date}.json')
    search = source.json('public-pages/news/search_index.json')
    for label, data in [('daily', daily), ('report', report), ('report API', api), ('daily snapshot', snapshot)]:
        require(isinstance(data, dict) and data.get('date') == expected_date, f'{label} date does not match {expected_date}')
    items = daily.get('items')
    normalized_daily = normalize_daily_payload(daily)
    daily_rows = rows_by_url(normalized_daily['items'])
    require(items and daily.get('total') == len(items), 'daily total does not match nonempty items')
    snapshot_rows = rows_by_url(snapshot.get('items'))
    require(snapshot.get('total') == len(snapshot_rows), 'daily snapshot total does not match items')
    require(set(snapshot_rows) == set(daily_rows), 'daily snapshot URL coverage does not match daily items')
    require(all(item.get('date') == expected_date for item in snapshot_rows.values()), 'daily snapshot item date mismatch')
    require(isinstance(search, list), 'search index must be an array')
    search_rows = rows_by_url([row for row in search if row.get('date') == expected_date and row.get('type') != 'slide'])
    require(set(daily_rows) <= set(search_rows), 'search index missing current-date daily URLs')
    for url, item in daily_rows.items():
        require(item.get('title') == snapshot_rows[url].get('title'), 'daily snapshot title mismatch')
        require(item.get('title') == search_rows[url].get('title'), 'search index current-date title mismatch')
    sections = report_sections(report)
    api_sections = report_sections(api)
    headlines = sections['headlines']
    report_items = [item for rows in sections.values() for item in rows]
    require(bool(headlines), 'report headlines are empty')
    require(report.get('total') == len(report_items), 'report total does not match all section counts')
    for name in sections:
        require(signature(sections[name]) == signature(api_sections[name]), f'report API {name} differ from report')
    require(report.get('total') == api.get('total'), 'report API total differs from report')
    if require_quality:
        require(normalized_daily.get('excluded_item_count', 0) == 0, 'strict publication has excluded unsafe or invalid daily items')
        validate_quality(daily)
        require(snapshot.get('schema_version') == 1, 'strict daily snapshot schema is missing')
        require(normalize_daily_payload(snapshot) == normalized_daily, 'daily snapshot metadata/content differs from normalized daily publication')
        fields = ('date', 'title', 'url', 'type', 'category', 'source', 'published_at', 'summary', 'capture_schema')
        for projected in _daily_rows(normalized_daily):
            url = canonical_url(projected['url'])
            matches = [row for row in search if row.get('date') == expected_date and row.get('type') != 'slide' and canonical_url(row.get('url')) == url]
            require(matches and all({key: row[key] for key in fields if key in row} == projected for row in matches),
                    'search index managed current-date metadata/content differs from daily publication')
        for section, section_items in sections.items():
            for item in section_items:
                url = external_url(item.get('url'))
                require(bool(url), f'report {section} has an unsafe or invalid URL')
                require(url in daily_rows and url in search_rows, f'report {section} item absent from daily news or current-date search')
                require(is_japanese_summary(item.get('summary') or item.get('tldr')), f'Japanese report {section} summary missing')
                if section not in {'github', 'models'}:
                    require(is_japanese(item.get('title')), f'Japanese report {section} title missing')
    for relative, data, label in [('daily-news/index.html', daily, 'daily HTML'), ('presentations/auto_daily_report.html', report, 'report HTML')]:
        page = Page(source.text(relative))
        require(page.meta.get('report:date') == expected_date, f'{label} date mismatch')
        require(page.meta.get('report:total') == str(data.get('total')), f'{label} total mismatch')
        wanted = data.get('items', report_items)
        require(set(rows_by_url(wanted)) <= page.links, f'{label} is missing item URLs')
        if require_quality:
            if relative.startswith('daily-news/'):
                validate_rendered(page, wanted, True)
            else:
                for name, rows in sections.items():
                    validate_rendered(page, rows, False, name)
    homepage = Page(source.text('index.html'))
    require(homepage.elements.get('dailyReportDate', '').strip() == expected_date, 'homepage dailyReportDate mismatch')
    require(homepage.elements.get('dailyNewsDate', '').strip() == expected_date, 'homepage dailyNewsDate mismatch')
    first = headlines[0]
    require(first.get('title', '') in homepage.elements.get('dailyHeadlines', '') or canonical_url(first.get('url')) in homepage.links, 'homepage does not contain the top report headline or link')
    if require_quality:
        require(plain(first.get('title')) in plain(homepage.elements.get('dailyHeadlines', '')), 'homepage rendered top headline text mismatch')
    if expected:
        expected_daily = expected.json('daily-news/data.json')
        expected_report = expected.json('presentations/auto_daily_report.json')
        require(daily.get('date') == expected_daily.get('date') and signature(items) == signature(expected_daily.get('items', [])), 'deployed daily content differs from expected repository data')
        expected_sections = report_sections(expected_report)
        require(report.get('date') == expected_report.get('date') and report.get('total') == expected_report.get('total'), 'deployed report count/date differs from expected repository data')
        for name in sections:
            require(signature(sections[name]) == signature(expected_sections[name]), f'deployed report {name} differs from expected repository data')
        if require_quality:
            require(daily.get('quality') == expected_daily.get('quality'), 'deployed quality differs from expected repository data')
    if check_urls:
        for relative in ['about.html', 'contact.html', 'privacy-policy.html', 'credits.html', '404.html', 'ads.txt', 'robots.txt', 'sitemap.xml', 'assets/js/analytics.js', 'assets/hero-planck.jpg', 'assets/og/default.png']:
            require(bool(source.read(relative).strip()), f'critical URL {relative} is empty')
    mode = 'quality and content passed' if require_quality else 'structural checks passed; publication quality not certified'
    return f"{expected_date}: {len(items)} daily items, {len(search_rows)} searchable news rows; excluded={normalized_daily.get('excluded_item_count', 0)}, duplicates={normalized_daily.get('duplicate_item_count', 0)}; {mode}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--base-url')
    parser.add_argument('--date', required=True, type=lambda value: date.fromisoformat(value).isoformat())
    parser.add_argument('--require-quality', action='store_true')
    parser.add_argument('--check-urls', action='store_true')
    parser.add_argument('--attempts', type=int, default=1)
    parser.add_argument('--delay', type=float, default=15)
    args = parser.parse_args(argv)
    if not args.root and not args.base_url:
        parser.error('provide --root, --base-url, or both to compare live content with the repository')
    if not 1 <= args.attempts <= 6 or not 0 <= args.delay <= 30:
        parser.error('attempts must be 1..6 and delay 0..30 seconds')
    source = Source(args.root, args.base_url)
    expected = Source(args.root) if args.root and args.base_url else None
    for attempt in range(args.attempts):
        try:
            print(verify(source, args.date, args.require_quality, expected, args.check_urls))
            return 0
        except (PublicationError, KeyError, TypeError, ValueError) as error:
            print(f'Publication verification failed: {error}', file=sys.stderr)
            if attempt + 1 < args.attempts:
                time.sleep(args.delay)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
