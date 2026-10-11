"""Offline regressions for the legacy snapshot/index/compatibility bundle."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

from scripts.publish_editorial_recovery import fingerprint

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'tools/check_legacy_archive_bundle.py'
DATE = '2026-10-10'


def checker():
    assert CHECKER.exists(), 'Missing legacy bundle consistency validator'
    spec = importlib.util.spec_from_file_location('legacy_archive_bundle', CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(root, path):
    return json.loads((root / path).read_text())


def write(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value), encoding='utf-8')


def generate(root):
    for name in ('rebuild-news-indexes.js', 'generate-daily-news-json.js'):
        subprocess.run(['node', str(root / 'scripts' / name)], cwd=root, check=True, capture_output=True, text=True)


@pytest.fixture
def bundle(tmp_path):
    (tmp_path / 'scripts').mkdir()
    for name in ('rebuild-news-indexes.js', 'generate-daily-news-json.js'):
        shutil.copyfile(ROOT / 'scripts' / name, tmp_path / 'scripts' / name)
    for date, count in [('2026-10-09', 1), (DATE, 3)]:
        items = [{'title': f'Reviewed {i}', 'summary': f'Summary {i}', 'url': f'https://example.test/{date}/{i}',
                  'source': 'Primary source', 'published_at': date, 'impact': f'Audience {i}', 'processing_status': 'editorial_reviewed',
                  'editorial_review': {'source_url': f'https://example.test/{date}/{i}', 'source_date': date,
                                       'reviewed_at': date, 'review_method': 'ai_document_review',
                                       'content_sha256': 'a' * 64}}
                 for i in range(count)]
        for item in items:
            item['editorial_review']['content_sha256'] = fingerprint(item)
        write(tmp_path, f'public-pages/news/{date}.json', {'date': date, 'count': count,
              'publication_mode': 'editorial_review', 'notice': 'Reviewed provisional edition', 'items': items})
    generate(tmp_path)
    return tmp_path


def test_generated_bundle_passes_without_reading_separate_daily_route(bundle):
    write(bundle, 'daily-news/data.json', {'items': [{'url': 'raw'}] * 128})
    write(bundle, f'public-pages/news/daily/{DATE}.json', {'items': [{'url': 'raw'}] * 128})
    assert checker().validate_bundle(bundle) == []


@pytest.mark.parametrize('path', ['public-pages/news/archive_index.json', 'public-pages/news/daily_index.json'])
def test_rejects_pr124_stale_index_count(bundle, path):
    data = read(bundle, path)
    data[0]['count'] = 128
    write(bundle, path, data)
    assert any('count' in error for error in checker().validate_bundle(bundle))


@pytest.mark.parametrize('field,value', [('file', '2026-10-09.json'), ('date', '2026-10-08')])
def test_rejects_wrong_index_reference(bundle, field, value):
    path = 'public-pages/news/archive_index.json'
    data = read(bundle, path)
    data[0][field] = value
    write(bundle, path, data)
    assert checker().validate_bundle(bundle)


def test_rejects_snapshot_claimed_count_without_real_items(bundle):
    path = f'public-pages/news/{DATE}.json'
    data = read(bundle, path)
    data['items'] = []
    write(bundle, path, data)
    assert checker().validate_bundle(bundle)


def test_rejects_stale_daily_latest_even_if_count_is_same(bundle):
    path = 'public-pages/news/daily_latest.json'
    data = read(bundle, path)
    data['items'][0]['url'] = 'https://example.test/wrong'
    write(bundle, path, data)
    assert any('daily_latest' in error for error in checker().validate_bundle(bundle))


@pytest.mark.parametrize('file', ['daily-news.json', 'daily-news-latest.json'])
@pytest.mark.parametrize('mutation', ['count', 'date', 'filename', 'mode', 'url', 'sources', 'aliases', 'totals'])
def test_rejects_inconsistent_compatibility_api(bundle, file, mutation):
    path = f'presentations/api/{file}'
    data = read(bundle, path)
    for alias in ['entries', 'items']:
        entry = data[alias][0]
        if mutation == 'count': entry['count'] = 128
        elif mutation == 'date': entry['date'] = '2026-10-08'
        elif mutation == 'filename': entry['filename'] = '2026-10-09.json'
        elif mutation == 'mode': entry.pop('publicationMode')
        elif mutation == 'url': entry['items'][0]['url'] = 'https://example.test/wrong'
        elif mutation == 'sources': entry['items'][0]['sources'] = []
    if mutation == 'aliases': data['items'] = []
    if mutation == 'totals': data['totalArticles'] = 999
    write(bundle, path, data)
    assert checker().validate_bundle(bundle)


def test_legacy_articles_source_date_and_daily_precedence_are_supported(bundle):
    write(bundle, 'public-pages/news/2026-10-11_daily.json', {
        'metadata': {'source_date': DATE, 'total_articles': 1},
        'articles': [{'title': 'Rich daily snapshot', 'url': 'https://example.test/rich', 'published_at': DATE}]})
    generate(bundle)
    assert checker().validate_bundle(bundle, date=DATE) == []


def commit_baseline(root):
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'add', '.'], cwd=root, check=True)
    subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.test', 'commit', '-qm', 'baseline'], cwd=root, check=True)
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()


@pytest.mark.parametrize('mutation', ['mode', 'provenance', 'removed_item', 'deleted_snapshot'])
def test_git_baseline_blocks_data_only_loss_of_reviewed_snapshot(bundle, mutation):
    base = commit_baseline(bundle)
    # Mutate an older day so checking only latest would miss this regression.
    path = 'public-pages/news/2026-10-09.json'
    data = read(bundle, path)
    if mutation == 'mode': data.pop('publication_mode')
    elif mutation == 'provenance': data['items'][0].pop('editorial_review')
    elif mutation == 'removed_item': data['items'] = []; data['count'] = 0
    if mutation == 'deleted_snapshot': (bundle / path).unlink()
    else: write(bundle, path, data)
    generate(bundle)
    errors = checker().validate_bundle(bundle, base_ref=base)
    assert any('reviewed baseline' in error for error in errors)


def test_git_baseline_accepts_unchanged_review_and_new_day(bundle):
    base = commit_baseline(bundle)
    write(bundle, 'public-pages/news/2026-10-11.json', {'date': '2026-10-11', 'count': 1, 'items': [{'title': 'New', 'url': 'https://example.test/new'}]})
    generate(bundle)
    assert checker().validate_bundle(bundle, base_ref=base) == []


def test_invalid_git_baseline_fails_closed(bundle):
    commit_baseline(bundle)
    assert any('baseline' in error for error in checker().validate_bundle(bundle, base_ref='0' * 40))


def test_missing_or_invalid_json_fails_with_actionable_path(bundle):
    (bundle / 'public-pages/news/daily_latest.json').write_text('{broken')
    assert any('daily_latest.json' in error for error in checker().validate_bundle(bundle))


def workflow(name):
    return yaml.safe_load((ROOT / '.github/workflows' / name).read_text())


def test_ci_covers_data_only_changes_and_validates_before_compatibility_commit():
    ci = workflow('daily-pipeline-tests.yml')
    events = ci.get('on', ci.get(True))
    for event in ('push', 'pull_request'):
        paths = events[event]['paths']
        for path in ('update_news_archive.py', 'tools/**', 'src/utils/archive_protection.py', 'public-pages/news/*.json', 'presentations/api/daily-news*.json'):
            assert path in paths
    runs = str(ci['jobs'])
    assert 'tests/test_legacy_archive_bundle.py' in runs
    assert 'test_reviewed_archive_protection.py' in runs
    assert 'check_legacy_archive_bundle.py' in runs and '--base-ref' in runs
    compat = workflow('generate-daily-news-json.yml')
    steps = compat['jobs']['generate-json']['steps']
    commands = '\n'.join(s.get('run', '') for s in steps)
    assert commands.index('generate-daily-news-json.js') < commands.index('check_legacy_archive_bundle.py') < commands.index('git commit')
    assert '--base-ref HEAD' in commands


def test_rejects_conflicting_items_and_articles_payloads(bundle):
    path = f'public-pages/news/{DATE}.json'
    data = read(bundle, path)
    data['articles'] = [{'title': 'Unreviewed alternate', 'url': 'https://example.test/alternate'}]
    write(bundle, path, data)
    generate(bundle)
    assert any('items/articles' in error for error in checker().validate_bundle(bundle))


def test_unchanged_unreviewed_historical_count_uses_actual_payload(bundle):
    path = 'public-pages/news/2026-10-09.json'
    data = read(bundle, path)
    data.pop('publication_mode')
    for item in data['items']:
        item.pop('editorial_review')
        item.pop('processing_status')
    data['count'] = 56
    write(bundle, path, data)
    generate(bundle)
    assert checker().validate_bundle(bundle) == []
    assert any('count' in error for error in checker().validate_bundle(bundle, date='2026-10-09'))


def test_changed_unreviewed_snapshot_count_is_checked_against_baseline(bundle):
    path = 'public-pages/news/2026-10-09.json'
    data = read(bundle, path)
    data.pop('publication_mode')
    for item in data['items']:
        item.pop('editorial_review')
        item.pop('processing_status')
    write(bundle, path, data)
    generate(bundle)
    base = commit_baseline(bundle)
    data['count'] = 56
    write(bundle, path, data)
    generate(bundle)
    assert any('count' in error for error in checker().validate_bundle(bundle, base_ref=base))


def test_json_numeric_equivalence_allows_integral_float_scores_but_not_bool(bundle):
    path = f'public-pages/news/{DATE}.json'
    data = read(bundle, path)
    data['items'][0]['score'] = 85.0
    write(bundle, path, data)
    generate(bundle)
    assert checker().validate_bundle(bundle) == []
    api_path = 'presentations/api/daily-news.json'
    api = read(bundle, api_path)
    api['totalCount'] = True
    write(bundle, api_path, api)
    assert checker().validate_bundle(bundle)


@pytest.mark.parametrize('field', ['title', 'summary', 'url', 'notice'])
def test_git_baseline_rejects_reusing_review_provenance_for_changed_copy(bundle, field):
    base = commit_baseline(bundle)
    path = f'public-pages/news/{DATE}.json'
    data = read(bundle, path)
    if field == 'notice': data[field] = 'Different notice'
    else: data['items'][0][field] = 'Changed content'
    write(bundle, path, data)
    generate(bundle)
    assert any('reviewed baseline' in error for error in checker().validate_bundle(bundle, base_ref=base))


@pytest.mark.parametrize('marker,value', [('claim_evidence', {}), ('reviewed_summary', ''), ('provenance', False), ('reviewed_at', ''), ('review_method', '')])
def test_git_baseline_matches_writer_protection_for_falsey_provenance(bundle, marker, value):
    path = 'public-pages/news/2026-10-09.json'
    data = read(bundle, path)
    data.pop('publication_mode')
    for item in data['items']:
        item.pop('editorial_review')
        item.pop('processing_status')
    data['items'][0][marker] = value
    write(bundle, path, data)
    generate(bundle)
    base = commit_baseline(bundle)
    data['items'][0].pop(marker)
    write(bundle, path, data)
    generate(bundle)
    assert any('reviewed baseline' in error for error in checker().validate_bundle(bundle, base_ref=base))


def test_required_effective_date_checks_daily_source_count(bundle):
    write(bundle, 'public-pages/news/2026-10-11_daily.json', {
        'count': 9, 'metadata': {'source_date': DATE},
        'articles': [{'title': 'Rich daily', 'url': 'https://example.test/rich', 'published_at': DATE}]})
    generate(bundle)
    assert any('count' in error for error in checker().validate_bundle(bundle, date=DATE))


@pytest.mark.parametrize('raw', ['{"items":[],"items":[]}', '{"items":[],"score":NaN}'])
def test_rejects_ambiguous_or_nonstandard_source_json(bundle, raw):
    (bundle / f'public-pages/news/{DATE}.json').write_text(raw)
    assert any('cannot read JSON' in error for error in checker().validate_bundle(bundle))


def test_git_baseline_protects_mode_only_snapshot_with_unmarked_items(bundle):
    path = 'public-pages/news/2026-10-09.json'
    data = read(bundle, path)
    for item in data['items']:
        item.pop('editorial_review')
        item.pop('processing_status')
    write(bundle, path, data)
    generate(bundle)
    base = commit_baseline(bundle)
    data['items'] = [{'title': 'Unreviewed replacement', 'url': 'https://example.test/replacement'}]
    write(bundle, path, data)
    generate(bundle)
    assert any('reviewed baseline' in error for error in checker().validate_bundle(bundle, base_ref=base))


def test_rejects_normalized_reviewed_characters_without_git_baseline(bundle):
    path = f'public-pages/news/{DATE}.json'
    data = read(bundle, path)
    item = data['items'][0]
    item['summary'] = 'Reviewed source reports 52％.'
    item['editorial_review']['content_sha256'] = fingerprint(item)
    write(bundle, path, data)
    generate(bundle)
    assert checker().validate_bundle(bundle) == []
    item['summary'] = item['summary'].replace('％', '%')
    write(bundle, path, data)
    generate(bundle)
    assert any('content_sha256' in error for error in checker().validate_bundle(bundle))


def test_rejects_missing_fingerprinted_field_with_actionable_error(bundle):
    path = f'public-pages/news/{DATE}.json'
    data = read(bundle, path)
    data['items'][0].pop('impact')
    write(bundle, path, data)
    generate(bundle)
    assert any('content_sha256' in error for error in checker().validate_bundle(bundle))


def test_untracked_new_snapshot_count_is_checked_before_git_add(bundle):
    base = commit_baseline(bundle)
    write(bundle, 'public-pages/news/2026-10-11.json', {
        'date': '2026-10-11', 'count': 99,
        'items': [{'title': 'New untracked item', 'url': 'https://example.test/untracked'}]})
    generate(bundle)
    assert any('2026-10-11.json.count' in error for error in checker().validate_bundle(bundle, base_ref=base))


def test_untracked_nested_modern_route_is_outside_legacy_baseline(bundle):
    base = commit_baseline(bundle)
    write(bundle, 'public-pages/news/daily/2026-10-11.json', {'count': 99, 'items': [{}]})
    assert checker().validate_bundle(bundle, base_ref=base) == []
