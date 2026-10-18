import json
from pathlib import Path
import shutil
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]

def fixture(tmp_path):
    (tmp_path / 'scripts').mkdir()
    shutil.copy2(ROOT / 'scripts/build-homepage-latest.js', tmp_path / 'scripts')
    shutil.copy2(ROOT / 'index.html', tmp_path / 'index.html')
    slides = tmp_path / 'presentations/day_slides'
    slides.mkdir(parents=True)
    (slides / 'day_slide_2026_10_12.html').write_text('<title>REA | 2026-10-12</title><meta name="description" content="作者の検証例と限界"><h1>REAの確認範囲</h1>', encoding='utf-8')
    report = tmp_path / 'public-pages/api/auto_daily_report'
    report.mkdir(parents=True)
    (report / 'latest.json').write_text(json.dumps({'date': '2026-10-12', 'headlines': []}), encoding='utf-8')
    (tmp_path / 'news').mkdir()
    return tmp_path

def run(root, *args):
    return subprocess.run(['node', str(root / 'scripts/build-homepage-latest.js'), *args], capture_output=True, text=True, encoding='utf-8')

def test_unknown_clock_is_not_synthesized_and_repeat_is_idempotent(tmp_path):
    root = fixture(tmp_path)
    assert run(root).returncode == 0
    first = (root / 'index.html').read_bytes()
    data = json.loads((root / 'news/latest.json').read_text(encoding='utf-8'))
    assert data['generated_at'] == '2026-10-12'
    assert '生成時刻未記録' in first.decode('utf-8')
    assert 'id="statUpdated">未記録' in first.decode('utf-8')
    assert re.search(r'id="sitrepUpdate"[^>]*>REAの確認範囲', first.decode('utf-8'))
    assert run(root, '--check').returncode == 0
    assert (root / 'index.html').read_bytes() == first

def test_invalid_input_preserves_last_success_and_check_does_not_rewrite(tmp_path):
    root = fixture(tmp_path)
    assert run(root).returncode == 0
    before = {name: (root / name).read_bytes() for name in ['index.html', 'news/latest.json']}
    report = root / 'public-pages/api/auto_daily_report/latest.json'
    report.write_text('{invalid', encoding='utf-8')
    assert run(root).returncode != 0
    assert all((root / name).read_bytes() == data for name, data in before.items())
    report.write_text(json.dumps({'date': '2026-10-12', 'headlines': []}), encoding='utf-8')
    slide = root / 'presentations/day_slides/day_slide_2026_10_12.html'
    slide.write_text('<title>Changed</title><h1>変更された題名</h1>', encoding='utf-8')
    assert run(root, '--check').returncode != 0
    assert all((root / name).read_bytes() == data for name, data in before.items())

def test_real_clock_and_daily_schedule_are_explicit(tmp_path):
    root = fixture(tmp_path)
    (root / 'daily-news').mkdir()
    (root / 'daily-news/data.json').write_text(json.dumps({'date': '2026-10-12', 'generated_iso': '2026-10-12T00:21:36Z', 'items': [{'title': 'test'}], 'total': 1}), encoding='utf-8')
    assert run(root).returncode == 0
    assert '2026-10-12 09:21 JST' in (root / 'index.html').read_text(encoding='utf-8')
    workflow = (ROOT / '.github/workflows/pages.yml').read_text(encoding='utf-8')
    assert "cron: '15 0 * * *'" in workflow
    assert 'build-homepage-latest.js --strict --check' in workflow
    assert 'check_homepage_sync.py --base-url' in workflow

def test_strict_mode_preserves_last_success_when_required_source_is_missing(tmp_path):
    root = fixture(tmp_path)
    assert run(root).returncode == 0
    before = (root / 'index.html').read_bytes()
    assert run(root, '--strict').returncode != 0
    assert (root / 'index.html').read_bytes() == before

def test_resource_sync_uses_linked_metadata_not_an_earlier_navigation_link(tmp_path):
    root = fixture(tmp_path)
    tools = root / 'presentations/recommended_tools'
    tools.mkdir()
    (tools / 'index.html').write_text('<article data-evidence="official-info"></article>' * 3 + '<article data-evidence="usage-log"></article>', encoding='utf-8')
    (root / 'presentations/ai_tool_optimization_2026_04.html').write_text('<title>AIツール2026年6月版</title>', encoding='utf-8')
    index = root / 'index.html'
    index.write_text(index.read_text(encoding='utf-8').replace('<body>', '<body><a href="/presentations/recommended_tools/">shortcut</a>'), encoding='utf-8', newline='\n')
    assert run(root).returncode == 0
    updated = index.read_text(encoding='utf-8')
    assert '注目候補3件と利用記録1件' in updated
    assert '2026年6月版の保存ガイド' in updated
    assert '2026年6月版のカバー画像' in updated


def test_newer_published_news_is_preserved_when_report_lags(tmp_path):
    root = fixture(tmp_path)
    report = root / 'public-pages/api/auto_daily_report/latest.json'
    report.write_text(json.dumps({'date': '2026-10-11', 'headlines': []}), encoding='utf-8')
    (root / 'daily-news').mkdir()
    (root / 'daily-news/data.json').write_text(json.dumps({'date': '2026-10-12', 'items': [{'title': 'published'}], 'total': 1}), encoding='utf-8')
    items = [{'title': 'published AI news %d' % n, 'url': 'https://example.com/%d' % n} for n in range(64)]
    (root / 'news/latest.json').write_text(json.dumps({'news_date': '2026-10-12', 'sections': {'AI': items}}), encoding='utf-8')
    assert run(root, '--strict').returncode == 0
    data = json.loads((root / 'news/latest.json').read_text(encoding='utf-8'))
    assert data['news_date'] == '2026-10-12'
    assert len(data['sections']['AI']) == 64
    assert data['sections']['AI'][0]['title'] == 'published AI news 0'
