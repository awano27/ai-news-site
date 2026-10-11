"""Legacy writers must not rewrite reviewed copy or reuse its provenance."""
from copy import deepcopy
from datetime import datetime
import importlib.util
import inspect
import json
import os
from pathlib import Path

import pytest

import update_news_archive as updater
from src.utils import archive_protection

ROOT = Path(__file__).resolve().parents[1]
DAY = '2026-10-10'
HTML = ('<html><div class="news-item"><div class="news-rank">1</div>'
        '<h3>Replacement article</h3><p>Unreviewed replacement</p>'
        '<a href="https://example.org/new">Source</a></div></html>')
MARKERS = [
    {'publication_mode': 'editorial_review'},
    {'quality': {'mode': 'editorial_review'}},
    {'quality': {'status': 'editorial_reviewed'}},
    {'items': [{'editorial_review': {'content_sha256': 'review fingerprint'}}]},
    {'items': [{'processing_status': 'editorial_reviewed'}]},
    {'items': [{'reviewed_summary': {'reviewed_at': DAY}}]},
    {'items': [{'claim_evidence': {}}]},
    {'items': [{'provenance': {'review_method': 'ai_document_review'}}]},
]


def payload(marker=None):
    data = {'date': DAY, 'count': 1, 'items': [{
        'title': '<b>Reviewed title</b>', 'summary': 'Reviewed &amp; text',
        'url': 'https://example.org/reviewed', 'date': '2026/10/09',
        'points': ['Reviewed &amp; point'], 'claim_evidence': None,
    }]}
    if marker:
        marker = deepcopy(marker)
        if 'items' in marker:
            data['items'][0].update(marker.pop('items')[0])
        data.update(marker)
    return data


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def snapshot_tree(root):
    return {p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


def prepare(tmp_path, raw):
    news = tmp_path / 'news'
    news.mkdir()
    (news / f'{DAY}.json').write_text(raw, encoding='utf-8')
    (news / f'{DAY}.html').write_text('Reviewed HTML', encoding='utf-8')
    (news / 'archive_index.json').write_text(json.dumps([
        {'date': DAY, 'file': f'{DAY}.json', 'count': 1}]), encoding='utf-8')
    (news / 'version.json').write_text('{"version":"keep"}', encoding='utf-8')
    return news


def configure_updater(monkeypatch, tmp_path, news, *, today=False):
    inputs = tmp_path / 'input'
    inputs.mkdir()
    txt = inputs / '20261010.txt'
    txt.write_text('Unreviewed new title\nhttps://example.org/new', encoding='utf-8')
    os.utime(txt, (1, 1))  # Even an older input is forced for the same day.
    monkeypatch.setattr(updater, 'INPUT_DAY_DIR', inputs)
    monkeypatch.setattr(updater, 'PUBLIC_NEWS_DIR', news)
    monkeypatch.setattr(updater, 'ARCHIVE_INDEX_FILE', news / 'archive_index.json')
    monkeypatch.setattr(updater, 'VERSION_FILE', news / 'version.json')

    class FixedClock(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 10, 10 if today else 11, 8)

    monkeypatch.setattr(updater, 'datetime', FixedClock)
    return inputs


@pytest.mark.parametrize('marker', MARKERS)
@pytest.mark.parametrize('today', [True, False])
def test_updater_refuses_reviewed_even_for_today_or_older_mtime(monkeypatch, tmp_path, marker, today):
    news = prepare(tmp_path, json.dumps(payload(marker)))
    configure_updater(monkeypatch, tmp_path, news, today=today)
    before = snapshot_tree(tmp_path)
    with pytest.raises(ValueError, match='protected|reviewed'):
        updater.update_archive()
    assert snapshot_tree(tmp_path) == before


@pytest.mark.parametrize('marker', MARKERS)
def test_html_archiver_refuses_before_fetch_or_any_output(monkeypatch, tmp_path, marker):
    archiver = module('archive_daily_ai_news')
    news = prepare(tmp_path, json.dumps(payload(marker)))
    monkeypatch.setattr(archiver, 'OUT_DIR', news)
    monkeypatch.setattr(archiver.sys, 'argv', ['archive_daily_ai_news.py', DAY])
    def unexpected_fetch():
        pytest.fail('Protected target must be rejected before fetching a replacement')
    monkeypatch.setattr(archiver, 'fetch_remote', unexpected_fetch)
    before = snapshot_tree(tmp_path)
    assert archiver.main() == 1
    assert snapshot_tree(tmp_path) == before


@pytest.mark.parametrize('marker', MARKERS)
def test_normalizer_preserves_reviewed_text_and_provenance(monkeypatch, tmp_path, marker):
    normalizer = module('normalize_archive_json')
    news = prepare(tmp_path, json.dumps(payload(marker)))
    before = snapshot_tree(tmp_path)
    assert normalizer.normalize_file(news / f'{DAY}.json') is False
    assert snapshot_tree(tmp_path) == before


@pytest.mark.parametrize('raw', [
    '{broken', 'null', '[]', '{"items": "bad"}', '{"items": [null]}',
    '{"items": [], "score": NaN}',
    '{"publication_mode":"editorial_review","publication_mode":"automatic","items":[]}',
])
def test_invalid_existing_json_fails_closed_everywhere(monkeypatch, tmp_path, raw):
    news = prepare(tmp_path, raw)
    configure_updater(monkeypatch, tmp_path, news, today=True)
    before = snapshot_tree(tmp_path)
    with pytest.raises(ValueError, match='invalid|unreadable'):
        updater.update_archive()
    archiver = module('archive_daily_ai_news')
    monkeypatch.setattr(archiver, 'OUT_DIR', news)
    monkeypatch.setattr(archiver.sys, 'argv', ['archive_daily_ai_news.py', DAY])
    monkeypatch.setattr(archiver, 'fetch_remote', lambda: (HTML, 'fixture'))
    assert archiver.main() == 1
    normalizer = module('normalize_archive_json')
    assert normalizer.normalize_file(news / f'{DAY}.json') is False
    assert snapshot_tree(tmp_path) == before


def test_non_utf8_existing_snapshot_refuses_all_writers(monkeypatch, tmp_path):
    news = prepare(tmp_path, '{}')
    (news / f'{DAY}.json').write_bytes(b'\xffinvalid')
    configure_updater(monkeypatch, tmp_path, news, today=True)
    before = snapshot_tree(tmp_path)
    with pytest.raises(ValueError, match='unreadable'):
        updater.update_archive()
    archiver = module('archive_daily_ai_news')
    monkeypatch.setattr(archiver, 'OUT_DIR', news)
    monkeypatch.setattr(archiver.sys, 'argv', ['archive_daily_ai_news.py', DAY])
    monkeypatch.setattr(archiver, 'fetch_remote', lambda: (HTML, 'fixture'))
    assert archiver.main() == 1
    assert module('normalize_archive_json').normalize_file(news / f'{DAY}.json') is False
    assert snapshot_tree(tmp_path) == before


def test_updater_preflights_entire_batch_before_writing(monkeypatch, tmp_path):
    news = prepare(tmp_path, json.dumps(payload(MARKERS[0])))
    inputs = configure_updater(monkeypatch, tmp_path, news, today=True)
    # Sorted before the rejected date: cannot be published before refusal.
    (inputs / '20261009.txt').write_text('Safe new title\nhttps://example.org/new')
    before = snapshot_tree(tmp_path)
    with pytest.raises(ValueError):
        updater.update_archive()
    assert snapshot_tree(tmp_path) == before


@pytest.mark.parametrize('raw', [json.dumps(payload(MARKERS[0])), '{invalid'])
def test_normalizer_preflights_entire_batch_before_writing(monkeypatch, tmp_path, raw):
    normalizer = module('normalize_archive_json')
    news = prepare(tmp_path, raw)
    (news / '2026-10-09.json').write_text(json.dumps(payload()))
    monkeypatch.setattr(normalizer, 'NEWS_DIR', news)
    before = snapshot_tree(tmp_path)
    assert normalizer.main() == 1
    assert snapshot_tree(tmp_path) == before


def test_safe_updater_still_creates_and_replaces_unreviewed_snapshots(monkeypatch, tmp_path):
    news = prepare(tmp_path, json.dumps(payload()))
    inputs = configure_updater(monkeypatch, tmp_path, news, today=True)
    (inputs / '20261009.txt').write_text('Another title\nhttps://example.org/other')
    assert updater.update_archive() is True
    for day in (DAY, '2026-10-09'):
        data = json.loads((news / f'{day}.json').read_text())
        assert data['count'] == 1
        assert 'editorial_review' not in data['items'][0]
        assert 'publication_mode' not in data
    assert len(json.loads((news / 'archive_index.json').read_text())) == 2


def test_safe_html_archiver_still_writes_new_content(monkeypatch, tmp_path):
    archiver = module('archive_daily_ai_news')
    news = prepare(tmp_path, json.dumps(payload()))
    monkeypatch.setattr(archiver, 'OUT_DIR', news)
    monkeypatch.setattr(archiver.sys, 'argv', ['archive_daily_ai_news.py', DAY])
    monkeypatch.setattr(archiver, 'fetch_remote', lambda: (HTML, 'fixture'))
    assert archiver.main() in (None, 0)
    data = json.loads((news / f'{DAY}.json').read_text())
    assert data['items'][0]['title'] == 'Replacement article'
    assert 'editorial_review' not in data['items'][0]
    assert (news / f'{DAY}.html').read_text() == HTML


def test_safe_normalizer_still_normalizes_unreviewed_copy(tmp_path):
    normalizer = module('normalize_archive_json')
    news = prepare(tmp_path, json.dumps(payload()))
    assert normalizer.normalize_file(news / f'{DAY}.json') is True
    item = json.loads((news / f'{DAY}.json').read_text())['items'][0]
    assert item['title'] == 'Reviewed title'
    assert item['summary'] == 'Reviewed & text'
    assert item['date'] == '2026-10-09'


@pytest.mark.parametrize(('text', 'expected'), [
    ('[Source](https://example.org/article)', ['https://example.org/article']),
    ('https://example.org/a)))', ['https://example.org/a']),
    ('[Source](https://example.org/a_(b))', ['https://example.org/a_(b)']),
    ('https://example.org/a_(b_(c))', ['https://example.org/a_(b_(c))']),
    ('https://example.org/a)b(c)', ['https://example.org/a)b(c)']),
    ('https://example.org/a_%28b%29', ['https://example.org/a_%28b%29']),
    ('[Source](https://example.org/a_%28b%29)', ['https://example.org/a_%28b%29']),
    ('[Source](https://example.org/a_(b))\nhttps://example.org/a_(b)', ['https://example.org/a_(b)']),
    ('https://example.org/a\nhttps://example.org/a', ['https://example.org/a']),
    ('https://example.org/a!\nhttps://example.org/b,', ['https://example.org/a!', 'https://example.org/b,']),
])
def test_url_cleanup_trims_only_unmatched_closing_parentheses_then_dedupes(text, expected):
    item = updater.extract_news_content('Title\n' + text)
    assert [link['href'] for link in item['links']] == expected
    assert item['url'] == expected[0]
    assert item['extracted_urls_count'] == len(expected)


def test_public_provenance_detector_covers_falsey_markers_and_plain_copy():
    assert hasattr(archive_protection, 'has_review_provenance')
    for key in ('editorial_review', 'reviewed_summary', 'claim_evidence', 'provenance'):
        for value in ({}, [], '', False):
            assert archive_protection.has_review_provenance({'items': [{key: value}]})
        assert not archive_protection.has_review_provenance({'items': [{key: None}]})
    assert not archive_protection.has_review_provenance(payload())


def test_public_strict_loader_rejects_ambiguous_json():
    assert hasattr(archive_protection, 'load_strict_json')
    for raw in ('{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}', '{"x": -Infinity}'):
        with pytest.raises(ValueError):
            archive_protection.load_strict_json(raw)
    assert archive_protection.load_strict_json('{"items": []}') == {'items': []}


def test_protected_error_is_distinct_from_malformed_snapshot(tmp_path):
    assert hasattr(archive_protection, 'ProtectedArchiveError')
    news = prepare(tmp_path, json.dumps(payload(MARKERS[0])))
    with pytest.raises(archive_protection.ProtectedArchiveError):
        archive_protection.guard_legacy_archive_write(news / f'{DAY}.json')
    (news / f'{DAY}.json').write_text('{invalid')
    with pytest.raises(archive_protection.ArchiveProtectionError) as error:
        archive_protection.guard_legacy_archive_write(news / f'{DAY}.json')
    assert not isinstance(error.value, archive_protection.ProtectedArchiveError)


def test_normalizer_preserve_mode_keeps_reviewed_history_and_normalizes_new_day(monkeypatch, tmp_path):
    normalizer = module('normalize_archive_json')
    assert 'preserve_reviewed' in inspect.signature(normalizer.main).parameters
    news = prepare(tmp_path, json.dumps(payload(MARKERS[0])))
    reviewed = snapshot_tree(news)[Path(f'{DAY}.json')]
    new_day = news / '2026-10-11.json'
    new_day.write_text(json.dumps(payload()))
    # A derived alias is never a bulk normalization target, even if it is stale.
    alias = news / 'daily_latest.json'
    alias.write_text('{stale derived alias')
    alias_before = (alias.read_bytes(), alias.stat().st_mtime_ns)
    monkeypatch.setattr(normalizer, 'NEWS_DIR', news)
    assert normalizer.main(preserve_reviewed=True) == 0
    assert snapshot_tree(news)[Path(f'{DAY}.json')] == reviewed
    assert (alias.read_bytes(), alias.stat().st_mtime_ns) == alias_before
    assert json.loads(new_day.read_text())['items'][0]['summary'] == 'Reviewed & text'


@pytest.mark.parametrize('raw', ['{invalid', '{"items":[null]}', '{"value":NaN}', b'\xff'])
def test_normalizer_preserve_mode_still_preflights_invalid_batch(monkeypatch, tmp_path, raw):
    normalizer = module('normalize_archive_json')
    assert 'preserve_reviewed' in inspect.signature(normalizer.main).parameters
    news = prepare(tmp_path, json.dumps(payload(MARKERS[0])))
    (news / '2026-10-11.json').write_text(json.dumps(payload()))
    (news / '2026-10-12.json').write_bytes(raw if isinstance(raw, bytes) else raw.encode())
    monkeypatch.setattr(normalizer, 'NEWS_DIR', news)
    before = snapshot_tree(tmp_path)
    assert normalizer.main(preserve_reviewed=True) == 1
    assert snapshot_tree(tmp_path) == before


def test_updater_preserve_mode_keeps_reviewed_history_and_publishes_new_day(monkeypatch, tmp_path):
    assert 'preserve_reviewed' in inspect.signature(updater.update_archive).parameters
    news = prepare(tmp_path, json.dumps(payload(MARKERS[0])))
    inputs = configure_updater(monkeypatch, tmp_path, news, today=False)
    reviewed = snapshot_tree(news)[Path(f'{DAY}.json')]
    (inputs / '20261011.txt').write_text('New title\nhttps://example.org/new-day')
    assert updater.update_archive(preserve_reviewed=True) is True
    assert snapshot_tree(news)[Path(f'{DAY}.json')] == reviewed
    new_day = json.loads((news / '2026-10-11.json').read_text())
    assert new_day['items'][0]['title'] == 'New title'
    assert not archive_protection.has_review_provenance(new_day)
    index = json.loads((news / 'archive_index.json').read_text())
    assert [item['date'] for item in index] == ['2026-10-11', DAY]


def test_updater_preserve_mode_still_preflights_invalid_batch(monkeypatch, tmp_path):
    assert 'preserve_reviewed' in inspect.signature(updater.update_archive).parameters
    news = prepare(tmp_path, json.dumps(payload(MARKERS[0])))
    inputs = configure_updater(monkeypatch, tmp_path, news, today=False)
    (inputs / '20261011.txt').write_text('New title\nhttps://example.org/new-day')
    (inputs / '20261012.txt').write_text('Another title\nhttps://example.org/another')
    (news / '2026-10-12.json').write_text('{invalid')
    before = snapshot_tree(tmp_path)
    with pytest.raises(archive_protection.ArchiveProtectionError):
        updater.update_archive(preserve_reviewed=True)
    assert snapshot_tree(tmp_path) == before


def test_updater_preserve_mode_with_only_reviewed_input_does_not_touch_indexes(monkeypatch, tmp_path):
    news = prepare(tmp_path, json.dumps(payload(MARKERS[0])))
    configure_updater(monkeypatch, tmp_path, news, today=True)
    before = snapshot_tree(tmp_path)
    assert updater.update_archive(preserve_reviewed=True) is False
    assert snapshot_tree(tmp_path) == before
