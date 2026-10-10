"""End-to-end contract tests for local and deployed daily publication checks."""
from __future__ import annotations

import copy
import functools
import http.server
import json
from pathlib import Path
import subprocess
import sys
import threading

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/check_daily_publication.py'
DATE = '2026-10-09'
ITEM = {'title': '新しい日本語の見出し', 'url': 'https://example.com/news', 'summary': '日本語でニュースの要点を説明します。', 'processing_status': 'llm', 'source': 'Example', 'type': 'news'}


def write_json(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


def refresh_capture(root):
    from scripts.build_search_index import normalize_daily_payload, _daily_rows
    daily = json.loads((root / 'daily-news/data.json').read_text())
    snapshot = normalize_daily_payload(daily)
    write_json(root, f'public-pages/news/daily/{daily["date"]}.json', snapshot)
    write_json(root, 'public-pages/news/search_index.json', _daily_rows(snapshot) + [{'date': '2026-10-08', 'type': 'slide', 'title': '前日のスライド', 'url': '/presentations/day_slides/day_slide_2026_10_08.html'}])


def fixture_site(root):
    item = copy.deepcopy(ITEM)
    quality = {'status': 'passed', 'provider': 'test', 'model': 'test-model', 'article_count': 1, 'japanese_count': 1, 'sources': ['Example']}
    daily = {'date': DATE, 'total': 1, 'news_count': 1, 'items': [item], 'quality': quality}
    report = {'date': DATE, 'total': 1, 'headlines': [item]}
    write_json(root, 'daily-news/data.json', daily)
    write_json(root, 'presentations/auto_daily_report.json', report)
    write_json(root, 'public-pages/api/auto_daily_report/latest.json', report)
    refresh_capture(root)
    html = f'<meta name="report:date" content="{DATE}"><meta name="report:total" content="1"><article class="card"><h2 class="card-title"><a href="{item["url"]}">{item["title"]}</a></h2><div class="card-body">{item["summary"]}</div></article>'
    (root / 'daily-news/index.html').write_text(html, encoding='utf-8')
    (root / 'presentations/auto_daily_report.html').write_text(html.replace('class="card"', 'class="row"').replace('card-title', 'row-title').replace('card-body', 'd-summary'), encoding='utf-8')
    (root / 'index.html').write_text(f'<time id="dailyReportDate">{DATE}</time><time id="dailyNewsDate">{DATE}</time><ol id="dailyHeadlines"><li>{item["title"]}<a href="{item["url"]}">出典</a></li></ol><a href="day_slide_2026_10_08.html">前日のスライド</a>', encoding='utf-8')
    return root


def run_check(root=None, *extra):
    command = [sys.executable, str(SCRIPT), '--date', DATE, *extra]
    if root is not None:
        command += ['--root', str(root)]
    return subprocess.run(command, capture_output=True, text=True)


def change_json(root, path, change):
    data = json.loads((root / path).read_text())
    change(data)
    write_json(root, path, data)


def test_strict_verifier_rejects_a_published_article_that_was_marked_excluded(tmp_path):
    root = fixture_site(tmp_path)
    change_json(root, 'daily-news/data.json', lambda d: d['quality'].update(
        excluded_count=1,
        excluded=[{'index': 9, 'title': '落ちた記事', 'url': ITEM['url'], 'errors': ['fallback or unverified processing']}],
    ))
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'excluded' in (result.stderr + result.stdout).lower()


def test_strict_verifier_accepts_exclusion_metadata_for_articles_that_were_not_published(tmp_path):
    root = fixture_site(tmp_path)
    change_json(root, 'daily-news/data.json', lambda d: d['quality'].update(
        excluded_count=1,
        input_count=2,
        excluded_ratio=0.5,
        excluded=[{'index': 2, 'title': '落ちた記事', 'url': 'https://example.com/dropped', 'errors': ['Japanese summary missing or invalid', 'fallback or unverified processing']}],
    ))
    result = run_check(root, '--require-quality')
    assert result.returncode == 0, result.stderr + result.stdout
    assert 'excluded=0' in result.stdout


def test_complete_linked_publication_passes_with_previous_day_slide(tmp_path):
    result = run_check(fixture_site(tmp_path), '--require-quality')
    assert result.returncode == 0, result.stderr + result.stdout
    assert 'passed' in result.stdout.lower()


@pytest.mark.parametrize(('path', 'change', 'message'), [
    ('daily-news/data.json', lambda d: d.update(date='2026-10-08'), 'date'),
    ('daily-news/data.json', lambda d: d.update(total=2), 'total'),
    ('daily-news/data.json', lambda d: d.pop('quality'), 'quality'),
    ('daily-news/data.json', lambda d: d['quality'].update(status='degraded'), 'quality'),
    ('daily-news/data.json', lambda d: d['quality'].update(article_count=2), 'article_count'),
    ('daily-news/data.json', lambda d: d['items'][0].update(processing_status='fallback'), 'processing_status'),
    ('daily-news/data.json', lambda d: d['items'][0].update(summary='English summary only'), 'Japanese'),
    ('public-pages/news/search_index.json', lambda d: d[0].update(date='2026-10-08'), 'search'),
    ('public-pages/news/search_index.json', lambda d: d[0].update(title='古い記事の見出し'), 'search'),
    (f'public-pages/news/daily/{DATE}.json', lambda d: d.update(total=2), 'snapshot'),
    (f'public-pages/news/daily/{DATE}.json', lambda d: d['items'][0].update(url='https://example.com/missing'), 'snapshot'),
    ('presentations/auto_daily_report.json', lambda d: d['headlines'][0].update(url='https://example.com/absent'), 'headline'),
    ('public-pages/api/auto_daily_report/latest.json', lambda d: d.update(date='2026-10-08'), 'API'),
])
def test_strict_verifier_rejects_false_freshness(tmp_path, path, change, message):
    root = fixture_site(tmp_path)
    change_json(root, path, change)
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert message.lower() in (result.stdout + result.stderr).lower()


def test_generic_structural_check_does_not_claim_legacy_quality(tmp_path):
    root = fixture_site(tmp_path)
    change_json(root, 'daily-news/data.json', lambda d: d.pop('quality'))
    result = run_check(root)
    assert result.returncode == 0, result.stderr
    assert 'not certified' in result.stdout


@pytest.mark.parametrize(('path', 'old', 'new', 'message'), [
    ('daily-news/index.html', 'content="1"', 'content="2"', 'HTML'),
    ('daily-news/index.html', ITEM['url'], 'https://example.com/stale', 'HTML'),
    ('index.html', DATE, '2026-10-08', 'homepage'),
    ('index.html', ITEM['title'], '別の記事', 'homepage'),
])
def test_html_linkage_is_checked(tmp_path, path, old, new, message):
    root = fixture_site(tmp_path)
    target = root / path
    text = target.read_text().replace(old, new)
    # The home contract allows matching top title OR source link; corrupt both.
    if path == 'index.html' and old == ITEM['title']:
        text = text.replace(ITEM['url'], 'https://example.com/stale')
    target.write_text(text)
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert message.lower() in (result.stderr + result.stdout).lower()


def test_remote_verification_compares_content_not_only_dates(tmp_path):
    expected = fixture_site(tmp_path / 'expected')
    live = fixture_site(tmp_path / 'live')
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(live))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f'http://127.0.0.1:{server.server_port}'
        assert run_check(expected, '--base-url', url, '--require-quality').returncode == 0
        for path in ['daily-news/data.json', 'presentations/auto_daily_report.json', 'public-pages/api/auto_daily_report/latest.json', f'public-pages/news/daily/{DATE}.json', 'public-pages/news/search_index.json']:
            target = live / path
            target.write_text(target.read_text().replace(ITEM['title'], '別の日本語見出し'))
        for path in ['index.html', 'daily-news/index.html', 'presentations/auto_daily_report.html']:
            target = live / path
            target.write_text(target.read_text().replace(ITEM['title'], '別の日本語見出し'))
        result = run_check(expected, '--base-url', url, '--require-quality')
        assert result.returncode != 0
        assert 'repository' in (result.stderr + result.stdout).lower()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_snapshot_uses_canonical_unique_counts_not_raw_daily_total(tmp_path):
    root = fixture_site(tmp_path)
    def duplicate(data):
        data['items'].append(dict(data['items'][0], url=ITEM['url'] + '?utm_source=rss'))
        data['total'] = 2
    change_json(root, 'daily-news/data.json', duplicate)
    refresh_capture(root)
    target = root / 'daily-news/index.html'
    target.write_text(target.read_text().replace('content="1"', 'content="2"'))
    result = run_check(root)
    assert result.returncode == 0, result.stderr


def test_quality_source_provenance_must_match_actual_items(tmp_path):
    root = fixture_site(tmp_path)
    change_json(root, 'daily-news/data.json', lambda d: d['quality'].update(sources=['Wrong source']))
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'sources' in result.stderr


def test_quality_japanese_cannot_be_a_token_suffix(tmp_path):
    root = fixture_site(tmp_path)
    change_json(root, 'daily-news/data.json', lambda d: d['items'][0].update(summary='This long English paragraph did not receive Japanese localization. 日本語'))
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'Japanese' in result.stderr


def test_generic_excluded_rows_disclosed_and_strict_exclusion_fails(tmp_path):
    root = fixture_site(tmp_path)
    def unsafe(data):
        data['items'].append(dict(data['items'][0], url='https://example.com/unsafe\\'))
        data['total'] = 2
        data['quality'].update(article_count=2, japanese_count=2)
    change_json(root, 'daily-news/data.json', unsafe)
    refresh_capture(root)
    target = root / 'daily-news/index.html'
    target.write_text(target.read_text().replace('content="1"', 'content="2"') + '<a href="https://example.com/unsafe\\">unsafe</a>')
    result = run_check(root)
    assert result.returncode == 0, result.stderr
    assert 'excluded=1' in result.stdout
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'excluded' in result.stderr


def test_critical_url_probe_includes_binary_assets(tmp_path):
    root = fixture_site(tmp_path)
    for relative in ['about.html', 'contact.html', 'privacy-policy.html', 'credits.html', '404.html', 'ads.txt', 'robots.txt', 'sitemap.xml', 'assets/js/analytics.js', 'assets/hero-planck.jpg', 'assets/og/default.png']:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'\xff\xd8\xff' if relative.endswith(('.jpg', '.png')) else b'content')
    assert run_check(root, '--check-urls').returncode == 0
    (root / 'assets/hero-planck.jpg').unlink()
    result = run_check(root, '--check-urls')
    assert result.returncode != 0
    assert 'hero-planck.jpg' in result.stderr


def test_report_api_count_must_match_report(tmp_path):
    root = fixture_site(tmp_path)
    change_json(root, 'public-pages/api/auto_daily_report/latest.json', lambda d: d.update(total=99))
    result = run_check(root)
    assert result.returncode != 0
    assert 'API' in result.stderr


@pytest.mark.parametrize('path', ['daily-news/index.html', 'presentations/auto_daily_report.html'])
@pytest.mark.parametrize('field', ['title', 'summary'])
def test_strict_checks_rendered_card_content_not_only_json_or_link(tmp_path, path, field):
    root = fixture_site(tmp_path)
    target = root / path
    text = target.read_text().replace(ITEM[field], 'Stale untranslated English content')
    # Expected data hidden in scripts or attributes is not reader-visible content.
    text += f'<script type="application/json">{ITEM[field]}</script><span hidden>{ITEM[field]}</span><div data-search="{ITEM[field]}"></div>'
    target.write_text(text)
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'rendered' in result.stderr


def test_strict_homepage_title_cannot_be_replaced_while_link_stays_correct(tmp_path):
    root = fixture_site(tmp_path)
    target = root / 'index.html'
    target.write_text(target.read_text().replace(ITEM['title'], 'Stale English headline'))
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'homepage' in result.stderr


def test_daily_rendered_summary_accepts_renderer_truncation(tmp_path):
    root = fixture_site(tmp_path)
    full = ITEM['summary'] * 30
    change_json(root, 'daily-news/data.json', lambda d: d['items'][0].update(summary=full))
    refresh_capture(root)
    target = root / 'daily-news/index.html'
    target.write_text(target.read_text().replace(ITEM['summary'], full[:239] + '…'))
    result = run_check(root, '--require-quality')
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('section', ['funding', 'github', 'models'])
def test_strict_verifies_unsafe_urls_in_every_report_section(tmp_path, section):
    root = fixture_site(tmp_path)
    for path in ['presentations/auto_daily_report.json', 'public-pages/api/auto_daily_report/latest.json']:
        change_json(root, path, lambda d: d.update({section: [dict(ITEM, url='javascript:alert(1)', title='English extra', summary='English extra')], 'total': 2}))
    target = root / 'presentations/auto_daily_report.html'
    target.write_text(target.read_text().replace('content="1"', 'content="2"') + '<a href="javascript:alert(1)">English extra</a>')
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'unsafe' in result.stderr


@pytest.mark.parametrize('section', ['funding', 'github', 'models'])
def test_generic_verifies_all_report_api_sections(tmp_path, section):
    root = fixture_site(tmp_path)
    change_json(root, 'public-pages/api/auto_daily_report/latest.json', lambda d: d.update({section: [dict(ITEM, url='https://example.com/extra')]}))
    result = run_check(root)
    assert result.returncode != 0
    assert 'API' in result.stderr


def test_report_total_counts_all_sections(tmp_path):
    root = fixture_site(tmp_path)
    for path in ['presentations/auto_daily_report.json', 'public-pages/api/auto_daily_report/latest.json']:
        change_json(root, path, lambda d: d.update(total=2))
    target = root / 'presentations/auto_daily_report.html'
    target.write_text(target.read_text().replace('content="1"', 'content="2"'))
    result = run_check(root)
    assert result.returncode != 0
    assert 'section' in result.stderr


def add_report_section(root, section, title='org/EnglishModel'):
    item = dict(ITEM, url=f'https://example.com/{section}', title=title, source='HuggingFace Trending' if section == 'models' else 'GitHub Trending')
    for path in ['daily-news/data.json', f'public-pages/news/daily/{DATE}.json']:
        def update(data):
            data['items'].append(dict(item, date=DATE))
            data['total'] = 2
            data['news_count'] = 2
            if 'quality' in data:
                data['quality'].update(article_count=2, japanese_count=2, sources=['Example', item['source']])
        change_json(root, path, update)
    change_json(root, 'public-pages/news/search_index.json', lambda d: d.append(dict(item, date=DATE)))
    for path in ['presentations/auto_daily_report.json', 'public-pages/api/auto_daily_report/latest.json']:
        change_json(root, path, lambda d: d.update({section: [item], 'total': 2}))
    target = root / 'daily-news/index.html'
    target.write_text(target.read_text().replace('content="1"', 'content="2"') + f'<article class="card"><h2 class="card-title"><a href="{item["url"]}">{item["title"]}</a></h2><div class="card-body">{item["summary"]}</div></article>')
    target = root / 'presentations/auto_daily_report.html'
    container, title_class, summary_class = {'github': ('gh', 'gh-name', 'gh-desc'), 'models': ('mdl', 'gh-name', 'mdl-summary'), 'funding': ('row', 'row-title', 'd-summary')}[section]
    target.write_text(target.read_text().replace('content="1"', 'content="2"') + f'<div class="{container}"><span class="{title_class}"><a href="{item["url"]}">{item["title"]}</a></span><div class="{summary_class}">{item["summary"]}</div></div>')
    refresh_capture(root)
    return item


@pytest.mark.parametrize('section', ['github', 'models'])
def test_report_proper_names_allowed_but_rendered_summary_must_be_japanese(tmp_path, section):
    root = fixture_site(tmp_path)
    item = add_report_section(root, section)
    result = run_check(root, '--require-quality')
    assert result.returncode == 0, result.stderr
    target = root / 'presentations/auto_daily_report.html'
    # Corrupt only the secondary section, retaining the correct first headline.
    text = target.read_text()
    split = text.rfind(item['summary'])
    target.write_text(text[:split] + text[split:].replace(item['summary'], 'Stale English summary', 1))
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'rendered' in result.stderr


@pytest.mark.parametrize('section', ['funding', 'github', 'models'])
def test_every_report_section_must_exist_in_daily_and_search(tmp_path, section):
    root = fixture_site(tmp_path)
    for path in ['presentations/auto_daily_report.json', 'public-pages/api/auto_daily_report/latest.json']:
        change_json(root, path, lambda d: d.update({section: [dict(ITEM, url='https://example.com/absent')], 'total': 2}))
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert 'absent' in result.stderr


def test_next_day_real_formatter_renderer_search_homepage_strict_end_to_end(tmp_path, monkeypatch):
    """A new edition must cross real serialization boundaries, not only fixtures."""
    from datetime import date
    import shutil
    from scripts.sync_daily_search import sync_daily_search
    from src.auto_collect import daily_news_page
    from src.auto_collect.formatter import DayFileFormatter
    from src.auto_collect.html_report_parser import parse_daily_txt
    from src.auto_collect.html_report_renderer import generate_html
    from src.auto_collect.quality import validate_articles

    repo = tmp_path / 'repo'
    repo.mkdir()
    source_root = SCRIPT.parents[1]
    (repo / 'scripts').mkdir()
    shutil.copy(source_root / 'scripts/build-homepage-latest.js', repo / 'scripts')
    shutil.copy(source_root / 'index.html', repo / 'index.html')
    write_json(repo, 'public-pages/news/archive_index.json', [{'date': DATE, 'count': 150}])
    write_json(repo, 'public-pages/news/search_index.json', [])
    slide = repo / 'presentations/day_slides/day_slide_2026_10_09.html'
    slide.parent.mkdir(parents=True)
    slide.write_text('<title>前日の独立したスライド</title><meta name="description" content="前日のスライドです。"><h1>前日の独立したスライド</h1>')
    day = date(2026, 10, 10)
    def article(title, url, source):
        return dict(ITEM, title=title, url=url, source=source, category='Product', score=80, evidence={})
    headline = article('翌日の新しい技術ニュース', 'https://example.com/new-day', 'Official')
    funding = article('企業が新しい投資の取り組みを発表', 'https://example.com/business', 'Business')
    github = article('owner/tool', 'https://github.com/owner/tool', 'GitHub Trending')
    model = article('owner/model', 'https://huggingface.co/owner/model', 'HuggingFace Trending')
    items = [headline, funding, github, model]
    quality = dict(validate_articles(items, min_articles=3, min_sources=2), provider='test', model='test-model')
    assert quality['status'] == 'passed'
    transport = repo / 'input/day/1010.txt'
    DayFileFormatter().write([headline], transport, day, github_articles=[github], benchmark_articles=[model], funding_articles=[funding])
    parsed = parse_daily_txt(transport)
    html, report = generate_html(parsed, repo / 'presentations/daily_reports', 'https://example.com/og.png')
    assert report['total'] == 4
    write_json(repo, 'presentations/auto_daily_report.json', report)
    write_json(repo, 'public-pages/api/auto_daily_report/latest.json', report)
    (repo / 'presentations/auto_daily_report.html').write_text(html)
    monkeypatch.setattr(daily_news_page, 'DAILY_NEWS_DIR', repo / 'daily-news')
    monkeypatch.setattr(daily_news_page, 'ARCHIVE_DIR', repo / 'daily-news/archive')
    daily_news_page.generate_daily_news(day, [headline], github_articles=[github], benchmark_articles=[model], funding_articles=[funding], quality=quality)
    sync_daily_search(repo)
    build = subprocess.run(['node', str(repo / 'scripts/build-homepage-latest.js')], capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(repo), '--date', day.isoformat(), '--require-quality'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '2026-10-10' in result.stdout and '4 daily items' in result.stdout
    assert '<time id="dailyNewsDate">2026-10-10</time>' in (repo / 'index.html').read_text()


def test_failed_articles_are_omitted_and_strict_publication_still_passes(tmp_path, monkeypatch):
    """Kept articles must satisfy --require-quality; exclusions stay in quality metadata."""
    from datetime import date
    import shutil
    from scripts.sync_daily_search import sync_daily_search
    from src.auto_collect import daily_news_page
    from src.auto_collect.formatter import DayFileFormatter
    from src.auto_collect.html_report_parser import parse_daily_txt
    from src.auto_collect.html_report_renderer import generate_html
    from src.auto_collect.quality import filter_publishable

    repo = tmp_path / 'repo'
    repo.mkdir()
    source_root = SCRIPT.parents[1]
    (repo / 'scripts').mkdir()
    shutil.copy(source_root / 'scripts/build-homepage-latest.js', repo / 'scripts')
    shutil.copy(source_root / 'index.html', repo / 'index.html')
    write_json(repo, 'public-pages/news/archive_index.json', [{'date': DATE, 'count': 150}])
    write_json(repo, 'public-pages/news/search_index.json', [])
    slide = repo / 'presentations/day_slides/day_slide_2026_10_09.html'
    slide.parent.mkdir(parents=True)
    slide.write_text('<title>前日の独立したスライド</title><meta name="description" content="前日のスライドです。"><h1>前日の独立したスライド</h1>')
    day = date(2026, 10, 10)
    summary = '日本語でニュースの要点を説明します。'
    def good(title, url, source):
        return dict(ITEM, title=title, url=url, source=source, summary=summary, category='Product', score=80, evidence={}, published_at='2026-10-10')
    rows = [
        good('翌日の新しい技術ニュース', 'https://example.com/new-day', 'Official'),
        good('別の研究チームが評価を公開', 'https://example.com/research', 'Other'),
        good('開発者が試せる新しい道具', 'https://example.com/tool-news', 'Official'),
        good('国内向けの推論サービスが開始', 'https://example.com/service', 'Other'),
        good('画像モデルの更新点が判明', 'https://example.com/image', 'Official'),
        good('音声認識の精度が改善', 'https://example.com/speech', 'Other'),
        good('小型モデルが端末で動く', 'https://example.com/edge', 'Official'),
        good('企業が導入手順を公開', 'https://example.com/rollout', 'Other'),
        dict(ITEM, title='Broken one', url='https://example.com/bad-1', source='Official', summary='English fallback', processing_status='fallback', processing_error='invalid_japanese'),
        dict(ITEM, title='Broken two', url='https://example.com/bad-2', source='Other', summary='English fallback', processing_status='fallback', processing_error='invalid_japanese'),
    ]
    kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'passed' and quality['excluded_count'] == 2
    quality = dict(quality, provider='test', model='test-model', date=day.isoformat())
    transport = repo / 'input/day/1010.txt'
    DayFileFormatter().write(kept, transport, day)
    parsed = parse_daily_txt(transport)
    html, report = generate_html(parsed, repo / 'presentations/daily_reports', 'https://example.com/og.png')
    assert report['total'] == 8
    assert all(item['url'] not in {'https://example.com/bad-1', 'https://example.com/bad-2'} for item in report['headlines'])
    write_json(repo, 'presentations/auto_daily_report.json', report)
    write_json(repo, 'public-pages/api/auto_daily_report/latest.json', report)
    (repo / 'presentations/auto_daily_report.html').write_text(html)
    monkeypatch.setattr(daily_news_page, 'DAILY_NEWS_DIR', repo / 'daily-news')
    monkeypatch.setattr(daily_news_page, 'ARCHIVE_DIR', repo / 'daily-news/archive')
    daily_news_page.generate_daily_news(day, kept, quality=quality)
    sync_daily_search(repo)
    build = subprocess.run(['node', str(repo / 'scripts/build-homepage-latest.js')], capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(repo), '--date', day.isoformat(), '--require-quality'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'excluded=0' in result.stdout
    published = json.loads((repo / 'daily-news/data.json').read_text(encoding='utf-8'))
    assert published['quality']['article_count'] == 8
    assert published['quality']['excluded_count'] == 2
    assert {row['url'] for row in published['quality']['excluded']} == {'https://example.com/bad-1', 'https://example.com/bad-2'}
    assert all(item['url'] not in {'https://example.com/bad-1', 'https://example.com/bad-2'} for item in published['items'])
    assert all(item.get('processing_status') in {'llm', 'source_japanese'} for item in published['items'])


@pytest.mark.parametrize('field,value', [('summary', 'Stale English summary'), ('source', 'Wrong source'), ('category', 'Wrong category'), ('published_at', '2020-01-01')])
@pytest.mark.parametrize('target', ['snapshot', 'search'])
def test_strict_rejects_stale_capture_metadata_even_with_correct_url_and_title(tmp_path, target, field, value):
    root = fixture_site(tmp_path)
    path = f'public-pages/news/daily/{DATE}.json' if target == 'snapshot' else 'public-pages/news/search_index.json'
    def stale(data):
        rows = data['items'] if target == 'snapshot' else data
        rows[0][field] = value
    change_json(root, path, stale)
    result = run_check(root, '--require-quality')
    assert result.returncode != 0
    assert target in result.stderr


@pytest.mark.parametrize('target', ['snapshot', 'search'])
def test_remote_strict_rejects_stale_capture_summary_against_repository(tmp_path, target):
    root = fixture_site(tmp_path)
    path = f'public-pages/news/daily/{DATE}.json' if target == 'snapshot' else 'public-pages/news/search_index.json'
    change_json(root, path, lambda d: (d['items'] if target == 'snapshot' else d)[0].update(summary='Stale English summary'))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = run_check(root, '--base-url', f'http://127.0.0.1:{server.server_port}', '--require-quality')
        assert result.returncode != 0
        assert target in result.stderr
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
