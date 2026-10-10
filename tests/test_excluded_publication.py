"""Excluded articles stay out of the published edition and the strict check still passes."""
from datetime import date
from pathlib import Path
import json
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from src.auto_collect import daily_news_page, html_report, html_report_archive, ogp_generator
from src.auto_collect import main as auto_collect_main

WORKSPACE = Path(__file__).resolve().parents[1]
SUMMARY = '新しい言語モデルを公開しました。開発者は公式資料を確認できます。'
TODAY = date.today().isoformat()


GOOD = [
    ('quartz', '石英の結晶欠陥を測る手順が研究所から出た', 'Alpha Desk', 99),
    ('badger', '穴熊の生態を追跡する小型端末が動き始めた', 'Alpha Desk', 70),
    ('violin', '提琴の音色を分類する実験結果がまとまった', 'Alpha Desk', 70),
    ('cactus', '多肉植物の灌水を制御する装置が加わった', 'Alpha Desk', 70),
    ('nebula', '星雲の写真を解析する手法が公開された', 'Beta Desk', 70),
    ('kettle', '薬缶の温度を保つ家庭向け機能が届いた', 'Beta Desk', 70),
    ('orchid', '蘭の開花を予測する観測が始まった', 'Beta Desk', 70),
    ('piston', '活塞の摩耗を検知する計測が進んだ', 'Beta Desk', 70),
    ('glacier', '氷河の後退を記録する調査が報告された', 'Beta Desk', 70),
]
BAD_HEADLINE = ('anvil', '金床の硬さを比べる速報が届いた', 'Alpha Desk')
BAD_GITHUB = ('zephyr', '西風の観測装置', 'GitHub Trending')


def _raw(name):
    return {
        'name': name,
        'tagline': f'{name} source text',
        'source': 'Collector',
        'links': {'official': f'https://{name}.example/story'},
    }


def _published(name, title, source, score, *, ok):
    return {
        'title': title,
        'summary': SUMMARY if ok else 'English fallback that must not publish',
        'url': f'https://{name}.example/story',
        'source': source,
        'category': 'Product',
        'score': score,
        'tldr': '要点だけを先に示す',
        'processing_status': 'llm' if ok else 'fallback',
        'processing_error': '' if ok else 'invalid_japanese',
        'published_at': TODAY,
        'date': TODAY,
        'evidence': {},
    }


class ScriptedProcessor:
    available = True
    provider = SimpleNamespace(config=SimpleNamespace(model='test-model'), last_error='')

    def process_batch(self, articles):
        by_name = {name: _published(name, title, source, score, ok=True) for name, title, source, score in GOOD}
        bad_name, bad_title, bad_source = BAD_HEADLINE
        by_name[bad_name] = _published(bad_name, bad_title, bad_source, 10, ok=False)
        return [by_name[article['name']] for article in articles]

    def process_github_repos(self, repos):
        name, title, source = BAD_GITHUB
        return [_published(name, title, source, 10, ok=False) for _repo in repos]

    def process_benchmarks(self, _rows):
        return []

    def process_funding(self, _rows):
        return []


def test_excluded_articles_are_omitted_and_strict_publication_check_passes(monkeypatch, tmp_path):
    repo = tmp_path / 'repo'
    (repo / 'scripts').mkdir(parents=True)
    (repo / 'presentations' / 'daily_reports').mkdir(parents=True)
    shutil.copy(WORKSPACE / 'index.html', repo / 'index.html')
    shutil.copy(WORKSPACE / 'scripts' / 'build-homepage-latest.js', repo / 'scripts' / 'build-homepage-latest.js')

    monkeypatch.setattr(auto_collect_main, 'setup_logging', lambda: None)
    monkeypatch.setattr(auto_collect_main, 'parse_args', lambda: SimpleNamespace(provider='ollama', force=True))
    monkeypatch.setattr(auto_collect_main, 'PROJECT_ROOT', repo)
    monkeypatch.setattr(auto_collect_main, 'INPUT_DAY_DIR', repo / 'input' / 'day')
    monkeypatch.setattr(auto_collect_main, 'LOG_DIR', repo / 'logs')
    monkeypatch.setattr(auto_collect_main, 'build_processor', lambda _name: ScriptedProcessor())
    monkeypatch.setattr(auto_collect_main, 'RSSAutoCollector', lambda: _Collector([_raw(name) for name, *_rest in GOOD] + [_raw(BAD_HEADLINE[0])]))
    for collector_name in ('HNAutoCollector', 'JPCollector', 'ArxivCollector', 'XBookmarksCollector', 'BenchmarkCollector', 'FundingCollector'):
        monkeypatch.setattr(auto_collect_main, collector_name, lambda: _Collector([]))
    monkeypatch.setattr(auto_collect_main, 'GitHubTrendingCollector', lambda: _Collector([_raw(BAD_GITHUB[0])]))
    monkeypatch.setattr(ogp_generator, 'render', lambda *_args, **_kwargs: None)

    monkeypatch.setattr(html_report, 'OUTPUT_PATH', repo / 'presentations' / 'auto_daily_report.html')
    monkeypatch.setattr(html_report, 'JSON_OUTPUT_PATH', repo / 'presentations' / 'auto_daily_report.json')
    monkeypatch.setattr(html_report, 'PUBLIC_API_DIR', repo / 'public-pages' / 'api' / 'auto_daily_report')
    archive = repo / 'presentations' / 'daily_reports'
    monkeypatch.setattr(html_report, 'ARCHIVE_DIR', archive)
    monkeypatch.setattr(html_report_archive, 'ARCHIVE_DIR', archive)
    monkeypatch.setattr(html_report_archive, 'ARCHIVE_INDEX_PATH', archive / 'index.json')
    monkeypatch.setattr(html_report_archive, 'SEARCHABLE_INDEX_PATH', archive / 'searchable.json')
    monkeypatch.setattr(daily_news_page, 'DAILY_NEWS_DIR', repo / 'daily-news')
    monkeypatch.setattr(daily_news_page, 'ARCHIVE_DIR', repo / 'daily-news' / 'archive')

    outputs = []
    real_run = subprocess.run

    def run(command, cwd=None, check=False, timeout=None, **_ignored):
        cmd = list(command)
        script_cwd = repo
        if cmd and cmd[0] == sys.executable:
            cmd[1] = str(WORKSPACE / 'scripts' / Path(cmd[1]).name)
            script_cwd = WORKSPACE
        completed = real_run(cmd, cwd=script_cwd, check=False, timeout=timeout, capture_output=True, text=True)
        outputs.append(completed)
        if check and completed.returncode != 0:
            raise subprocess.CalledProcessError(completed.returncode, cmd, completed.stdout, completed.stderr)
        return completed

    monkeypatch.setattr(auto_collect_main.subprocess, 'run', run)
    auto_collect_main.main()

    data = json.loads((repo / 'daily-news' / 'data.json').read_text(encoding='utf-8'))
    excluded_urls = {row['url'] for row in data['quality']['excluded']}
    published_urls = {item['url'] for item in data['items']}
    assert excluded_urls == {f'https://{BAD_HEADLINE[0]}.example/story', f'https://{BAD_GITHUB[0]}.example/story'}
    assert published_urls.isdisjoint(excluded_urls)
    articles = [item for item in data['items'] if item.get('type') != 'x']
    assert data['quality']['status'] == 'passed'
    assert data['quality']['article_count'] == len(articles)
    assert data['quality']['japanese_count'] == len(articles)
    assert sorted(data['quality']['sources']) == sorted({item['source'] for item in articles})
    report = json.loads((repo / 'presentations' / 'auto_daily_report.json').read_text(encoding='utf-8'))
    report_urls = {item['url'] for rows in (report.get('headlines'), report.get('funding'), report.get('github'), report.get('models')) for item in rows or []}
    assert report_urls.isdisjoint(excluded_urls)
    day_file = (repo / 'input' / 'day' / f"{date.today().strftime('%m%d')}.txt").read_text(encoding='utf-8')
    for url in excluded_urls:
        assert url not in day_file
    quality_log = json.loads(next((repo / 'logs').glob('daily_quality_*.json')).read_text(encoding='utf-8'))
    assert {row['url'] for row in quality_log['excluded']} == excluded_urls
    assert outputs[-1].returncode == 0, outputs[-1].stdout + outputs[-1].stderr
    assert 'quality and content passed' in outputs[-1].stdout


class _Collector:
    def __init__(self, items):
        self.items = items

    def collect(self, _today):
        return self.items
