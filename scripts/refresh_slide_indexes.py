#!/usr/bin/env python3
"""Refresh generated slide discovery without rebuilding curated historical records.

Only previously unindexed HTML decks are opened. Existing metadata/list rows and
extra editorial fields are retained, including history absent from this checkout.
The curated day_slides_index.html remains part of the daily authoring workflow.
The newsstand is rendered only when metadata changes or its output is missing.

    python scripts/refresh_slide_indexes.py [--root PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from script import build_day_slides_index as metadata_builder
from script import build_day_slides_list as newsstand_builder

SLIDES = Path('presentations/day_slides')
META = SLIDES / 'meta_index.json'
LIST = SLIDES / 'list.json'
NEWSSTAND = Path('presentations/day_slides_list.html')
FILE_RE = re.compile(r'day_slide_(\d{4})_(\d{2})_(\d{2})\.html')
ISSUE_KEYS = ('date', 'no', 'file', 'url', 'title', 'description', 'section', 'cat', 'cat_label', 'cover')


class RefreshError(ValueError):
    pass


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RefreshError(f'{path.name}: {exc}') from exc


def validate_indexes(meta, entries) -> None:
    """Refuse an incomplete base rather than silently replacing archive history."""
    try:
        if not isinstance(meta, dict) or not isinstance(meta.get('issues'), list) or not meta['issues']:
            raise ValueError('expected a nonempty issues array')
        if not isinstance(meta.get('categories'), dict):
            raise ValueError('expected categories object')
        date.fromisoformat(meta['since'])
        date.fromisoformat(meta['latest'])
        dates, numbers = set(), set()
        for issue in meta['issues']:
            if not isinstance(issue, dict) or not all(key in issue for key in ISSUE_KEYS):
                raise ValueError('incomplete issue record')
            if not all(isinstance(issue[key], str) for key in ISSUE_KEYS if key not in ('no', 'cover')):
                raise ValueError('issue text fields must be strings')
            if issue['cover'] is not None and not isinstance(issue['cover'], str):
                raise ValueError('issue cover must be a string or null')
            date.fromisoformat(issue['date'])
            if issue['date'] in dates or issue['no'] in numbers:
                raise ValueError('duplicate issue date or index number')
            if type(issue['no']) is not int or issue['no'] < 1:
                raise ValueError('invalid index issue number')
            if issue['cat'] not in newsstand_builder.CATS:
                raise ValueError('unknown issue category')
            dates.add(issue['date'])
            numbers.add(issue['no'])
    except (KeyError, TypeError, ValueError) as exc:
        raise RefreshError(f'{META.name}: {exc}') from exc
    try:
        if not isinstance(entries, list):
            raise ValueError('expected an array')
        dates = set()
        for entry in entries:
            if not isinstance(entry, dict) or not all(key in entry for key in ('date', 'url', 'label')):
                raise ValueError('incomplete list record')
            if not all(isinstance(entry[key], str) for key in ('date', 'url', 'label')):
                raise ValueError('list date, URL and label must be strings')
            date.fromisoformat(entry['date'])
            if entry['date'] in dates:
                raise ValueError('duplicate list date')
            dates.add(entry['date'])
    except (TypeError, ValueError) as exc:
        raise RefreshError(f'{LIST.name}: {exc}') from exc


def discover(root: Path, issues: list[dict]) -> list[dict]:
    listed = {issue['date'] for issue in issues}
    numbers = {issue['no'] for issue in issues}
    added = []
    original_day_dir = metadata_builder.DAY_DIR
    metadata_builder.DAY_DIR = root / SLIDES
    try:
        for path in sorted((root / SLIDES).glob('day_slide_????_??_??.html')):
            match = FILE_RE.fullmatch(path.name)
            if not match:
                continue
            stamp = '-'.join(match.groups())
            if stamp in listed:
                continue
            try:
                date.fromisoformat(stamp)
                page = path.read_text(encoding='utf-8')
                if not any(re.search(pattern, page) for pattern in (
                    r'<title\b[^>]*>\s*\S', r'<h1\b[^>]*>\s*\S',
                    r'<meta\s+property="og:title"\s+content="\S',
                )):
                    raise ValueError('missing slide title')
                issue = metadata_builder.extract(path, stamp)
                issue['title'] = re.sub(r'\s*[|｜]\s*VisionHub\s*$', '', issue['title']).strip()
                printed = re.search(r'\bNo\.\s*(\d+)', page)
                # An index ordinal is stable even when the deck prints no issue number.
                number = int(printed.group(1)) if printed else max(numbers, default=0) + 1
                if number < 1 or number in numbers:
                    raise ValueError(f'duplicate or invalid index issue number {number}')
                issue['no'] = number
                numbers.add(number)
                added.append(issue)
            except (OSError, UnicodeError, ValueError) as exc:
                raise RefreshError(f'{path.name}: {exc}') from exc
    finally:
        metadata_builder.DAY_DIR = original_day_dir
    return added


def refresh(root: Path = ROOT, dry_run: bool = False) -> int:
    meta = read_json(root / META)
    entries = read_json(root / LIST)
    validate_indexes(meta, entries)
    added = discover(root, meta['issues'])
    if added:
        issues = sorted([*meta['issues'], *added], key=lambda row: row['date'], reverse=True)
        counts = Counter(issue['cat'] for issue in issues)
        category_order = [*meta['categories'], *(cat for cat in counts if cat not in meta['categories'])]
        meta = {
            **meta,
            'generated_from': max(issue['no'] for issue in issues),
            'since': min(meta['since'], issues[-1]['date']),
            'latest': issues[0]['date'],
            'categories': {cat: counts[cat] for cat in category_order if counts[cat]},
            'issues': issues,
        }
    listed = {entry['date'] for entry in entries}
    missing = [issue for issue in meta['issues'] if issue['date'] not in listed]
    if missing:
        entries = sorted([*entries, *({
            'date': issue['date'],
            'url': f'day_slides/{issue["file"]}',
            'label': f'{int(issue["date"][5:7])}/{int(issue["date"][8:10])} - {issue["title"]}',
        } for issue in missing)], key=lambda row: row['date'], reverse=True)

    # Prepare everything before writing. Commit discovery metadata last so an
    # interrupted run retries generation instead of treating it as complete.
    changes = {}
    if missing:
        changes[LIST] = json.dumps(entries, ensure_ascii=False, indent=2) + '\n'
    if added or not (root / NEWSSTAND).is_file():
        changes[NEWSSTAND] = newsstand_builder.render(meta)
    if added:
        changes[META] = json.dumps(meta, ensure_ascii=False, indent=2) + '\n'
    for issue in added:
        print(f'discovered {issue["date"]}: index issue {issue["no"]}')
    for rel, text in changes.items():
        path = root / rel
        if path.is_file() and path.read_bytes() == text.encode('utf-8'):
            continue
        if dry_run:
            print(f'would write {rel}')
        else:
            temporary = path.with_suffix(path.suffix + '.tmp')
            temporary.write_text(text, encoding='utf-8', newline='\n')
            temporary.replace(path)
            print(f'wrote {rel}')
    if not changes:
        print('slide indexes already current; no decks reread or outputs rewritten')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        return refresh(args.root, args.dry_run)
    except (RefreshError, OSError) as exc:
        print(f'[refresh_slide_indexes] {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
