"""Reviewed Japanese copy must reach HTML and JSON without changing evidence."""
from copy import deepcopy

import pytest

from src.auto_collect.claim_evidence import article_fingerprint
from src.auto_collect.html_report_renderer import generate_html


TITLES = {
    "https://karagila.org/2026/openai-pp": "数学者 Karagila 氏、OpenAI の分割原理論文の説明品質を批判",
    "https://openai.com/index/oracle": "OpenAI、Oracle の採用・開発業務での活用事例を公開",
    "https://openai.com/index/pollo-ai": "OpenAI、Pollo AI の画像・動画制作支援事例を公開",
}


def article(url="https://openai.com/index/oracle"):
    return {
        "title": "Original English title", "tldr": "Original English teaser",
        "summary": "Original English summary", "impact": "", "url": url,
        "source": "OpenAI", "score": 60, "category": "AI Model",
        "claim_evidence": None, "metrics": [], "points": [],
    }


def render(items, tmp_path):
    data = {"date": "2026-10-09", "headlines": items, "funding": [], "github": [], "models": []}
    return generate_html(data, archive_dir=tmp_path, default_og_image="https://example.test/og.png")


@pytest.mark.parametrize("url,title", TITLES.items())
def test_reviewed_copy_reaches_html_and_report_json(url, title, tmp_path):
    item = article(url)
    before = deepcopy(item)
    page, report = render([item], tmp_path)
    actual = report["headlines"][0]

    assert actual["title"] == title
    for field in ("title", "tldr", "summary", "impact"):
        assert actual[field] and actual[field] != before[field]
        assert actual[field] in page
    assert item == before  # No mutation of collector/parser input.
    for field in set(item) - {"title", "tldr", "summary", "impact"}:
        assert actual[field] == item[field]
    assert actual["reviewed_summary"] == {
        "source_url": url + "/", "source_date": "2026-10-08",
        "reviewed_at": "2026-10-09", "review_method": "ai_document_review",
    }
    # Reviewed copy may be rendered repeatedly without accumulating metadata.
    assert render(report["headlines"], tmp_path)[1]["headlines"] == report["headlines"]


@pytest.mark.parametrize("url", [
    "https://openai.com/index/oracle/", "https://OPENAI.com/index/oracle",
    "HTTPS://openai.com/index/oracle/",
])
def test_benign_url_variants_use_the_same_reviewed_article(url, tmp_path):
    _, report = render([article(url)], tmp_path)
    assert report["headlines"][0]["title"] == TITLES["https://openai.com/index/oracle"]


@pytest.mark.parametrize("url", [
    "https://openai.com/index/oracle/new", "https://openai.com/index/oracle-news",
    "https://openai.com/index/Oracle", "https://other.test/index/oracle",
    "https://openai.com/index/oracle?version=2", "https://openai.com/index/oracle#different",
    "http://openai.com/index/oracle", "javascript:openai.com/index/oracle",
])
def test_other_paths_sources_queries_and_fragments_keep_original_copy(url, tmp_path):
    item = article(url)
    _, report = render([item], tmp_path)
    assert report["headlines"] == [item]


def test_existing_claim_evidence_keeps_its_reviewed_wording_and_fingerprint(tmp_path):
    item = article()
    item["claim_evidence"] = {
        "version": 1, "sources": [], "claims": [{
            "id": "original-claim", "statement": "Original claim",
            "basis": "vendor_claim", "status": "unverified", "conditions": [],
            "source_refs": [],
        }],
        "subject_fingerprint": article_fingerprint(item),
    }
    before = deepcopy(item)
    _, report = render([item], tmp_path)
    assert report["headlines"] == [before]
    assert item == before


def test_invalid_claim_evidence_is_not_hidden_or_rebound_by_enrichment(tmp_path):
    item = article()
    item["claim_evidence"] = {"version": 1, "sources": [], "claims": []}
    with pytest.raises(ValueError, match="nonempty claims"):
        render([item], tmp_path)


def test_registry_missing_is_a_safe_noop(tmp_path):
    from src.auto_collect.reviewed_summaries import load_reviewed_summaries
    assert load_reviewed_summaries(tmp_path / "missing.json") == {}


@pytest.mark.parametrize("corruption", [
    "version", "article_map", "source_url", "empty_title", "missing_summary",
    "invalid_source_date", "invalid_review_date", "review_before_source", "duplicate_url",
])
def test_malformed_review_registry_fails_explicitly(tmp_path, corruption):
    import json
    from src.auto_collect.reviewed_summaries import REGISTRY_PATH, load_reviewed_summaries

    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    url, record = next(iter(payload["articles"].items()))
    if corruption == "version":
        payload["version"] = 2
    elif corruption == "article_map":
        payload["articles"] = []
    elif corruption == "source_url":
        record["source_url"] = "https://example.test/unrelated"
    elif corruption == "empty_title":
        record["title"] = " "
    elif corruption == "missing_summary":
        del record["summary"]
    elif corruption == "invalid_source_date":
        record["source_date"] = "2026-02-30"
    elif corruption == "invalid_review_date":
        record["reviewed_at"] = "not-a-date"
    elif corruption == "review_before_source":
        record["reviewed_at"] = "2026-10-07"
    elif corruption == "duplicate_url":
        payload["articles"][url.rstrip("/")] = dict(record)
    registry = tmp_path / "reviewed_news_summaries.json"
    registry.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="reviewed summaries"):
        load_reviewed_summaries(registry)


@pytest.mark.parametrize("url", [
    None, "", "https://openai.com:invalid/index/oracle",
    "https://user:password@openai.com/index/oracle", "https://openai.com/\nindex/oracle",
    "https://openai.com/index/oracle//",
])
def test_malformed_or_distinct_urls_are_not_enriched(url, tmp_path):
    item = article(url)
    # Exercise the registry independently of report link rendering.
    from src.auto_collect.reviewed_summaries import apply_reviewed_summary
    assert apply_reviewed_summary(item) == item


def test_empty_evidence_object_is_not_replaced_by_reviewed_copy():
    from src.auto_collect.reviewed_summaries import apply_reviewed_summary
    item = article()
    item["claim_evidence"] = {}
    assert apply_reviewed_summary(item) == item
