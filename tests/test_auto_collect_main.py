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


X_SUMMARY = "新しい言語モデルの発表を紹介しています。研究者は公式資料を確認できます。"
LUNCH_SUMMARY = "昼ごはんの写真が共有されています。食事の様子が写っています。"


def bookmark(name, url, body, author):
    return {
        "name": name,
        "description": body,
        "tagline": body[:80],
        "rss_source": f"X (@{author})",
        "source": "X",
        "url": url,
        "links": {"official": url},
        "x_curated": True,
        "x_tweet_id": url.rsplit("/", 1)[-1],
        "bookmark_date": "2026-10-12",
        "authors": f"@{author}",
    }


class XAwareProvider(ScriptedProvider):
    def chat(self, prompt):
        if "NOTAI lunch" in prompt:
            return (
                '{"title_ja":"昼ごはんの写真","summary":"%s","ai_related":false}'
                % LUNCH_SUMMARY
            )
        if "BROKENX" in prompt:
            return "not json"
        if "AI model launch" in prompt:
            return (
                '{"title_ja":"新しいモデルの発表","summary":"%s","ai_related":true}'
                % X_SUMMARY
            )
        extra = {
            "chip": "推論チップが新たに発表されました",
            "agent": "業務エージェントが公開されました",
            "dataset": "学習データセットが更新されました",
            "policy": "モデル利用方針が改訂されました",
        }
        for key, title in extra.items():
            if key in prompt:
                return (
                    '{"title_ja":"%s", "summary":"新しいモデルを公開しました。公式サイトで確認できます。", "score":80}'
                    % title
                )
        return super().chat(prompt)


def test_main_summarizes_x_posts_and_drops_failed_or_unrelated_ones(monkeypatch, tmp_path):
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
            headline("A vendor announces an inference chip", "https://example.com/chip", "Official"),
            headline("A studio releases a coding agent", "https://example.com/agent", "Other"),
            headline("A lab refreshes a training dataset", "https://example.com/dataset", "Official"),
            headline("A company revises model policy", "https://example.com/policy", "Other"),
        ],
        github=[],
    )
    posts = [
        bookmark("AI model launch thread", "https://x.com/lab/status/1", "AI model launch details", "lab"),
        bookmark("Lunch photo", "https://x.com/cafe/status/2", "NOTAI lunch photo", "cafe"),
        bookmark("BROKENX vendor note", "https://x.com/vendor/status/3", "BROKENX vendor note", "vendor"),
    ]
    monkeypatch.setattr(auto_collect_main, "XBookmarksCollector", lambda: StaticCollector(posts))
    monkeypatch.setattr(auto_collect_main, "make_provider", lambda _name: XAwareProvider())
    monkeypatch.setattr(auto_collect_main, "generate_html_report", lambda _path: tmp_path / "report.html")
    captured = {}

    def capture_daily(*_args, **kwargs):
        captured.update(kwargs)
        return tmp_path / "daily.html"

    monkeypatch.setattr(auto_collect_main, "generate_daily_news", capture_daily)
    auto_collect_main.main()

    published = captured["x_articles"]
    assert [row["url"] for row in published] == ["https://x.com/lab/status/1"]
    assert published[0]["processing_status"] == "llm"
    assert published[0]["ai_related"] is True
    assert X_SUMMARY in published[0]["summary"]
    dayfile_urls = {row["url"] for row in writes[0][0]}
    assert "https://x.com/lab/status/1" not in dayfile_urls
    quality = captured["quality"]
    assert quality["status"] == "passed"
    assert quality["input_count"] == 11
    assert quality["article_count"] == 9
    assert quality["japanese_count"] == 9
    assert quality["excluded_count"] == 2
    assert "X (@lab)" in quality["sources"]
    by_url = {row["url"]: row["errors"] for row in quality["excluded"]}
    assert by_url["https://x.com/cafe/status/2"] == ["not AI-related"]
    assert "fallback or unverified processing" in by_url["https://x.com/vendor/status/3"]
    assert "Japanese summary missing or invalid" in by_url["https://x.com/vendor/status/3"]
    logged = json.loads((tmp_path / "logs" / f"daily_quality_{date.today().isoformat()}.json").read_text(encoding="utf-8"))
    assert logged["excluded_count"] == 2
    assert {row["url"] for row in logged["excluded"]} == set(by_url)
    assert captured["x_authoritative"] is True


def test_missing_x_vault_is_not_authoritative(tmp_path):
    from datetime import date
    from src.auto_collect.collectors.x_bookmarks import XBookmarksCollector

    collector = XBookmarksCollector(bookmarks_dir=tmp_path / "missing-vault")
    assert collector.collect(date.today()) == []
    assert collector.vault_available is False


def test_x_only_collection_reaches_the_shared_quality_gate(monkeypatch, tmp_path):
    import json
    from datetime import date

    install_deterministic_pipeline(monkeypatch, tmp_path, headlines=[], github=[])
    posts = [
        bookmark("model one", "https://x.com/lab/status/1", "first model note", "lab"),
        bookmark("model two", "https://x.com/lab/status/2", "second model note", "lab"),
        bookmark("model three", "https://x.com/other/status/3", "third model note", "other"),
    ]

    class ReadyVault(StaticCollector):
        vault_available = True

        def collect(self, today):
            return posts

    monkeypatch.setattr(auto_collect_main, "XBookmarksCollector", lambda: ReadyVault(posts))

    class AcceptingProvider(ScriptedProvider):
        def chat(self, _prompt):
            return (
                '{"title_ja":"新しいモデルの発表","summary":"%s","ai_related":true}'
                % X_SUMMARY
            )

    monkeypatch.setattr(auto_collect_main, "make_provider", lambda _name: AcceptingProvider())
    monkeypatch.setattr(auto_collect_main, "generate_html_report", lambda _path: tmp_path / "report.html")
    captured = {}

    def capture_daily(*_args, **kwargs):
        captured.update(kwargs)
        return tmp_path / "daily.html"

    monkeypatch.setattr(auto_collect_main, "generate_daily_news", capture_daily)
    auto_collect_main.main()
    quality = json.loads((tmp_path / "logs" / f"daily_quality_{date.today().isoformat()}.json").read_text(encoding="utf-8"))
    assert quality["status"] == "passed"
    assert quality.get("failure_reason") != "collection_unavailable"
    assert quality["article_count"] == 3
    assert quality["input_count"] == 3
    assert sorted(quality["sources"]) == ["X (@lab)", "X (@other)"]
    assert {row["url"] for row in captured["x_articles"]} == {post["url"] for post in posts}
    assert captured["x_authoritative"] is True


def test_main_leaves_stale_articles_out_of_the_quality_gate(monkeypatch, tmp_path):
    import json
    from datetime import date, timedelta

    today = date.today()
    stale_day = (today - timedelta(days=3)).isoformat()
    install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[
            headline("OpenAI ships a voice model", "https://example.com/voice", "Official"),
            headline("Google changes image pricing", "https://example.com/pricing", "Other"),
            headline("MIT revises an evaluation benchmark", "https://example.com/benchmark", "Official"),
            dict(headline("A lab expands inference capacity", "https://example.com/old-capacity", "Other"), date=stale_day),
        ],
        github=[],
    )
    monkeypatch.setattr(auto_collect_main, "make_provider", lambda _name: ScriptedProvider())
    monkeypatch.setattr(auto_collect_main, "generate_html_report", lambda _path: tmp_path / "report.html")
    captured = {}

    def capture_daily(*_args, **kwargs):
        captured.update(kwargs)
        return tmp_path / "daily.html"

    monkeypatch.setattr(auto_collect_main, "generate_daily_news", capture_daily)
    auto_collect_main.main()
    quality = captured["quality"]
    assert quality["status"] == "passed"
    assert quality["input_count"] == 3
    assert quality["article_count"] == 3
    assert quality["excluded_count"] == 0
    published = {row["url"] for row in captured["articles"]}
    assert "https://example.com/old-capacity" not in published
    logged = json.loads((tmp_path / "logs" / f"daily_quality_{today.isoformat()}.json").read_text(encoding="utf-8"))
    assert logged["article_count"] == 3


def test_main_keeps_x_bookmarks_outside_the_news_date_window(monkeypatch, tmp_path, caplog):
    import logging
    from datetime import date, timedelta

    real_date = date

    class FrozenDate(real_date):
        @classmethod
        def today(cls):
            return real_date(2026, 10, 15)

    monkeypatch.setattr(auto_collect_main, "date", FrozenDate)
    posts = [
        bookmark(f"AI model launch {i}", f"https://x.com/lab/status/{i}", "AI model launch details", "lab")
        for i in range(19)
    ]
    for post in posts:
        post["bookmark_date"] = "2026-10-13"
    install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[
            dict(headline("OpenAI ships a voice model", "https://example.com/voice", "Official"), date="2026-10-15"),
            dict(headline("Google changes image pricing", "https://example.com/pricing", "Other"), date="2026-10-14"),
            dict(headline("MIT revises an evaluation benchmark", "https://example.com/benchmark", "Official"), date="2026-10-13"),
        ],
        github=[],
    )

    class ReadyVault(StaticCollector):
        vault_available = True

    monkeypatch.setattr(auto_collect_main, "XBookmarksCollector", lambda: ReadyVault(posts))

    class AcceptingX(XAwareProvider):
        def chat(self, prompt):
            if "X投稿" in prompt:
                return (
                    '{"title_ja":"新しいモデルの発表","summary":"%s","ai_related":true}'
                    % X_SUMMARY
                )
            return super().chat(prompt)

    monkeypatch.setattr(auto_collect_main, "make_provider", lambda _name: AcceptingX())
    monkeypatch.setattr(auto_collect_main, "generate_html_report", lambda _path: tmp_path / "report.html")
    captured = {}

    def capture_daily(*_args, **kwargs):
        captured.update(kwargs)
        return tmp_path / "daily.html"

    monkeypatch.setattr(auto_collect_main, "generate_daily_news", capture_daily)
    with caplog.at_level(logging.INFO):
        auto_collect_main.main()
    quality = captured["quality"]
    assert quality["status"] == "passed"
    assert quality["article_count"] == 21
    assert {row["url"] for row in captured["x_articles"]} == {post["url"] for post in posts}
    assert "https://example.com/benchmark" not in {row["url"] for row in captured["articles"]}
    assert any("news items" in record.message and "X posts" in record.message for record in caplog.records)
    assert not any(record.levelno >= logging.WARNING and "X posts" in record.message for record in caplog.records)
