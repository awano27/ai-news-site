from copy import deepcopy

from scripts.check_claim_evidence import compare_article_evidence, compare_homepage_evidence
from src.auto_collect.claim_evidence import article_fingerprint, claim_fingerprint


def record_fixture():
    item = {"title": "価値と調達", "tldr": "異なる指標", "summary": "報道にある2つの指標"}
    sources = [{"id": "news", "publisher": "Newsroom", "title": "Financing report", "url": "https://example.com/financing", "published_at": "2026-09-03"}]
    claim = {"id": "funding", "statement": "調達額の報道", "evidence_label": "Claim", "basis": "reporting", "status": "matched", "source_refs": [{"source_id": "news", "section": "lead", "supports": "調達額"}], "conditions": ["別紙報道の引用"], "as_of": "2026-09-03"}
    claim["verification"] = {"checked_at": "2026-09-05", "method": "ai_document_review", "fingerprint": claim_fingerprint(claim, sources)}
    item["claim_evidence"] = {"version": 1, "sources": sources, "claims": [claim], "subject_fingerprint": article_fingerprint(item)}
    return item


def test_derivative_review_date_and_category_drift_are_errors():
    item = record_fixture()
    expected = deepcopy(item["claim_evidence"])
    assert compare_article_evidence(item, expected) == []
    item["claim_evidence"]["claims"][0]["verification"]["checked_at"] = "2026-09-06"
    assert compare_article_evidence(item, expected)
    item = record_fixture()
    item["claim_evidence"]["claims"][0]["evidence_label"] = "Fact-A"
    assert compare_article_evidence(item, expected)


def test_migrated_subject_cannot_drop_metadata_or_change_body():
    item = record_fixture()
    expected = item.pop("claim_evidence")
    assert compare_article_evidence(item, expected)
    item = record_fixture()
    item["summary"] = "別の主張"
    assert compare_article_evidence(item, item["claim_evidence"])


def test_homepage_projection_preserves_evidence_and_dated_detail():
    expected = record_fixture()["claim_evidence"]
    projection = {"blurb": "短い表示", "claim_evidence": deepcopy(expected), "evidence_url": "presentations/daily_reports/auto_daily_report_2026_09_05.html#evidence-funding"}
    assert compare_homepage_evidence(projection, expected) == []
    projection["evidence_url"] = "presentations/auto_daily_report.html"
    assert compare_homepage_evidence(projection, expected)
    projection.pop("claim_evidence")
    assert compare_homepage_evidence(projection, expected)


def test_homepage_body_change_cannot_reuse_reviewed_bundle():
    item = record_fixture()
    expected = item["claim_evidence"]
    projection = {"title": item["title"], "blurb": item["tldr"], "claim_evidence": expected, "evidence_url": "presentations/daily_reports/auto_daily_report_2026_09_05.html#evidence-funding"}
    assert compare_homepage_evidence(projection, expected, item) == []
    projection["blurb"] = "企業公式発表で確認済みという別の本文"
    assert compare_homepage_evidence(projection, expected, item)
