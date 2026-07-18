from types import SimpleNamespace

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


def test_unavailable_nvidia_uses_heuristic_fallback(monkeypatch, tmp_path):
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

    auto_collect_main.main()

    assert len(writes) == 1
    headline_items, _sections = writes[0]
    assert headline_items[0]["title"] == "New GPT model released"
    assert headline_items[0]["score"] == 60


def test_empty_headline_and_github_sources_exit_before_provider(monkeypatch, tmp_path):
    install_deterministic_pipeline(monkeypatch, tmp_path, headlines=[], github=[])

    def fail_if_provider_is_built(_name):
        pytest.fail("provider must not be constructed for an empty report")

    monkeypatch.setattr(auto_collect_main, "make_provider", fail_if_provider_is_built)

    with pytest.raises(SystemExit) as exc_info:
        auto_collect_main.main()

    assert exc_info.value.code == 1
