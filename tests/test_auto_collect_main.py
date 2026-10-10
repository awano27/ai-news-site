from types import SimpleNamespace
import logging

import pytest

from src.auto_collect import main as auto_collect_main


class StaticCollector:
    def __init__(self, items):
        self.items = items

    def collect(self, _today):
        return self.items


class UnavailableNvidiaProvider:
    name = "nvidia"
    available = False

    def chat(self, _prompt):
        raise AssertionError("unavailable provider must not be called")


def install_deterministic_pipeline(monkeypatch, tmp_path, *, headlines, github):
    """Replace collection and rendering boundaries with deterministic fakes."""
    monkeypatch.setattr(auto_collect_main, "setup_logging", lambda: None)
    monkeypatch.setattr(
        auto_collect_main,
        "parse_args",
        lambda: SimpleNamespace(provider="nvidia", force=True),
    )
    monkeypatch.setattr(auto_collect_main, "INPUT_DAY_DIR", tmp_path)
    monkeypatch.setattr(auto_collect_main, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(auto_collect_main, "LOG_DIR", tmp_path / "logs")

    monkeypatch.setattr(
        auto_collect_main, "RSSAutoCollector", lambda: StaticCollector(headlines)
    )
    for collector_name in (
        "HNAutoCollector",
        "JPCollector",
        "ArxivCollector",
        "XBookmarksCollector",
        "BenchmarkCollector",
        "FundingCollector",
    ):
        monkeypatch.setattr(
            auto_collect_main, collector_name, lambda: StaticCollector([])
        )
    monkeypatch.setattr(
        auto_collect_main, "GitHubTrendingCollector", lambda: StaticCollector(github)
    )

    captured_writes = []

    class CapturingFormatter:
        def write(self, articles, _output_path, _today, **sections):
            captured_writes.append((articles, sections))

    monkeypatch.setattr(auto_collect_main, "DayFileFormatter", CapturingFormatter)
    monkeypatch.setattr(auto_collect_main, "generate_html_report", lambda _path: None)
    monkeypatch.setattr(auto_collect_main, "generate_daily_news", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(auto_collect_main.subprocess, "run", lambda *_args, **_kwargs: None)
    return captured_writes


def test_unavailable_nvidia_blocks_before_any_public_output(monkeypatch, tmp_path):
    writes = install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[
            {
                "name": "New GPT model released",
                "tagline": "A deterministic fallback item",
                "source_rank": 1,
                "links": {"official": "https://example.com/official"},
            }
        ],
        github=[],
    )
    monkeypatch.setattr(
        auto_collect_main, "make_provider", lambda _name: UnavailableNvidiaProvider()
    )

    with pytest.raises(SystemExit) as exc:
        auto_collect_main.main()
    assert exc.value.code == 1
    assert writes == []
    assert list((tmp_path / "logs").glob("daily_quality_*.json"))
    assert list((tmp_path / "logs").glob("daily_candidate_*.json"))


def test_too_many_failed_articles_hold_publication_before_any_write(monkeypatch, tmp_path, caplog):
    headlines = []
    names = ['quartz', 'badger', 'violin', 'cactus', 'nebula']
    for name in names:
        headlines.append({
            'name': name,
            'tagline': 'English source text',
            'source': 'OnlyOne',
            'links': {'official': f'https://{name}.example/story'},
        })
    writes = install_deterministic_pipeline(monkeypatch, tmp_path, headlines=headlines, github=[])

    class Processor:
        available = True
        provider = SimpleNamespace(config=SimpleNamespace(model='test-model'))

        def process_batch(self, articles):
            titles = {
                'quartz': '石英の結晶欠陥を測る手順が研究所から出た',
                'badger': '穴熊の生態を追跡する小型端末が動き始めた',
                'violin': '提琴の音色を分類する実験結果がまとまった',
                'cactus': '多肉植物の灌水を制御する装置が加わった',
                'nebula': '星雲の写真を解析する手法が公開された',
            }
            rendered = []
            for index, article in enumerate(articles):
                rendered.append({
                    'title': titles[article['name']],
                    'summary': '新しい言語モデルを公開しました。開発者は公式資料を確認できます。' if index == 0 else 'English fallback',
                    'url': article['links']['official'],
                    'source': 'OnlyOne',
                    'processing_status': 'llm' if index == 0 else 'fallback',
                    'processing_error': 'invalid_japanese',
                })
            return rendered

        def process_github_repos(self, _repos):
            return []

        def process_benchmarks(self, _rows):
            return []

        def process_funding(self, _rows):
            return []

    monkeypatch.setattr(auto_collect_main, 'build_processor', lambda _name: Processor())
    with caplog.at_level(logging.WARNING, logger='auto_collect'):
        with pytest.raises(SystemExit) as exc:
            auto_collect_main.main()
    assert exc.value.code == 1
    assert writes == []
    assert 'Excluded 4/5 articles' in caplog.text
    quality = next((tmp_path / 'logs').glob('daily_quality_*.json')).read_text(encoding='utf-8')
    assert 'https://badger.example/story' in quality
    assert '"status": "failed"' in quality


def test_empty_headline_and_github_sources_exit_before_provider(monkeypatch, tmp_path):
    install_deterministic_pipeline(monkeypatch, tmp_path, headlines=[], github=[])

    def fail_if_provider_is_built(_name):
        pytest.fail("provider must not be constructed for an empty report")

    monkeypatch.setattr(auto_collect_main, "make_provider", fail_if_provider_is_built)

    with pytest.raises(SystemExit) as exc_info:
        auto_collect_main.main()

    assert exc_info.value.code == 1
