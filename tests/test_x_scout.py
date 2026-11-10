"""X Scout collection, rejection, and card rendering."""

import json
from datetime import date, datetime, timedelta, timezone

from src.auto_collect.collectors.x_scout import XScoutCollector, XScoutFetchError, scout_url
from src.auto_collect.config import X_SCOUT_BRANCH, X_SCOUT_URL_TEMPLATE
from src.auto_collect.daily_news_page import _flatten_x, _render_x_card
from src.auto_collect.processor import LLMProcessor
from src.auto_collect.quality import article_errors, filter_publishable


TODAY = date(2026, 10, 15)
NOW = datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc)
LLM_SUMMARY = "新しいモデルの発表を紹介しています。研究者は公式資料を確認できます。"


def _item(**changes):
    row = {
        "id": "scout-1",
        "title_ja": "新しいモデルの公開",
        "summary_ja": "参考要約です。モデルの公開を一次情報で確認します。",
        "url_primary": "https://example.com/primary",
        "primary_date": "2026-10-15",
        "primary_verified": True,
        "x_url": "https://x.com/lab/status/1",
        "x_author": "@lab",
        "x_posted_at": "2026-10-14T22:00:00Z",
        "evidence_label": "Fact",
        "x_tweet_id": "1",
        "caveat": "料金は発表時点です",
    }
    row.update(changes)
    return row


def _file(items, **changes):
    payload = {
        "schema_version": 1,
        "date": "2026-10-15",
        "generated_at": "2026-10-15T02:00:00+00:00",
        "generated_by": "grok-bot",
        "items": items,
    }
    payload.update(changes)
    return json.dumps(payload)


def _collector(monkeypatch, raw):
    monkeypatch.setenv("X_SCOUT_ENABLED", "true")
    monkeypatch.delenv("X_SCOUT_DRY_RUN", raising=False)
    seen = {}

    def fetch(url):
        seen["url"] = url
        if isinstance(raw, Exception):
            raise raw
        return raw

    return XScoutCollector(fetch=fetch, now=lambda: NOW), seen


def test_url_template_uses_the_data_branch():
    assert X_SCOUT_BRANCH == "data/x-scout"
    assert scout_url(TODAY) == X_SCOUT_URL_TEMPLATE.format(branch=X_SCOUT_BRANCH, date="2026-10-15")
    assert scout_url(TODAY) == (
        "https://raw.githubusercontent.com/awano27/ai-news-site/data/x-scout/x_scout/2026-10-15.json"
    )


def test_accepts_a_verified_post_and_keeps_the_newer_date(monkeypatch):
    collector, seen = _collector(monkeypatch, _file([_item()]))
    posts = collector.collect(TODAY)
    assert seen["url"].endswith("/x_scout/2026-10-15.json")
    assert len(posts) == 1
    post = posts[0]
    assert post["url"] == "https://example.com/primary"
    assert post["rss_source"] == "X Scout (@lab)"
    assert post["x_curated"] is True
    assert post["x_scout"] is True
    assert post["x_tweet_id"] == "1"
    assert post["x_url"] == "https://x.com/lab/status/1"
    assert post["caveat"] == "料金は発表時点です"
    assert post["description"] == "参考要約です。モデルの公開を一次情報で確認します。"
    assert post["summary"] == ""
    # 2026-10-14 22:00Z is 2026-10-15 in JST, newer than primary_date 2026-10-15? equal.
    # primary_date is the 15th and the post is also the 15th in JST.
    assert post["bookmark_date"] == "2026-10-15"


def test_bookmark_date_uses_the_newer_of_primary_and_posted(monkeypatch):
    older_post = _item(primary_date="2026-10-14", x_posted_at="2026-10-13T00:00:00+09:00")
    newer_post = _item(id="scout-2", primary_date="2026-10-14", x_posted_at="2026-10-15T09:00:00+09:00")
    collector, _seen = _collector(monkeypatch, _file([older_post, newer_post]))
    posts = collector.collect(TODAY)
    assert [post["bookmark_date"] for post in posts] == ["2026-10-14", "2026-10-15"]


def test_disabled_flag_does_not_fetch(monkeypatch):
    monkeypatch.delenv("X_SCOUT_ENABLED", raising=False)

    def fetch(_url):
        raise AssertionError("fetch must not run when X Scout is disabled")

    assert XScoutCollector(fetch=fetch, now=lambda: NOW).collect(TODAY) == []


def test_fetch_404_invalid_json_and_transport_errors_return_empty(monkeypatch, caplog):
    for raw in (XScoutFetchError("404"), XScoutFetchError("HTTP 500"), "{not json", XScoutFetchError("timed out")):
        collector, _seen = _collector(monkeypatch, raw)
        with caplog.at_level("WARNING"):
            assert collector.collect(TODAY) == []
        assert any("continuing without X Scout" in record.message for record in caplog.records)
        caplog.clear()


def test_http_404_and_invalid_body_do_not_raise(monkeypatch):
    monkeypatch.setenv("X_SCOUT_ENABLED", "true")

    class Response:
        def __init__(self, status, text):
            self.status_code = status
            self.text = text

    def fake_get(url, timeout, headers):
        assert "Authorization" not in headers
        assert url.endswith("2026-10-15.json")
        return Response(404, "missing")

    monkeypatch.setattr("src.auto_collect.collectors.x_scout.requests.get", fake_get)
    assert XScoutCollector(now=lambda: NOW).collect(TODAY) == []

    def bad_json(url, timeout, headers):
        return Response(200, "{not json")

    monkeypatch.setattr("src.auto_collect.collectors.x_scout.requests.get", bad_json)
    assert XScoutCollector(now=lambda: NOW).collect(TODAY) == []


def test_stale_generated_at_is_not_used(monkeypatch, caplog):
    generated = (NOW - timedelta(hours=24, seconds=1)).isoformat()
    collector, _seen = _collector(monkeypatch, _file([_item()], generated_at=generated))
    with caplog.at_level("WARNING"):
        assert collector.collect(TODAY) == []
    assert any("older than 24 hours" in record.message for record in caplog.records)


def test_generated_at_exactly_24_hours_old_is_used(monkeypatch):
    generated = (NOW - timedelta(hours=24)).isoformat()
    collector, _seen = _collector(monkeypatch, _file([_item()], generated_at=generated))
    assert len(collector.collect(TODAY)) == 1


def test_rejection_rules_and_daily_cap(monkeypatch):
    items = [
        _item(id="ok-http", url_primary="http://example.com/http"),
        _item(id="unverified", primary_verified=False),
        _item(id="string-true", primary_verified="true"),
        _item(id="bad-url", url_primary="javascript:alert(1)"),
        _item(id="ftp", url_primary="ftp://example.com/file"),
        _item(id="old", primary_date="2026-10-13"),
        _item(id="future", primary_date="2026-10-16"),
        _item(id="dup", url_primary="https://example.com/dup"),
        _item(id="dup", url_primary="https://example.com/dup-again"),
        _item(id="missing", summary_ja=""),
        _item(id="yesterday", primary_date="2026-10-14", url_primary="https://example.com/yesterday"),
    ]
    items.extend(
        _item(id=f"extra-{index}", url_primary=f"https://example.com/extra-{index}")
        for index in range(5)
    )
    collector, _seen = _collector(monkeypatch, _file(items))
    posts = collector.collect(TODAY)
    assert [post["url"] for post in posts] == [
        "http://example.com/http",
        "https://example.com/dup",
        "https://example.com/yesterday",
        "https://example.com/extra-0",
        "https://example.com/extra-1",
    ]
    assert len(posts) == 5


def test_bad_schema_returns_empty(monkeypatch, caplog):
    collector, _seen = _collector(monkeypatch, _file([_item()], schema_version=2))
    with caplog.at_level("WARNING"):
        assert collector.collect(TODAY) == []
    assert any("schema_version" in record.message for record in caplog.records)


def test_summary_ja_is_only_model_input_and_the_quality_gate_still_applies():
    reference = "参考要約です。モデルの公開を一次情報で確認します。"
    article = {
        "name": "新しいモデルの公開",
        "description": reference,
        "tagline": reference,
        "url": "https://example.com/primary",
        "links": {"official": "https://example.com/primary"},
        "rss_source": "X Scout (@lab)",
        "source": "X Scout (@lab)",
        "authors": "@lab",
        "x_curated": True,
        "x_scout": True,
        "x_url": "https://x.com/lab/status/1",
        "x_tweet_id": "1",
        "bookmark_date": "2026-10-13",
        "caveat": "料金は発表時点です",
        "evidence_label": "Fact",
        "summary": "",
    }
    assert article_errors(article)

    class Provider:
        available = True
        name = "ollama"
        last_error = ""

        def chat(self, prompt):
            assert reference in prompt
            assert "ツイート本文そのもの" not in prompt
            return (
                '{"title_ja":"モデル公開","summary":"%s","ai_related":true}' % LLM_SUMMARY
            )

    processed = LLMProcessor(provider=Provider()).process_x_posts([article])[0]
    assert processed["summary"] == LLM_SUMMARY
    assert reference not in processed["summary"]
    assert processed["processing_status"] == "llm"
    assert processed["x_scout"] is True
    assert processed["caveat"] == "料金は発表時点です"
    assert processed["x_url"] == "https://x.com/lab/status/1"
    assert processed["bookmark_date"] == "2026-10-13"
    assert article_errors(processed) == []
    kept, quality = filter_publishable([processed], min_articles=1, min_sources=1)
    assert quality["status"] == "passed"
    assert kept[0]["url"] == "https://example.com/primary"

    class Unrelated(Provider):
        def chat(self, _prompt):
            return '{"title_ja":"昼ごはん","summary":"昼ごはんの写真が共有されています。食事の様子が写っています。","ai_related":false}'

    dropped = LLMProcessor(provider=Unrelated()).process_x_posts([article])[0]
    assert "not AI-related" in article_errors(dropped)


def test_x_scout_card_shows_source_and_caveat_without_the_post_body():
    reference = "参考要約です。モデルの公開を一次情報で確認します。"
    flattened = _flatten_x([{
        "title": "モデル公開",
        "summary": LLM_SUMMARY,
        "description": reference,
        "url": "https://example.com/primary",
        "rss_source": "X Scout (@lab)",
        "authors": "@lab",
        "x_scout": True,
        "x_url": "https://x.com/lab/status/1",
        "caveat": "料金は<script>発表時点</script>です",
        "evidence_label": "Fact",
        "bookmark_date": "2026-10-13",
    }])[0]
    html = _render_x_card(flattened)
    assert "X Scout" in html
    assert "一次情報を開く" in html
    assert "https://example.com/primary" in html
    assert "料金は&lt;script&gt;発表時点&lt;/script&gt;です" in html
    assert reference not in html
    assert "https://x.com/lab/status/1" not in html
    assert ">Fact<" in html

    bookmark = _render_x_card(_flatten_x([{
        "title": "ブックマーク",
        "summary": LLM_SUMMARY,
        "url": "https://x.com/lab/status/2",
        "authors": "@lab",
        "x_note": "memo",
        "evidence_label": "Curated",
    }])[0])
    assert ">X</span>" in bookmark
    assert "X で開く" in bookmark
    assert "X Scout" not in bookmark
    assert ">Curated<" in bookmark
