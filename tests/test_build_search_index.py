from pathlib import Path

from scripts.build_search_index import extract_slide_record


def test_extract_slide_record_strips_date_and_sets_type(tmp_path: Path):
    path = tmp_path / "day_slide_2026_08_21.html"
    path.write_text(
        "<html><head>"
        "<title>Ox Alpha — stealth frontier | 2026-08-21</title>"
        '<meta name="description" content="A summary about Claude.">'
        "</head></html>",
        encoding="utf-8",
    )
    row = extract_slide_record(path)
    assert row["type"] == "slide"
    assert row["date"] == "2026-08-21"
    assert row["title"] == "Ox Alpha — stealth frontier"
    assert row["summary"] == "A summary about Claude."
    assert row["url"] == "/presentations/day_slides/day_slide_2026_08_21.html"
    assert "type" in row


import json

import pytest

from scripts import build_search_index as search


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def daily_payload(day="2026-10-09", **article):
    return {"date": day, "items": [{"title": "本日のモデル", "url": "https://example.com/model", "type": "news", **article}]}


def build(root):
    # The incremental entry point is shared by CLI and daily publication.
    return search.build_index(root)


def test_incremental_build_keeps_every_stored_row_and_identity(tmp_path):
    historical = [
        {"date": "2025-01-01", "title": "old A", "url": "https://example.com/a?utm_source=old", "summary": "keep exactly", "custom": [1]},
        {"date": "2025-01-01", "title": "old B", "url": "https://example.com/a", "summary": "also keep exactly"},
    ]
    write_json(tmp_path / "public-pages/news/search_index.json", historical)
    write_json(tmp_path / "daily-news/data.json", daily_payload())
    result = build(tmp_path)
    assert all(row in result for row in historical)
    assert len(result) == 3
    assert next(row for row in result if row["date"] == "2026-10-09")["type"] == "news"


def test_new_capture_dedupes_tracking_only_and_retains_source_url(tmp_path):
    tracked = "https://EXAMPLE.com/model?b=2&utm_source=mail&a=1#top"
    candidate = daily_payload(url=tracked)
    candidate["items"].append({"title": "duplicate", "url": "https://example.com/model?a=1&b=2", "type": "news"})
    write_json(tmp_path / "daily-news/data.json", candidate)
    result = build(tmp_path)
    assert len(result) == 1
    assert result[0]["url"] == tracked
    write_json(tmp_path / "public-pages/news/search_index.json", result)
    assert build(tmp_path) == result


def test_capture_date_and_source_publication_date_are_independent(tmp_path):
    write_json(tmp_path / "daily-news/data.json", daily_payload(date="2026-10-08T18:30:00+00:00", summary="日本語の要約です。"))
    row = build(tmp_path)[0]
    assert row["date"] == "2026-10-09"
    assert row["published_at"] == "2026-10-08T18:30:00+00:00"
    assert row["summary"] == "日本語の要約です。"


def test_builder_reads_daily_snapshots_when_current_feed_advances(tmp_path):
    write_json(tmp_path / "public-pages/news/daily/2026-10-08.json", daily_payload("2026-10-08"))
    write_json(tmp_path / "daily-news/data.json", daily_payload("2026-10-09"))
    result = build(tmp_path)
    assert {row["date"] for row in result} == {"2026-10-08", "2026-10-09"}


def test_richer_same_day_snapshot_wins_over_delayed_cloud(tmp_path):
    local = daily_payload()
    local["items"].append({"title": "手選び X", "type": "x", "url": "https://x.com/curator/status/1", "body": "日本語の投稿要約"})
    write_json(tmp_path / "public-pages/news/daily/2026-10-09.json", local)
    write_json(tmp_path / "daily-news/data.json", daily_payload(title="cloud replacement"))
    rows = build(tmp_path)
    assert {row["title"] for row in rows} == {"本日のモデル", "手選び X"}


def test_only_existing_valid_slides_added_and_old_slides_retained(tmp_path):
    historical = {"date": "2026-10-07", "url": "/presentations/day_slides/day_slide_2026_10_07.html", "title": "missing locally", "type": "slide"}
    current = {"date": "2026-10-08", "url": "/presentations/day_slides/day_slide_2026_10_08.html", "title": "stale", "type": "slide", "slide_schema": 1, "custom": "keep"}
    write_json(tmp_path / "public-pages/news/search_index.json", [historical, current])
    slides = tmp_path / "presentations/day_slides"
    slides.mkdir(parents=True)
    (slides / "day_slide_2026_10_08.html").write_text('<title>Updated | 2026-10-08</title><meta name="description" content="Fresh">')
    (slides / "day_slide_2026_10_09.html").write_text('<title>New | 2026-10-09</title>')
    (slides / "day_slide_2026_99_99.html").write_text('<title>Invalid</title>')
    rows = build(tmp_path)
    assert historical in rows
    assert len(rows) == 3
    updated = next(row for row in rows if row["date"] == "2026-10-08")
    assert updated["title"] == "Updated"
    assert updated["summary"] == "Fresh"
    assert updated["custom"] == "keep"


@pytest.mark.parametrize("invalid", ["javascript:alert(1)", "data:text/html,test", "//example.com/a", "https://user:secret@example.com/a", "https://example.com/a\nnext", "http://"])
def test_new_rows_exclude_unsafe_urls(tmp_path, invalid):
    data = daily_payload()
    data["items"].append({"title": "unsafe", "url": invalid})
    write_json(tmp_path / "daily-news/data.json", data)
    assert len(build(tmp_path)) == 1


def test_new_rows_exclude_invalid_dates(tmp_path):
    data = daily_payload()
    data["items"].append({"title": "bad date", "url": "https://example.com/bad", "date": "2026-99-99"})
    write_json(tmp_path / "daily-news/data.json", data)
    assert len(build(tmp_path)) == 1


def test_stored_news_is_not_replaced_by_sparse_legacy_aggregate(tmp_path):
    old = {"date": "2026-08-23", "title": "genuine record", "url": "https://example.com/model", "summary": "preserve"}
    write_json(tmp_path / "public-pages/news/search_index.json", [old])
    write_json(tmp_path / "public-pages/news/2026-08-23.json", {"articles": [{"title": "aggregate", "url": old["url"]}]})
    assert build(tmp_path) == [old]


def test_large_index_never_strips_historical_summaries(tmp_path):
    old = {"date": "2025-01-01", "title": "large", "url": "https://example.com/large", "summary": "x" * 2_000_100}
    write_json(tmp_path / "public-pages/news/search_index.json", [old])
    search.write_index(tmp_path)
    assert json.loads((tmp_path / "public-pages/news/search_index.json").read_text()) == [old]


@pytest.mark.parametrize("target", ["public-pages/news/search_index.json", "public-pages/news/daily/2026-10-08.json", "daily-news/data.json"])
def test_invalid_json_aborts_without_overwriting_index(tmp_path, target):
    output = tmp_path / "public-pages/news/search_index.json"
    write_json(output, [{"date": "2025-01-01", "title": "keep", "url": "https://example.com/keep"}])
    path = tmp_path / target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{corrupt")
    before = output.read_bytes()
    with pytest.raises((ValueError, OSError)):
        search.write_index(tmp_path)
    assert output.read_bytes() == before


def test_only_managed_capture_rows_refresh_on_same_day_corrections(tmp_path):
    legacy = {"date": "2026-10-09", "title": "legacy remains", "url": "https://example.com/legacy", "summary": "original"}
    write_json(tmp_path / "public-pages/news/search_index.json", [legacy])
    source = tmp_path / "daily-news/data.json"
    write_json(source, daily_payload(summary="first"))
    first = build(tmp_path)
    managed = next(row for row in first if row["url"] == "https://example.com/model")
    assert managed["capture_schema"] == 1
    managed["custom"] = "keep"
    write_json(tmp_path / "public-pages/news/search_index.json", first)
    second = daily_payload(title="訂正された日本語見出し", summary="訂正済み要約", url="https://example.com/model?utm_source=new")
    second["items"].append({"title": "do not replace legacy", "url": legacy["url"], "summary": "new"})
    write_json(source, second)
    result = build(tmp_path)
    assert len(result) == 2
    assert legacy in result
    managed = next(row for row in result if row.get("capture_schema") == 1)
    assert managed["title"] == "訂正された日本語見出し"
    assert managed["summary"] == "訂正済み要約"
    assert managed["custom"] == "keep"


def test_new_real_daily_article_takes_precedence_over_legacy_aggregate(tmp_path):
    write_json(tmp_path / "daily-news/data.json", daily_payload())
    write_json(tmp_path / "public-pages/news/2026-10-09.json", {"articles": [{"title": "aggregate title", "url": "https://example.com/model"}]})
    assert build(tmp_path)[0]["title"] == "本日のモデル"


@pytest.mark.parametrize("source", ["/srv/repo/input/day/1009.txt", r"C:\repo\input\day\1009.txt", "input/day/1009.txt"])
def test_new_legacy_daily_aggregate_is_not_treated_as_an_article(tmp_path, source):
    aggregate = {"date": "2026-10-09", "source": source, "count": 1, "items": [
        {"title": "2026年10月09日のAIニュース速報", "url": "https://example.com/first-of-many", "summary": "A whole daily bulletin", "extracted_urls_count": 20, "content_sections": 80}
    ]}
    write_json(tmp_path / "public-pages/news/2026-10-09.json", aggregate)
    assert build(tmp_path) == []


def test_already_indexed_daily_aggregate_remains_exactly_preserved(tmp_path):
    historical = {"date": "2026-10-09", "title": "2026年10月09日のAIニュース速報", "url": "https://example.com/first-of-many", "summary": "legacy preserved"}
    write_json(tmp_path / "public-pages/news/search_index.json", [historical])
    write_json(tmp_path / "public-pages/news/2026-10-09.json", {"date": "2026-10-09", "source": "/srv/repo/input/day/1009.txt", "count": 1, "items": [dict(historical, summary="changed aggregate")]})
    assert build(tmp_path) == [historical]


def test_unmarked_legacy_slide_metadata_is_immutable_when_html_differs(tmp_path):
    historical = {"date": "2026-10-08", "title": "Published legacy title", "url": "/presentations/day_slides/day_slide_2026_10_08.html", "type": "slide", "summary": "Published summary", "custom": [1, 2]}
    write_json(tmp_path / "public-pages/news/search_index.json", [historical])
    slide = tmp_path / "presentations/day_slides/day_slide_2026_10_08.html"
    slide.parent.mkdir(parents=True)
    slide.write_text('<title>Newly changed HTML title</title><meta name="description" content="Revised description">')
    assert build(tmp_path) == [historical]


def test_new_slides_are_explicitly_marked_and_can_refresh_later(tmp_path):
    slide = tmp_path / "presentations/day_slides/day_slide_2026_10_09.html"
    slide.parent.mkdir(parents=True)
    slide.write_text('<title>First version</title>')
    first = build(tmp_path)
    assert first[0]["slide_schema"] == 1
    write_json(tmp_path / "public-pages/news/search_index.json", first)
    slide.write_text('<title>Corrected version</title>')
    second = build(tmp_path)
    assert len(second) == 1
    assert second[0]["title"] == "Corrected version"
    assert (second[0]["date"], second[0]["url"]) == (first[0]["date"], first[0]["url"])


def test_all_legacy_corpus_rows_survive_full_slide_metadata_difference(tmp_path):
    """Simulate a full checkout whose legacy HTML metadata differs everywhere."""
    baseline_path = Path(__file__).resolve().parents[1] / "public-pages/news/search_index.json"
    historical = [row for row in json.loads(baseline_path.read_text(encoding="utf-8"))
                  if row.get("capture_schema") != 1 and row.get("slide_schema") != 1]
    write_json(tmp_path / "public-pages/news/search_index.json", historical)
    for row in historical:
        if row.get("type") == "slide":
            slide = tmp_path / row["url"].lstrip("/")
            slide.parent.mkdir(parents=True, exist_ok=True)
            slide.write_text('<title>Different metadata</title><meta name="description" content="Different summary">')
    result = build(tmp_path)
    assert len(result) == len(historical)
    assert all(row in result for row in historical)


@pytest.mark.parametrize("meta", [
    '<meta content="Japanese &amp; English summary" name="description"/>',
    "<META CONTENT='Japanese &amp; English summary' data-extra='value' NAME='Description'>",
    '<meta name = "description"\ncontent = "Japanese &amp; English summary">',
])
def test_slide_description_is_independent_of_attribute_order_and_case(tmp_path, meta):
    slide = tmp_path / "day_slide_2026_09_14.html"
    slide.write_text(f'<title>A real slide</title>{meta}', encoding="utf-8")
    assert extract_slide_record(slide)["summary"] == "Japanese & English summary"


def test_new_slide_with_description_is_byte_idempotent_on_repeat_build(tmp_path):
    slide = tmp_path / "presentations/day_slides/day_slide_2026_10_09.html"
    slide.parent.mkdir(parents=True)
    slide.write_text('<title>New slide</title><meta name="description" content="Stable summary">')
    search.write_index(tmp_path)
    output = tmp_path / "public-pages/news/search_index.json"
    before = output.read_bytes()
    search.write_index(tmp_path)
    assert output.read_bytes() == before
