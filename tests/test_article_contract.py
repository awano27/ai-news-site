"""Fixed-fixture coverage for article time and information-label contracts."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from src.auto_collect.claim_evidence import information_label
from src.auto_collect.collectors.hn_collector import HNAutoCollector
from src.auto_collect.daily_news_page import _flatten_news, _is_recent, _render_news_card
from src.auto_collect.processor import LLMProcessor
from src.auto_collect.formatter import DayFileFormatter
from src.auto_collect.html_report_parser import parse_daily_txt
from src.auto_collect.html_report_renderer import _render_news_row


JST = timezone(timedelta(hours=9))
TARGET = date(2026, 10, 3)


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _HNSession:
    def __init__(self, items):
        self.items = items

    def get(self, url, timeout=10):
        if url.endswith("topstories.json"):
            return _Response(list(self.items))
        story_id = int(url.rsplit("/", 1)[-1].split(".", 1)[0])
        return _Response(self.items[story_id])


def _epoch(day: date, hour: int = 12) -> int:
    return int(datetime.combine(day, datetime.min.time(), JST).replace(hour=hour).timestamp())


def test_hn_filters_on_jst_target_window_and_records_provenance(monkeypatch):
    items = {
        1: {"title": "AI today", "url": "https://example.test/today", "score": 100, "time": _epoch(TARGET)},
        2: {"title": "AI yesterday", "url": "https://example.test/yesterday", "score": 100, "time": _epoch(TARGET - timedelta(days=1))},
        3: {"title": "AI old", "url": "https://example.test/old", "score": 100, "time": _epoch(TARGET - timedelta(days=2), 23)},
        4: {"title": "AI future", "url": "https://example.test/future", "score": 100, "time": _epoch(TARGET + timedelta(days=1), 0)},
        5: {"title": "AI invalid", "url": "https://example.test/invalid", "score": 100, "time": "not-an-epoch"},
    }
    collector = HNAutoCollector()
    collector.session = _HNSession(items)
    monkeypatch.setattr(collector, "_rate_limit", lambda: None)

    result = collector.collect(TARGET)

    assert [item["name"] for item in result] == ["AI today", "AI yesterday"]
    assert all(item["target_date"] == "2026-10-03" for item in result)
    assert all(item["published_at"].endswith("+00:00") for item in result)
    assert all(item["collected_at"].endswith("+00:00") for item in result)


def test_processor_preserves_temporal_fields_in_model_and_fallback_paths():
    source = {
        "name": "AI source", "tagline": "summary", "links": {"official": "https://example.test/a"},
        "published_at": "2026-10-02T23:30:00Z", "collected_at": "2026-10-03T00:10:00Z",
        "target_date": "2026-10-03",
    }
    fallback = LLMProcessor(provider=SimpleNamespace(available=False, name="fixture"))
    fallback_result = fallback._fallback_process(source)
    assert {key: fallback_result[key] for key in ("published_at", "collected_at", "target_date")} == {
        "published_at": source["published_at"], "collected_at": source["collected_at"],
        "target_date": source["target_date"],
    }

    provider = SimpleNamespace(
        available=True,
        name="fixture",
        chat=lambda prompt: '{"title_ja":"記事","score":70,"evidence_label":"NotVerified"}',
    )
    model_result = LLMProcessor(provider=provider)._process_with_llm(source)
    assert model_result["published_at"] == source["published_at"]
    assert model_result["evidence"]["evidence_label"] == ""
    invalid_model_card = _render_news_card(_flatten_news([model_result])[0])
    assert "情報区分未確認" in invalid_model_card
    assert "照合未確認" in invalid_model_card
    assert "資料との照合済み" not in invalid_model_card

    provider.chat = lambda prompt: '{"title_ja":"記事","score":70,"evidence_label":"Fact"}'
    classified = LLMProcessor(provider=provider)._process_with_llm(source)
    assert classified["evidence"]["evidence_label"] == "Fact"
    assert "claim_evidence" not in classified
    fact_model_card = _render_news_card(_flatten_news([classified])[0])
    assert "Fact" in fact_model_card
    assert "照合未確認" in fact_model_card
    assert "資料との照合済み" not in fact_model_card


def test_daily_news_freshness_uses_jst_publication_date_and_rejects_unknown():
    cases = [
        ({"published_at": "2026-10-03T00:00:00+09:00"}, True),
        ({"published_at": "2026-10-03T23:59:59+09:00"}, True),  # same JST calendar day
        ({"published_at": "2026-10-02T00:00:00+09:00"}, True),
        ({"published_at": "2026-10-01T23:59:59+09:00"}, False),
        ({"published_at": "2026-10-03T15:00:00Z"}, False),  # 2026-10-04 JST
        ({"published_at": "2026-10-01T15:00:00Z"}, True),   # 2026-10-02 JST
        ({"published_at": "invalid"}, False),
        ({"published_at": None, "date": "2026-10-03"}, False),
        ({"target_date": "2026-10-03", "date": "2026-10-03"}, False),
        ({"date": "2026-10-03"}, True),  # legacy publication-date shape
        ({}, False),
        ({"collected_at": "2026-10-03T01:00:00Z"}, False),
    ]
    for item, expected in cases:
        assert _is_recent(item, TARGET) is expected


def test_nested_label_is_validated_and_propagated_without_review_status():
    article = {
        "title": "Nested label", "summary": "body", "url": "https://example.test/a",
        "published_at": "2026-10-03T00:00:00+09:00", "evidence": {"evidence_label": "Claim"},
    }
    flattened = _flatten_news([article])
    assert flattened[0]["evidence_label"] == "Claim"
    assert flattened[0]["claim_evidence"] is None
    assert information_label({"evidence": {"evidence_label": "Verified"}}) == ""
    assert information_label({"evidence_label": "", "evidence": {"evidence_label": "Claim"}}) == "Claim"


def _render_fixture(**overrides):
    item = {
        "title": "Classification fixture", "summary": "body", "url": "https://example.test/a",
        "category": "Research", "source": "Fixture", "score": 70,
        **overrides,
    }
    return _render_news_card(item), _render_news_row(1, item)


def test_invalid_nested_label_is_visibly_pending_in_both_renderers():
    for rendered in _render_fixture(evidence={"evidence_label": "Verified"}):
        assert "情報区分未確認" in rendered
        assert "照合未確認" in rendered
        assert "資料との照合済み" not in rendered


def test_fact_classification_without_claim_evidence_does_not_imply_review():
    for rendered in _render_fixture(evidence={"evidence_label": "Fact"}):
        assert "Fact" in rendered
        assert "照合未確認" in rendered
        assert "資料との照合済み" not in rendered


def test_dayfile_round_trip_preserves_time_fields_and_nested_label(tmp_path):
    article = {
        "title": "Contract", "tldr": "short", "summary": "body", "score": 70,
        "category": "Research", "url": "https://example.test/contract", "source": "Fixture",
        "published_at": "2026-10-02T23:30:00Z", "collected_at": "2026-10-03T00:10:00Z",
        "target_date": "2026-10-03", "evidence": {"evidence_label": "Claim"},
    }
    dayfile = tmp_path / "1003.txt"

    DayFileFormatter().write([article], dayfile, TARGET)
    parsed = parse_daily_txt(dayfile)["headlines"][0]

    assert parsed["published_at"] == article["published_at"]
    assert parsed["collected_at"] == article["collected_at"]
    assert parsed["target_date"] == article["target_date"]
    assert parsed["evidence_label"] == "Claim"
