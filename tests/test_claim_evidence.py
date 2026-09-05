"""Fixed source records: no network, wall clock, API or reviewer invention."""
from copy import deepcopy
import json

import pytest

from src.auto_collect.claim_evidence import (
    article_fingerprint, claim_fingerprint, render_evidence, require_valid_evidence,
    safe_http_url, validate_bundle,
)


def fixture_bundle():
    sources = [{"id": "vendor-doc", "publisher": "Example vendor", "title": "Benchmark report", "url": "https://example.com/report", "published_at": "2026-09-03"}]
    claim = {"id": "performance", "label": "性能値", "statement": "提供元は達成率72.6%と公表した。", "evidence_label": "Claim", "basis": "vendor_claim", "status": "matched", "source_refs": [{"source_id": "vendor-doc", "section": "Results", "supports": "提供元が公表した達成率"}], "conditions": ["提供元の固定ベンチマーク"], "as_of": "2026-09-03", "uncertainty": "独立した再測定は未実施"}
    claim["verification"] = {"checked_at": "2026-09-05", "method": "ai_document_review", "fingerprint": claim_fingerprint(claim, sources), "note": "資料の表をAIが照合。人の確認記録は未登録。"}
    return {"version": 1, "sources": sources, "claims": [claim]}


def test_legacy_missing_metadata_is_not_upgraded():
    for bundle in (None, {}):
        assert validate_bundle(bundle) == []
        assert render_evidence(bundle) == ""
    bundle = fixture_bundle()
    claim = bundle["claims"][0]
    claim.update(status="unverified", verification=None, source_refs=[])
    assert not validate_bundle(bundle)
    rendered = render_evidence(bundle)
    assert "照合日未記録" in rendered
    assert "資料との照合済み" not in rendered
    assert "虚偽の判定ではありません" in rendered


def test_vendor_claim_and_ai_method_are_preserved_without_implicit_promotion():
    bundle = fixture_bundle()
    before = deepcopy(bundle)
    assert not validate_bundle(bundle)
    rendered = render_evidence(bundle)
    assert "ベンダー公称値" in rendered and "AIによる資料照合" in rendered
    assert "第三者の測定" not in rendered and "運営者による実測" not in rendered
    assert "人による資料照合" not in rendered
    assert bundle == before


@pytest.mark.parametrize("value", [None, "", "2026-02-30", "2026-9-5", "2026-09-05T00:00:00Z"])
def test_matched_record_needs_actual_valid_date(value):
    bundle = fixture_bundle()
    bundle["claims"][0]["verification"]["checked_at"] = value
    assert validate_bundle(bundle)
    rendered = render_evidence(bundle)
    assert "資料との照合済み" not in rendered
    assert "照合日未記録" in rendered


@pytest.mark.parametrize("field,value", [("statement", "数値を変更した。"), ("conditions", ["別OS"]), ("basis", "independent_measurement"), ("uncertainty", "全環境で保証")])
def test_changed_claim_does_not_inherit_review(field, value):
    bundle = fixture_bundle()
    bundle["claims"][0][field] = value
    assert any("fingerprint" in e for e in validate_bundle(bundle))
    assert "資料との照合済み" not in render_evidence(bundle)
    with pytest.raises(ValueError):
        require_valid_evidence(bundle)


def test_wrong_source_and_missing_support_are_detected():
    bundle = fixture_bundle()
    bundle["claims"][0]["source_refs"][0]["source_id"] = "another-document"
    assert any("missing referenced source" in e for e in validate_bundle(bundle))
    bundle = fixture_bundle()
    bundle["sources"][0]["url"] = "https://example.com/another-report"
    assert any("fingerprint" in e for e in validate_bundle(bundle))
    bundle = fixture_bundle()
    bundle["claims"][0]["source_refs"][0]["supports"] = ""
    assert any("supports" in e for e in validate_bundle(bundle))


def test_article_binding_detects_changed_title_and_summary():
    item = {"title": "見出し", "tldr": "概要", "summary": "本文"}
    bundle = fixture_bundle()
    assert validate_bundle(bundle, item)  # Explicit news metadata cannot omit the subject binding.
    bundle["subject_fingerprint"] = article_fingerprint(item)
    assert validate_bundle(bundle, item) == []
    assert validate_bundle(bundle, {**item, "summary": "別の本文"})
    assert "資料との照合済み" not in render_evidence(bundle, subject={**item, "title": "新しい見出し"})


def test_operator_measurement_requires_reproducible_record():
    bundle = fixture_bundle()
    claim = bundle["claims"][0]
    claim["basis"] = "operator_measurement"
    claim["verification"]["fingerprint"] = claim_fingerprint(claim, bundle["sources"])
    assert any("operator measurement" in e for e in validate_bundle(bundle))
    claim["measurement"] = {"environment": "Fixed local test environment", "method": "Fixed test workload", "results_url": "https://example.com/results"}
    claim["verification"]["fingerprint"] = claim_fingerprint(claim, bundle["sources"])
    assert not validate_bundle(bundle)


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,test", "//evil.example", "https://user:password@example.com", "https://example.com\n/test", "https://example.com\\@evil.example", "https://example.com:bad", ""])
def test_unsafe_urls_are_never_links(url):
    assert safe_http_url(url) == ""
    bundle = fixture_bundle()
    bundle["sources"][0]["url"] = url
    assert validate_bundle(bundle)
    assert f'href="{url}"' not in render_evidence(bundle)


def test_external_text_is_escaped_and_limits_visible_outside_details():
    bundle = fixture_bundle()
    bundle["sources"][0]["title"] = '<img src=x onerror="alert(1)">'
    claim = bundle["claims"][0]
    claim["verification"]["fingerprint"] = claim_fingerprint(claim, bundle["sources"])
    rendered = render_evidence(bundle)
    assert "<img" not in rendered and "&lt;img" in rendered
    assert rendered.index("独立した再測定は未実施") < rendered.index("<details>")
    assert "<summary>" in rendered and "tabindex=\"-1\"" not in rendered


def test_render_is_deterministic_and_never_changes_review_date():
    bundle = fixture_bundle()
    encoded = json.dumps(bundle, sort_keys=True)
    assert render_evidence(bundle) == render_evidence(bundle)
    assert json.dumps(bundle, sort_keys=True) == encoded
    assert "2026-09-05" in render_evidence(bundle)


@pytest.mark.parametrize("field,value", [("basis", []), ("status", {}), ("source_refs", [{"source_id": []}]), ("verification", {"method": []})])
def test_malformed_explicit_records_are_rejected_without_breaking_display(field, value):
    bundle = fixture_bundle()
    bundle["claims"][0][field] = value
    assert validate_bundle(bundle)
    assert "資料との照合済み" not in render_evidence(bundle)


def test_invalid_sources_shape_does_not_crash_legacy_fallback_display():
    bundle = fixture_bundle()
    bundle["sources"] = None
    assert validate_bundle(bundle)
    assert "資料との照合済み" not in render_evidence(bundle)
