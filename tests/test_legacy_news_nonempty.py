"""Legacy news indexes must never advertise empty or missing snapshots."""
import json
import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def prepare(tmp_path, files):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    news = tmp_path / 'public-pages/news'
    news.mkdir(parents=True)
    for name in ('rebuild-news-indexes.js', 'generate-daily-news-json.js'):
        shutil.copyfile(ROOT / 'scripts' / name, scripts / name)
    for name, payload in files.items():
        (news / name).write_text(json.dumps(payload), encoding='utf-8')
    return news


def run(tmp_path, name):
    node = shutil.which('node')
    if not node:
        pytest.skip('node is required for legacy news regression tests')
    result = subprocess.run([node, str(tmp_path / 'scripts' / name)],
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def article(title='Actual article'):
    return {'title': title, 'summary': 'A source-backed article',
            'url': 'https://example.org/article', 'source': 'Example'}


def test_empty_newer_snapshot_does_not_replace_latest_or_enter_indexes(tmp_path):
    older = {'date': '2026-10-09', 'count': 1, 'items': [article()]}
    news = prepare(tmp_path, {
        '2026-10-09.json': older,
        '2026-10-10.json': {'date': '2026-10-10', 'count': 0, 'items': []},
    })
    run(tmp_path, 'rebuild-news-indexes.js')
    assert read(news / 'daily_latest.json') == older
    for index in ('archive_index.json', 'daily_index.json'):
        assert [row['date'] for row in read(news / index)] == ['2026-10-09']


def test_empty_rich_snapshot_cannot_hide_nonempty_same_day_snapshot(tmp_path):
    valid = {'date': '2026-10-10', 'count': 999, 'items': [article()]}
    news = prepare(tmp_path, {
        '2026-10-10.json': valid,
        '2026-10-10_daily.json': {'metadata': {'total_articles': 2}, 'articles': []},
    })
    run(tmp_path, 'rebuild-news-indexes.js')
    assert read(news / 'daily_latest.json') == valid
    assert read(news / 'daily_index.json')[0]['count'] == 1


def test_nonempty_rich_snapshot_preserves_source_date_and_precedence(tmp_path):
    rich = {'metadata': {'source_date': '2026-10-09'}, 'articles': [article('Rich')]}
    news = prepare(tmp_path, {
        '2026-10-09.json': {'count': 1, 'items': [article()]},
        '2026-10-10_daily.json': rich,
    })
    run(tmp_path, 'rebuild-news-indexes.js')
    assert read(news / 'daily_latest.json') == rich
    entry = read(news / 'daily_index.json')[0]
    assert entry['date'] == '2026-10-09'
    assert entry['snapshot_date'] == '2026-10-10'


def test_compatibility_api_skips_empty_missing_and_invalid_snapshots(tmp_path):
    news = prepare(tmp_path, {
        '2026-10-09.json': {'count': 99, 'items': [article()]},
        '2026-10-10.json': {'count': 0, 'items': []},
        'daily_index.json': [
            {'date': '2026-10-12', 'file': '2026-10-12.json', 'count': 99},
            {'date': '2026-10-11', 'file': '2026-10-11.json', 'count': 99},
            {'date': '2026-10-10', 'file': '2026-10-10.json', 'count': 0},
            {'date': '2026-10-09', 'file': '2026-10-09.json', 'count': 99},
        ],
    })
    (news / '2026-10-11.json').write_text('{invalid', encoding='utf-8')
    run(tmp_path, 'generate-daily-news-json.js')
    latest = read(tmp_path / 'presentations/api/daily-news-latest.json')
    assert [row['date'] for row in latest['entries']] == ['2026-10-09']
    assert latest['totalArticles'] == 1
    assert latest['entries'][0]['count'] == 1


def test_empty_duplicate_does_not_hide_valid_compatibility_entry(tmp_path):
    prepare(tmp_path, {
        '2026-10-10_daily.json': {'metadata': {'source_date': '2026-10-09'}, 'articles': []},
        '2026-10-09.json': {'items': [article()]},
        'daily_index.json': [
            {'date': '2026-10-10', 'file': '2026-10-10_daily.json'},
            {'date': '2026-10-09', 'file': '2026-10-09.json'},
        ],
    })
    run(tmp_path, 'generate-daily-news-json.js')
    latest = read(tmp_path / 'presentations/api/daily-news-latest.json')
    assert len(latest['entries']) == 1
    assert latest['entries'][0]['title'] == 'Actual article'


def test_compatibility_fallback_discovers_date_named_snapshots_without_index(tmp_path):
    prepare(tmp_path, {'2026-10-10.json': {'items': [article()]}})
    run(tmp_path, 'generate-daily-news-json.js')
    latest = read(tmp_path / 'presentations/api/daily-news-latest.json')
    assert latest['entries'][0]['date'] == '2026-10-10'


def test_empty_archiver_source_preserves_existing_snapshot(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location('legacy_archiver', ROOT / 'tools/archive_daily_ai_news.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    existing = {'date': '2026-10-10', 'items': [article()], 'count': 1}
    snapshot = tmp_path / '2026-10-10.json'
    snapshot.write_text(json.dumps(existing), encoding='utf-8')
    index = tmp_path / 'archive_index.json'
    index.write_text('[{"date":"2026-10-10","count":1}]', encoding='utf-8')
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    monkeypatch.setattr(module, 'OUT_DIR', tmp_path)
    monkeypatch.setattr(module, 'LOCAL_FALLBACK', tmp_path / 'missing.html')
    monkeypatch.setattr(module, 'fetch_remote', lambda: ('<html>redirect</html>', 'https://example.org/'))
    monkeypatch.setattr(module.sys, 'argv', ['archive_daily_ai_news.py', '2026-10-10'])
    assert module.main() == 1
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_blank_card_archiver_source_preserves_existing_snapshot(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location('legacy_archiver_blank', ROOT / 'tools/archive_daily_ai_news.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshot = tmp_path / '2026-10-10.json'
    snapshot.write_text('{"items":[{"title":"Preserved"}]}', encoding='utf-8')
    before = snapshot.read_bytes()
    monkeypatch.setattr(module, 'OUT_DIR', tmp_path)
    monkeypatch.setattr(module, 'LOCAL_FALLBACK', tmp_path / 'missing.html')
    monkeypatch.setattr(module, 'fetch_remote', lambda: ('<html><div class="news-item"></div></html>', 'https://example.org/'))
    monkeypatch.setattr(module.sys, 'argv', ['archive_daily_ai_news.py', '2026-10-10'])
    assert module.main() == 1
    assert snapshot.read_bytes() == before
    assert not (tmp_path / 'archive_index.json').exists()


def test_compatibility_fallback_prefers_nonempty_rich_snapshot(tmp_path):
    prepare(tmp_path, {
        '2026-10-10.json': {'items': [article('Simple')]},
        '2026-10-10_daily.json': {'articles': [article('Rich'), article('Second')]},
    })
    run(tmp_path, 'generate-daily-news-json.js')
    latest = read(tmp_path / 'presentations/api/daily-news-latest.json')
    assert latest['entries'][0]['title'] == 'Rich'
    assert latest['entries'][0]['count'] == 2


def test_compatibility_workflow_rebuilds_index_before_loading_it():
    workflow = yaml.safe_load((ROOT / '.github/workflows/generate-daily-news-json.yml').read_text())
    commands = '\n'.join(step.get('run', '') for step in workflow['jobs']['generate-json']['steps'])
    assert commands.index('rebuild-news-indexes.js') < commands.index('generate-daily-news-json.js')


def test_compatibility_api_preserves_provisional_notice_and_source_date(tmp_path):
    row = dict(article(), published_at='2026-10-09')
    prepare(tmp_path, {'2026-10-10.json': {
        'items': [row], 'publication_mode': 'editorial_review',
        'notice': '編集確認済み・3件の暫定版',
    }})
    run(tmp_path, 'generate-daily-news-json.js')
    latest = read(tmp_path / 'presentations/api/daily-news-latest.json')
    entry = latest['entries'][0]
    assert entry['date'] == '2026-10-10'
    assert entry.get('publicationMode') == 'editorial_review'
    assert entry.get('notice') == '編集確認済み・3件の暫定版'
    assert entry['items'][0]['publishedAt'] == '2026-10-09'
