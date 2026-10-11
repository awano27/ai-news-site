#!/usr/bin/env python3
"""Read-only, offline consistency check for the legacy news publication bundle.

The root date snapshots select archive_index/daily_index, daily_latest, and the
presentations compatibility APIs. The modern daily-news/data.json and nested
public-pages/news/daily route deliberately do not participate in this selector.
--base-ref checks only changed root snapshots against a locally available Git
baseline; it never fetches, regenerates, or writes publication files.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

# Direct `python tools/...` execution must use the same detector as the writers.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.archive_protection import has_review_provenance, load_strict_json
from scripts.publish_editorial_recovery import CONTENT_FIELDS, fingerprint

SNAPSHOT = re.compile(r'^(\d{4}-\d{2}-\d{2})(_daily)?\.json$')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
NEWS = Path('public-pages/news')


def _read(root, path, errors):
    try:
        return load_strict_json((root / path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        errors.append(f'{path}: cannot read JSON: {exc}')
        return None


def _items(data):
    if isinstance(data.get('items'), list):
        return data['items']
    if isinstance(data.get('articles'), list):
        return data['articles']
    return []


def _effective_date(data, fallback):
    metadata = data.get('metadata') or {}
    source_date = metadata.get('source_date', '')
    if isinstance(source_date, str) and DATE.fullmatch(source_date):
        return source_date
    dates = sorted(str(item.get('published_at') or '')[:10]
                   for item in data.get('articles', []) if isinstance(item, dict))
    dates = [date for date in dates if DATE.fullmatch(date)]
    return dates[-1] if dates else fallback


def _news_item(article, date, filename):
    source = article.get('source') or 'source'
    url = article.get('url') or ''
    return {
        'date': date, 'filename': filename, 'title': article.get('title') or 'タイトル不明',
        'summary': article.get('summary') or '', 'surprise': '',
        'sources': [{'text': source, 'url': url}] if url else [],
        'engineerPoints': '', 'businessPoints': '', 'comparison': '',
        'category': article.get('category') or '', 'importance': article.get('importance') or '',
        'score': article.get('score') or 0, 'rank': article.get('rank') or 0,
        'publishedAt': article.get('published_at') or '', 'source': source, 'url': url,
    }


def _compare(actual, expected, path, errors):
    """Report the first concrete difference per artifact without dumping content."""
    numeric = lambda value: isinstance(value, (int, float)) and not isinstance(value, bool)
    if numeric(actual) and numeric(expected) and actual == expected:
        return
    if type(actual) is not type(expected):
        errors.append(f'{path}: expected {type(expected).__name__}, got {type(actual).__name__}')
        return
    if isinstance(expected, dict):
        for key, value in expected.items():
            if key not in actual:
                errors.append(f'{path}.{key}: missing field')
                return
            before = len(errors)
            _compare(actual[key], value, f'{path}.{key}', errors)
            if len(errors) > before:
                return
        for key in actual.keys() - expected.keys():
            errors.append(f'{path}.{key}: unexpected field')
            return
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            errors.append(f'{path}: entry/item count {len(actual)} != expected {len(expected)}')
            return
        for index, (left, right) in enumerate(zip(actual, expected)):
            before = len(errors)
            _compare(left, right, f'{path}[{index}]', errors)
            if len(errors) > before:
                return
    elif actual != expected:
        errors.append(f'{path}: value differs from selected snapshot (expected {expected!r}, got {actual!r})')


def _git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'git command failed')
    return result.stdout


def _baseline_snapshots(root, base_ref, errors):
    """Read only root snapshots changed since one local Git commit."""
    snapshots = {}
    try:
        base = _git(root, 'rev-parse', '--verify', '--end-of-options', f'{base_ref}^{{commit}}').strip()
        changes = _git(root, 'diff', '--name-status', '--no-renames', base, '--', str(NEWS))
        for line in changes.splitlines():
            status, path = line.split('\t', 1)
            relative = Path(path)
            if relative.parent != NEWS or not SNAPSHOT.fullmatch(relative.name):
                continue
            snapshots[path] = None if status == 'A' else load_strict_json(_git(root, 'show', f'{base}:{path}'))
        # Producer checks run before git add, so include new untracked roots.
        untracked = _git(root, 'ls-files', '--others', '--exclude-standard', '--', str(NEWS))
        for path in untracked.splitlines():
            relative = Path(path)
            if relative.parent == NEWS and SNAPSHOT.fullmatch(relative.name):
                snapshots.setdefault(path, None)
    except (OSError, ValueError) as exc:
        errors.append(f'Git baseline {base_ref}: cannot verify reviewed snapshots: {exc}')
    return snapshots


def _check_reviewed_baseline(root, snapshots, errors):
    for path, old in snapshots.items():
        if not has_review_provenance(old):
            continue
        current = _read(root, path, errors)
        # Protect the evidence-to-content binding, not just its marker keys.
        _compare(current, old, f'{path}: reviewed baseline snapshot must be preserved', errors)


def validate_bundle(root, date=None, base_ref=None):
    """Return actionable errors. An empty list means the local bundle is coherent."""
    root = Path(root)
    errors = []
    baseline = _baseline_snapshots(root, base_ref, errors) if base_ref else {}
    selected = {}
    for path in sorted((root / NEWS).glob('*.json')):
        match = SNAPSHOT.fullmatch(path.name)
        if not match:
            continue
        data = _read(root, NEWS / path.name, errors)
        if not isinstance(data, dict):
            errors.append(f'{NEWS / path.name}: snapshot must be an object')
            continue
        items = _items(data)
        if isinstance(data.get('items'), list) and isinstance(data.get('articles'), list) and data['items'] != data['articles']:
            errors.append(f'{NEWS / path.name}: conflicting items/articles payloads')
        if any(not isinstance(item, dict) for item in items):
            errors.append(f'{NEWS / path.name}: items/articles must contain objects')
            continue
        for index, item in enumerate(items):
            review = item.get('editorial_review')
            if isinstance(review, dict) and 'content_sha256' in review:
                if not all(field in item for field in CONTENT_FIELDS):
                    errors.append(f'{NEWS / path.name}.items[{index}].editorial_review.content_sha256: missing fingerprinted content field')
                elif review['content_sha256'] != fingerprint(item):
                    errors.append(f'{NEWS / path.name}.items[{index}].editorial_review.content_sha256: reviewed copy fingerprint mismatch')
        filename_date, daily = match.groups()
        effective = _effective_date(data, filename_date) if daily else filename_date
        # Historical unreviewed count metadata was not canonical. Always check
        # derived counts, but only hard-gate this field for reviewed/changed/
        # explicitly requested source snapshots.
        strict_count = has_review_provenance(data) or str(NEWS / path.name) in baseline or effective == date
        if strict_count and 'count' in data and (isinstance(data['count'], bool) or data['count'] != len(items)):
            errors.append(f'{NEWS / path.name}.count: {data["count"]} != actual item count {len(items)}')
        if not items:
            continue  # Empty extractions are not publications, matching the selector.
        if not daily and data.get('date', filename_date) != filename_date:
            errors.append(f'{NEWS / path.name}.date: must match filename date')
        candidate = (path.name, data, effective, filename_date)
        previous = selected.get(effective)
        # Rich daily snapshots win; within a kind use lexical filename order.
        if previous is None or (daily and not previous[0].endswith('_daily.json')):
            selected[effective] = candidate
    if not selected:
        errors.append('Legacy bundle: no nonempty root date snapshots found')
        return errors
    if date and date not in selected:
        errors.append(f'Legacy bundle: requested date {date} has no selected nonempty snapshot')
    archive = []
    daily_index = []
    compatibility = []
    seen_api_dates = set()
    for selected_date in sorted(selected, reverse=True):
        filename, data, effective, filename_date = selected[selected_date]
        count = len(_items(data))
        entry = {'date': effective, 'file': filename, 'count': count}
        if filename_date != effective:
            entry['snapshot_date'] = filename_date
        archive.append(entry)
        metadata = data.get('metadata') or {}
        daily_index.append(dict(entry, extracted_at=metadata.get('extracted_at') or data.get('extracted_at') or '',
                                source_date=metadata.get('source_date') or '', source=metadata.get('source') or data.get('source') or ''))
        api_date = _effective_date(data, effective)
        if api_date in seen_api_dates:
            continue
        seen_api_dates.add(api_date)
        articles = data.get('articles') if isinstance(data.get('articles'), list) else _items(data)
        if not articles:
            continue
        api_items = [_news_item(item, api_date, filename) for item in articles[:3]]
        api_entry = {'date': api_date, 'snapshotDate': effective, 'filename': filename, 'file': filename,
                     'title': api_items[0]['title'], 'summary': api_items[0]['summary'], 'count': len(articles), 'items': api_items}
        if data.get('publication_mode'):
            api_entry['publicationMode'] = data['publication_mode']
        if data.get('notice'):
            api_entry['notice'] = data['notice']
        compatibility.append(api_entry)
    for name, expected in [('archive_index.json', archive), ('daily_index.json', daily_index)]:
        path = NEWS / name
        _compare(_read(root, path, errors), expected, str(path), errors)
    latest = selected[max(selected)][1]
    _compare(_read(root, NEWS / 'daily_latest.json', errors), latest, str(NEWS / 'daily_latest.json'), errors)
    compatibility.sort(key=lambda entry: entry['date'], reverse=True)
    for filename, latest_only in [('daily-news.json', False), ('daily-news-latest.json', True)]:
        path = Path('presentations/api') / filename
        actual = _read(root, path, errors)
        if not isinstance(actual, dict):
            errors.append(f'{path}: API must be an object')
            continue
        entries = compatibility[:10] if latest_only else compatibility
        expected = {'totalCount': len(compatibility), 'totalArticles': sum(entry['count'] for entry in compatibility),
                    'entries': entries, 'items': entries}
        if latest_only:
            expected['latestCount'] = len(entries)
        # generatedAt is a build timestamp, not source evidence.
        _compare({key: value for key, value in actual.items() if key != 'generatedAt'}, expected, str(path), errors)
    if base_ref:
        _check_reviewed_baseline(root, baseline, errors)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--date', help='Require this effective publication date in the audited bundle')
    parser.add_argument('--base-ref', help='Local Git commit to compare changed reviewed snapshots against')
    args = parser.parse_args(argv)
    errors = validate_bundle(args.root, args.date, args.base_ref)
    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1
    print('Legacy archive bundle is consistent (snapshots, indexes, latest, compatibility APIs).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
