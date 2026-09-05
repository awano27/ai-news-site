from __future__ import annotations

import json
from datetime import date

import pytest

from src.auto_collect import daily_news_page
from src.auto_collect.html_report import generate_html
from src.auto_collect.html_report_parser import parse_daily_txt
from src.auto_collect.formatter import DayFileFormatter
from src.auto_collect.content_integrity import (
    CRUSOE_2026_09_05_URL,
    FinancialClaimError,
    apply_article_correction,
    apply_financial_integrity,
    validate_financial_claims,
)


def test_same_metric_conflict_is_rejected_using_fixed_fixture() -> None:
    """The published 30B/30億 mismatch must fail before the correction runs."""
    with pytest.raises(FinancialClaimError, match="inconsistent financial claim"):
        validate_financial_claims(
            [
                {"metric": "valuation", "currency": "USD", "amount": "30", "unit": "billion", "event_date": "2026-09-03"},
                {"metric": "valuation", "currency": "USD", "amount": "30", "unit": "億", "event_date": "2026-09-03"},
            ]
        )


def test_distinct_financial_metrics_do_not_produce_a_false_positive() -> None:
    claims = validate_financial_claims(
        [
            {"metric": "valuation", "currency": "USD", "amount": "30", "unit": "billion", "event_date": "2026-09-03"},
            {"metric": "funding", "currency": "USD", "amount": "3", "unit": "billion", "event_date": "2026-09-03"},
            {"metric": "contract", "currency": "USD", "amount": "13", "unit": "billion", "event_date": "2026-09-03"},
        ]
    )

    assert [claim["amount_millions"] for claim in claims] == ["30000", "3000", "13000"]


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_amount_is_rejected(amount: str) -> None:
    with pytest.raises(FinancialClaimError, match="finite"):
        validate_financial_claims(
            [{"metric": "valuation", "currency": "USD", "amount": amount, "unit": "billion", "event_date": "2026-09-03"}]
        )


def test_equivalent_decimal_spellings_are_not_a_conflict() -> None:
    claims = validate_financial_claims(
        [
            {"metric": "valuation", "currency": "USD", "amount": "30", "unit": "billion", "event_date": "2026-09-03"},
            {"metric": "valuation", "currency": "USD", "amount": "30.0", "unit": "B", "event_date": "2026-09-03"},
        ]
    )
    assert len(claims) == 2


def test_crusoe_correction_is_idempotent_and_preserves_report_attribution() -> None:
    legacy_article = {
        "url": CRUSOE_2026_09_05_URL + "?utm_source=rss",
        "title": "クルーソ、30億ドル評価で30億ドル調達",
        "summary": "企業価値は$30億、調達額は$30億ドル。",
        "tldr": "データセンター開発企業が$30Bの評価で$3Bを調達",
        "points": ["企業価値は$30億"],
        "evidence": {"metrics": ["$30億"], "impact_ja": "未検証の因果", "actionable": "未検証の手順"},
    }

    once = apply_article_correction(legacy_article)
    twice = apply_article_correction(once)

    assert twice == once
    assert "$30億" not in once["summary"]
    assert once["title"] == "クルーソ、約300億米ドル評価で約30億米ドル調達"
    assert once["points"] == []
    assert "$30億" not in " ".join(once["metrics"])
    assert "$30億" not in " ".join(once["evidence"]["metrics"])
    assert once["evidence"]["impact_ja"] == ""
    assert once["evidence"]["actionable"] == ""
    assert once["source_attribution"] == "TechCrunch（Bloomberg報道）"
    assert [(claim["metric"], claim["amount_millions"]) for claim in once["financial_claims"]] == [
        ("valuation", "30000"),
        ("funding", "3000"),
        ("contract", "13000"),
    ]


def test_unknown_same_metric_conflict_holds_only_that_article_for_review() -> None:
    checked = apply_financial_integrity(
        {
            "title": "Example raises at valuation",
            "date": "2026-09-05",
            "summary": "企業価値は$30B。別の説明では企業価値は$30億。",
        }
    )

    assert checked["integrity_status"] == "pending_fact_check"
    assert checked["title"] == "数値整合性を確認中"
    assert "金額を含む要約の掲載を保留" in checked["summary"]
    assert checked["evidence"]["metrics"] == []
    assert checked["metrics"] == []


def test_decimal_billion_is_parsed_without_splitting_the_decimal_point() -> None:
    checked = apply_financial_integrity(
        {"title": "Example", "date": "2026-09-05", "summary": "企業価値は$1.5B。"}
    )
    assert checked["financial_claims"][0]["amount_millions"] == "1500.0"


def test_distinct_metrics_in_the_same_prose_do_not_create_false_claim_pairs() -> None:
    checked = apply_financial_integrity(
        {
            "title": "Example financial update",
            "date": "2026-09-05",
            "summary": "企業価値は$30B、調達額は$3B、契約額は$13B。",
        }
    )

    assert "integrity_status" not in checked
    assert [(claim["metric"], claim["amount_millions"]) for claim in checked["financial_claims"]] == [
        ("valuation", "30000"),
        ("funding", "3000"),
        ("contract", "13000"),
    ]


def test_jpy_and_usd_values_are_distinct_currencies_not_a_same_fact_conflict() -> None:
    claims = validate_financial_claims(
        [
            {"metric": "valuation", "currency": "JPY", "amount": "30", "unit": "億", "event_date": "2026-09-05"},
            {"metric": "valuation", "currency": "USD", "amount": "30", "unit": "billion", "event_date": "2026-09-05"},
        ]
    )
    assert [claim["currency"] for claim in claims] == ["JPY", "USD"]


def test_parameter_count_does_not_trigger_a_financial_warning() -> None:
    checked = apply_financial_integrity(
        {"title": "30B parameter model", "date": "2026-09-05", "summary": "30B parameter model was released."}
    )
    assert "integrity_warning" not in checked


def test_prior_period_values_warn_instead_of_holding_an_article() -> None:
    checked = apply_financial_integrity(
        {
            "title": "Example valuation update",
            "date": "2026-09-05",
            "summary": "前年の企業価値は$10B、現在の企業価値は$30B。",
        }
    )

    assert "integrity_status" not in checked
    assert "manual source review" in checked["integrity_warning"]


def test_formatter_and_parser_preserve_a_pending_article_without_restoring_numbers(tmp_path) -> None:
    pending = apply_financial_integrity(
        {
            "title": "Example raises at valuation",
            "url": "https://example.test/article",
            "date": "2026-09-05",
            "category": "Business",
            "score": 80,
            "summary": "企業価値は$30B。別の説明では企業価値は$30億。",
            "evidence": {
                "metrics": ["企業価値$30B", "企業価値$30億"],
                "impact_ja": "未検証の影響",
                "actionable": "未検証の手順",
            },
        }
    )
    dayfile = tmp_path / "0905.txt"

    DayFileFormatter().write([pending], dayfile, date(2026, 9, 5))
    parsed = parse_daily_txt(dayfile)["headlines"][0]

    assert parsed["integrity_status"] == "pending_fact_check"
    assert parsed["title"] == "数値整合性を確認中"
    assert "$30" not in parsed["summary"]
    assert parsed["metrics"] == []


def test_unlabelled_amount_creates_a_warning_but_does_not_hold_an_article() -> None:
    checked = apply_financial_integrity(
        {"title": "Example", "date": "2026-09-05", "summary": "投資家は$30Bを注視している。"}
    )

    assert "integrity_status" not in checked
    assert "manual source review" in checked["integrity_warning"]


def test_daily_news_regeneration_emits_corrected_html_and_json_without_duplicates(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    output_dir = tmp_path / "daily-news"
    monkeypatch.setattr(daily_news_page, "DAILY_NEWS_DIR", output_dir)
    monkeypatch.setattr(daily_news_page, "ARCHIVE_DIR", output_dir / "archive")
    article = {
        "title": "クルーソ、300億ドル評価で30億ドル調達",
        "url": CRUSOE_2026_09_05_URL,
        "summary": "企業価値は$30億、調達額は$30億ドル。",
        "tldr": "データセンター開発企業が$30Bの評価で$3Bを調達",
        "score": 85,
        "category": "Business",
        "source": "TechCrunch AI",
        "date": "2026-09-05",
    }

    daily_news_page.generate_daily_news(date(2026, 9, 5), [article])
    daily_news_page.generate_daily_news(date(2026, 9, 5), [article])

    html = (output_dir / "index.html").read_text(encoding="utf-8")
    payload = json.loads((output_dir / "data.json").read_text(encoding="utf-8"))
    item = payload["items"][0]
    assert "$30億" not in html
    assert "訂正: 2026-09-05: 企業価値・調達額・契約額を別の指標として訂正。" in html
    assert payload["total"] == 1
    assert item["summary"].count("企業価値が約300億米ドル") == 1
    assert item["correction_note"] == "2026-09-05: 企業価値・調達額・契約額を別の指標として訂正。"
    assert len(item["financial_claims"]) == 3


def test_dayfile_top15_generation_uses_the_same_crusoe_correction(tmp_path) -> None:
    dayfile = tmp_path / "0905.txt"
    dayfile.write_text(
        "2026年09月05日 AIニュース\n"
        "ヘッドライン速報\n"
        "■ クルーソ、300億ドル評価で30億ドル調達（Business / スコア: 85）\n"
        "ソース: TechCrunch AI\n"
        "URL: " + CRUSOE_2026_09_05_URL + "\n"
        "🎯 データセンター開発企業が$30Bの評価で$3Bを調達\n"
        "データセンター開発企業クルーソは、$30億の企業価値を評価され、$30億ドルを調達した。\n",
        encoding="utf-8",
    )

    parsed = parse_daily_txt(dayfile)
    html, report_data = generate_html(parsed)
    article = report_data["headlines"][0]

    assert "$30億" not in html
    assert "訂正: 2026-09-05: 企業価値・調達額・契約額を別の指標として訂正。" in html
    assert article["source_attribution"] == "TechCrunch（Bloomberg報道）"
    assert len(article["financial_claims"]) == 3
