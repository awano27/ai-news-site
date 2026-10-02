from pathlib import Path
import subprocess
import shutil

from scripts import public_html, check_analytics_coverage as coverage
from scripts.check_analytics_config import classify_measurement_id

ROOT = Path(__file__).resolve().parents[1]


def test_shared_inventory_covers_major_paths(tmp_path, monkeypatch):
    for name in ('index.html', 'daily-news/index.html', 'articles/claim-evidence-design.html',
                 'presentations/comparison.html', 'presentations/day_slides/slide.html'):
        file = tmp_path / name; file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('<head></head>', encoding='utf-8')
    monkeypatch.setattr(coverage, 'ROOT', tmp_path)
    assert len(public_html.public_html_files(tmp_path)) == 5
    assert coverage.main() is True
    for file in public_html.public_html_files(tmp_path):
        content = public_html.ensure_analytics(file.read_text(encoding='utf-8'))
        assert public_html.ensure_analytics(content) == content
        file.write_text(content, encoding='utf-8')
    assert coverage.main() is False


def test_comments_are_not_tags_and_redirects_have_reason():
    assert not public_html.analytics_present('<!-- <script src="/assets/js/analytics.js"></script> -->')
    assert public_html.exclusion_reason(Path('redirect.html'), '<meta content="0;url=/" http-equiv="refresh">') == 'meta-refresh redirect'
    assert not classify_measurement_id('G-REPLACE_ME')[0]
    assert not classify_measurement_id(None)[0]
    assert not classify_measurement_id('G-XXXXXX')[0]
    assert classify_measurement_id('G-LOCAL123')[0]


def test_design_source_and_render_preserve_tag():
    from scripts.render_claim_evidence import render_static_page
    source = (ROOT / 'articles/claim-evidence-design.html').read_text(encoding='utf-8')
    output, errors = render_static_page(source)
    assert not errors
    assert public_html.analytics_present(output)


def test_all_public_generation_templates_keep_analytics_tag():
    from src.generators.ranking_template import get_template_string
    assert public_html.analytics_present(get_template_string())
    for name in ('monthly_report', 'daily_slide', 'day_news_slide', 'daily_slide_index',
                 'day_slides_index', 'index'):
        assert public_html.analytics_present((ROOT / 'templates' / (name + '.html')).read_text(encoding='utf-8'))


def test_mocked_browser_events_and_privacy_guards():
    node = shutil.which('node')
    assert node, 'Node is required for offline analytics verification'
    result = subprocess.run([node, str(ROOT / 'tests/verify_analytics_events.cjs')],
                            capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stdout + result.stderr
