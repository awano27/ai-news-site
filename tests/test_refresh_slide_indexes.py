"""Incremental publication must retain curated history and discover the next deck."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import finalize_day_slide

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / 'scripts' / 'refresh_slide_indexes.py'
META = Path('presentations/day_slides/meta_index.json')
LIST = Path('presentations/day_slides/list.json')
NEWSSTAND = Path('presentations/day_slides_list.html')
OUTPUTS = (META, LIST, NEWSSTAND)


def write(root, rel, content):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def page(root, stamp, number=None):
    numbered = '' if number is None else f'<p>No.{number}</p>'
    write(root, f'presentations/day_slides/day_slide_{stamp.replace("-", "_")}.html',
          f'<html><head><title>Model &amp; tools｜VisionHub｜{stamp}</title>'
          '<meta name="description" content="New model release.">'
          '</head><body><h1>Model &amp; tools</h1>' + numbered + '</body></html>')


def seed(root):
    old = {
        'date': '2026-10-08', 'no': 434, 'file': 'day_slide_2026_10_08.html',
        'url': 'https://visionhub.jp/presentations/day_slides/day_slide_2026_10_08.html',
        'title': 'Curated historical title', 'description': 'Original description',
        'section': 'Product', 'cat': 'prod', 'cat_label': 'プロダクト', 'cover': None,
        'primary_url': 'https://example.com/keep-custom-field',
    }
    meta = {'generated_from': 434, 'since': '2026-10-08', 'latest': '2026-10-08',
            'categories': {'prod': 1}, 'issues': [old], 'editorial_note': 'Keep me'}
    write(root, META, json.dumps(meta, ensure_ascii=False, indent=1))
    write(root, LIST, json.dumps([{'date': old['date'], 'url': f'day_slides/{old["file"]}',
                                 'label': '10/8 - Curated label', 'custom': 'keep'}], indent=1))
    write(root, NEWSSTAND, 'existing generated page\n')
    write(root, 'presentations/day_slides_index.html', 'curated canonical archive\n')
    write(root, 'llms.txt', 'unrelated historical content\n')
    return old


def run(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), *args],
                          text=True, capture_output=True, cwd=REPO)


def snapshot(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def read(root, rel):
    return json.loads((root / rel).read_text(encoding='utf-8'))


def test_new_slide_without_printed_number_updates_all_indexes_and_keeps_history(tmp_path):
    old = seed(tmp_path)
    page(tmp_path, '2026-10-09')
    cover = 'presentations/day_slides/images/1009/cover.jpg'
    write(tmp_path, cover, 'image fixture')
    before = snapshot(tmp_path)

    result = run(tmp_path)

    assert result.returncode == 0, result.stderr
    meta = read(tmp_path, META)
    assert meta['issues'][1:] == [old]  # Old deck is deliberately absent on disk.
    assert meta['editorial_note'] == 'Keep me'
    assert meta['since'] == '2026-10-08'
    assert meta['latest'] == '2026-10-09'
    assert meta['generated_from'] == 435
    assert meta['categories'] == {'prod': 1, 'model': 1}
    assert meta['issues'][0]['title'] == 'Model & tools'
    assert meta['issues'][0]['no'] == 435
    assert meta['issues'][0]['cover'] == 'day_slides/images/1009/cover.jpg'
    entries = read(tmp_path, LIST)
    assert entries[0] == {'date': '2026-10-09', 'url': 'day_slides/day_slide_2026_10_09.html',
                          'label': '10/9 - Model & tools'}
    assert entries[1] == json.loads(before[LIST])[0]
    rendered = (tmp_path / NEWSSTAND).read_text(encoding='utf-8')
    assert 'day_slide_2026_10_09.html' in rendered
    assert 'Curated historical title' in rendered
    assert 'Model &amp; tools' in rendered
    after = snapshot(tmp_path)
    assert {key for key in after if after[key] != before[key]} == set(OUTPUTS)


def test_next_day_and_year_rollover_use_stable_index_issue_numbers(tmp_path):
    seed(tmp_path)
    for stamp, expected in [('2026-10-09', 435), ('2026-10-10', 436), ('2027-01-01', 437)]:
        page(tmp_path, stamp)
        result = run(tmp_path)
        assert result.returncode == 0, result.stderr
        assert read(tmp_path, META)['latest'] == stamp
        assert read(tmp_path, META)['issues'][0]['no'] == expected
        assert read(tmp_path, LIST)[0]['date'] == stamp


def test_repeat_run_does_not_rewrite_or_reread_already_indexed_decks(tmp_path):
    seed(tmp_path)
    page(tmp_path, '2026-10-09')
    assert run(tmp_path).returncode == 0
    # Invalid UTF-8 in an indexed deck would fail an unnecessary reread.
    (tmp_path / 'presentations/day_slides/day_slide_2026_10_09.html').write_bytes(b'\xff')
    before = snapshot(tmp_path)
    for rel in OUTPUTS:
        os.utime(tmp_path / rel, ns=(1_600_000_000_000_000_000,) * 2)
    mtimes = {rel: (tmp_path / rel).stat().st_mtime_ns for rel in OUTPUTS}

    result = run(tmp_path)

    assert result.returncode == 0, result.stderr
    assert snapshot(tmp_path) == before
    assert {rel: (tmp_path / rel).stat().st_mtime_ns for rel in OUTPUTS} == mtimes


def test_dry_run_leaves_all_files_untouched(tmp_path):
    seed(tmp_path)
    page(tmp_path, '2026-10-09')
    before = snapshot(tmp_path)
    result = run(tmp_path, '--dry-run')
    assert result.returncode == 0, result.stderr
    assert snapshot(tmp_path) == before
    assert '2026-10-09' in result.stdout


@pytest.mark.parametrize('rel', [META, LIST])
@pytest.mark.parametrize('bad', [None, '{broken json', '{}'])
def test_missing_or_malformed_index_fails_without_discarding_history(tmp_path, rel, bad):
    seed(tmp_path)
    page(tmp_path, '2026-10-09')
    if bad is None:
        (tmp_path / rel).unlink()
    else:
        write(tmp_path, rel, bad)
    before = snapshot(tmp_path)
    result = run(tmp_path)
    assert result.returncode == 1
    assert rel.name in result.stderr
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('stamp,content', [
    ('2026-02-30', '<title>Invalid date</title>'),
    ('2026-10-09', '<main>Missing title</main>'),
])
def test_invalid_new_deck_fails_before_any_write(tmp_path, stamp, content):
    seed(tmp_path)
    write(tmp_path, f'presentations/day_slides/day_slide_{stamp.replace("-", "_")}.html', content)
    before = snapshot(tmp_path)
    result = run(tmp_path)
    assert result.returncode == 1
    assert 'day_slide_' in result.stderr
    assert snapshot(tmp_path) == before


def test_existing_metadata_repairs_missing_list_row_without_rerender(tmp_path):
    seed(tmp_path)
    write(tmp_path, LIST, '[]')
    old_page = (tmp_path / NEWSSTAND).read_bytes()
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert read(tmp_path, LIST)[0]['date'] == '2026-10-08'
    assert (tmp_path / NEWSSTAND).read_bytes() == old_page


def test_missing_newsstand_is_rendered_from_preserved_metadata(tmp_path):
    seed(tmp_path)
    (tmp_path / NEWSSTAND).unlink()
    before_meta = (tmp_path / META).read_bytes()
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert 'Curated historical title' in (tmp_path / NEWSSTAND).read_text()
    assert (tmp_path / META).read_bytes() == before_meta


def test_finalize_refreshes_indexes_after_injection(tmp_path, monkeypatch):
    seed(tmp_path)
    page(tmp_path, '2026-10-09')
    monkeypatch.setattr(finalize_day_slide, 'ROOT', tmp_path)
    # These steps rewrite unrelated site assets; exercise only the new real refresh.
    monkeypatch.setattr(finalize_day_slide, 'run_injectors', lambda *args: None)
    monkeypatch.setattr(finalize_day_slide, 'run_nav_home_feed_sitemap', lambda *args: 0)

    assert finalize_day_slide.finalize('1009', 2026, checks=False) == 0

    assert read(tmp_path, META)['latest'] == '2026-10-09'
    assert read(tmp_path, LIST)[0]['date'] == '2026-10-09'


def test_pages_refreshes_indexes_before_homepage_packaging():
    workflow = (REPO / '.github/workflows/pages.yml').read_text()
    command = 'python scripts/refresh_slide_indexes.py'
    assert command in workflow
    assert workflow.index(command) < workflow.index('node scripts/build-homepage-latest.js')


@pytest.mark.parametrize('rel,field,value', [
    (META, 'title', None),
    (META, 'cover', {}),
    (LIST, 'label', 123),
])
def test_malformed_record_types_fail_clearly_before_publication(tmp_path, rel, field, value):
    seed(tmp_path)
    page(tmp_path, '2026-10-09')
    data = read(tmp_path, rel)
    row = data['issues'][0] if rel == META else data[0]
    row[field] = value
    write(tmp_path, rel, json.dumps(data))
    before = snapshot(tmp_path)

    result = run(tmp_path)

    assert result.returncode == 1
    assert rel.name in result.stderr
    assert 'Traceback' not in result.stderr
    assert snapshot(tmp_path) == before
