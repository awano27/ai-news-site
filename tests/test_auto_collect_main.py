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


def test_empty_headline_and_github_sources_exit_before_provider(monkeypatch, tmp_path):
    install_deterministic_pipeline(monkeypatch, tmp_path, headlines=[], github=[])

    def fail_if_provider_is_built(_name):
        pytest.fail("provider must not be constructed for an empty report")

    monkeypatch.setattr(auto_collect_main, "make_provider", fail_if_provider_is_built)

    with pytest.raises(SystemExit) as exc_info:
        auto_collect_main.main()

    assert exc_info.value.code == 1


GOOD_SUMMARIES = {
    "voice": "音声モデルが新たに公開されました",
    "pricing": "画像生成の料金が改定されました",
    "benchmark": "評価指標の改定が発表されました",
    "capacity": "推論基盤の増強が発表されました",
}


class ScriptedProvider:
    available = True
    name = "ollama"
    last_error = ""

    def __init__(self):
        self.config = SimpleNamespace(model="gemma3:4b")

    def chat(self, prompt):
        if "BROKENJSON" in prompt:
            return "not json"
        for key, title in GOOD_SUMMARIES.items():
            if key in prompt:
                return (
                    '{"title_ja":"%s", "summary":"新しいモデルを公開しました。公式サイトで確認できます。", "score":80}'
                    % title
                )
        raise AssertionError("unexpected prompt")


def headline(name, url, source):
    return {
        "name": name,
        "tagline": "English source text",
        "source": source,
        "rss_source": source,
        "links": {"official": url},
    }


def test_main_publishes_after_excluding_one_failed_article(monkeypatch, tmp_path, caplog):
    import json
    from datetime import date

    writes = install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[
            headline("OpenAI ships a voice model", "https://example.com/voice", "Official"),
            headline("Google changes image pricing", "https://example.com/pricing", "Other"),
            headline("MIT revises an evaluation benchmark", "https://example.com/benchmark", "Official"),
            headline("A lab expands inference capacity", "https://example.com/capacity", "Other"),
        ],
        github=[{
            "name": "BROKENJSON owner/tool",
            "url": "https://github.com/owner/broken",
            "tagline": "english only",
            "stars": 10,
        }],
    )
    monkeypatch.setattr(auto_collect_main, "make_provider", lambda _name: ScriptedProvider())
    monkeypatch.setattr(auto_collect_main, "generate_html_report", lambda _path: tmp_path / "report.html")
    monkeypatch.setattr(auto_collect_main, "generate_daily_news", lambda *_args, **_kwargs: tmp_path / "daily.html")
    with caplog.at_level("WARNING"):
        auto_collect_main.main()
    articles, sections = writes[0]
    assert {row["url"] for row in articles} == {
        "https://example.com/voice",
        "https://example.com/pricing",
        "https://example.com/benchmark",
        "https://example.com/capacity",
    }
    assert sections["github_articles"] == []
    assert sections["benchmark_articles"] == []
    assert sections["funding_articles"] == []
    quality = json.loads((tmp_path / "logs" / f"daily_quality_{date.today().isoformat()}.json").read_text(encoding="utf-8"))
    assert quality["status"] == "passed"
    assert quality["article_count"] == 4
    assert quality["excluded_count"] == 1
    assert quality["excluded"][0]["url"] == "https://github.com/owner/broken"
    assert quality["excluded"][0]["errors"]
    assert "Excluded 1/5 articles" in caplog.text


def test_main_holds_publication_when_too_many_articles_fail(monkeypatch, tmp_path):
    import json
    from datetime import date

    writes = install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[
            headline("OpenAI ships a voice model", "https://example.com/voice", "Official"),
            headline("Google changes image pricing", "https://example.com/pricing", "Other"),
            headline("Quantum chip bulletin BROKENJSON", "https://example.com/bad-1", "Official"),
            headline("Robotics vendor note BROKENJSON", "https://example.com/bad-2", "Other"),
            headline("MIT revises an evaluation benchmark", "https://example.com/benchmark", "Official"),
        ],
        github=[],
    )
    monkeypatch.setattr(auto_collect_main, "make_provider", lambda _name: ScriptedProvider())
    with pytest.raises(SystemExit) as exc:
        auto_collect_main.main()
    assert exc.value.code == 1
    assert writes == []
    quality = json.loads((tmp_path / "logs" / f"daily_quality_{date.today().isoformat()}.json").read_text(encoding="utf-8"))
    assert quality["status"] == "failed"
    assert quality["excluded_count"] == 2
    assert quality["failure_reason"] == "japanese_quality_failed"
    assert any("too many excluded" in err for err in quality["errors"])
