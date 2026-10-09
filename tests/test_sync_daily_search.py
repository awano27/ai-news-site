"""Real file-boundary coverage for durable daily capture."""
import importlib
import json
from pathlib import Path

import pytest

from tests.test_build_search_index import daily_payload, write_json


def sync(root):
    module = importlib.import_module("scripts.sync_daily_search")
    return module.sync_daily_search(root)


def test_sync_captures_real_articles_counts_and_preserves_legacy_archive(tmp_path):
    legacy = tmp_path / "public-pages/news/2026-10-09.json"
    write_json(legacy, {"articles": [{"title": "historic aggregate", "url": "https://example.com/legacy"}]})
    legacy_before = legacy.read_bytes()
    current = daily_payload(date="2026-10-08T18:00:00Z", summary="記事の日本語の要約")
    current["items"].append({"title": "手選び", "url": "https://x.com/example/status/1", "type": "x", "body": "日本語投稿", "source": "X"})
    write_json(tmp_path / "daily-news/data.json", current)
    sync(tmp_path)
    capture_path = tmp_path / "public-pages/news/daily/2026-10-09.json"
    capture = json.loads(capture_path.read_text())
    assert capture["schema_version"] == 1
    assert capture["date"] == "2026-10-09"
    assert (capture["total"], capture["news_count"], capture["x_count"]) == (2, 1, 1)
    assert capture["sources"]["X"] == 1
    assert capture["items"][0]["published_at"] == "2026-10-08T18:00:00Z"
    assert capture["items"][0]["url"] == current["items"][0]["url"]
    assert capture["items"][0]["summary"] == "記事の日本語の要約"
    assert capture["items"][1]["summary"] == "日本語投稿"
    assert legacy.read_bytes() == legacy_before
    assert not (tmp_path / "news/latest.json").exists()
    assert len(json.loads((tmp_path / "public-pages/news/search_index.json").read_text())) == 3


def test_sync_is_byte_idempotent_and_preserves_richer_x(tmp_path):
    source = tmp_path / "daily-news/data.json"
    local = daily_payload()
    local["items"].append({"title": "X", "url": "https://x.com/a/status/1", "type": "x"})
    write_json(source, local)
    sync(tmp_path)
    paths = [tmp_path / "public-pages/news/daily/2026-10-09.json", tmp_path / "public-pages/news/search_index.json"]
    before = [path.read_bytes() for path in paths]
    sync(tmp_path)
    assert [path.read_bytes() for path in paths] == before
    write_json(source, daily_payload(title="cloud"))
    sync(tmp_path)
    assert [path.read_bytes() for path in paths] == before


def test_sync_next_day_preserves_previous_snapshot_and_search_rows(tmp_path):
    source = tmp_path / "daily-news/data.json"
    write_json(source, daily_payload())
    sync(tmp_path)
    old = tmp_path / "public-pages/news/daily/2026-10-09.json"
    before = old.read_bytes()
    write_json(source, daily_payload("2026-10-10"))
    sync(tmp_path)
    assert old.read_bytes() == before
    assert (tmp_path / "public-pages/news/daily/2026-10-10.json").exists()
    assert len(json.loads((tmp_path / "public-pages/news/search_index.json").read_text())) == 2


@pytest.mark.parametrize("bad", [{}, {"date": "2026-99-99", "items": []}, {"date": "2026-10-09", "items": "invalid"}, {"date": "2026-10-09", "items": []}, {"date": "2026-10-09", "items": [{"title": "unsafe", "url": "javascript:alert(1)"}]}])
def test_invalid_capture_fails_without_changing_published_files(tmp_path, bad):
    source = tmp_path / "daily-news/data.json"
    write_json(source, daily_payload())
    sync(tmp_path)
    published = tmp_path / "public-pages/news"
    before = {path.relative_to(published): path.read_bytes() for path in published.rglob("*.json")}
    write_json(source, bad)
    with pytest.raises(ValueError):
        sync(tmp_path)
    assert {path.relative_to(published): path.read_bytes() for path in published.rglob("*.json")} == before


def test_index_validation_happens_before_snapshot_write(tmp_path):
    write_json(tmp_path / "daily-news/data.json", daily_payload())
    output = tmp_path / "public-pages/news/search_index.json"
    write_json(output, {"wrong": "shape"})
    before = output.read_bytes()
    with pytest.raises(ValueError):
        sync(tmp_path)
    assert output.read_bytes() == before
    assert not (tmp_path / "public-pages/news/daily/2026-10-09.json").exists()


def test_counts_are_computed_from_valid_unique_items(tmp_path):
    data = daily_payload(source="Official")
    data["total"] = 999
    data["x_count"] = 999
    data["items"].extend([dict(data["items"][0], url="https://example.com/model?utm_source=tracking"), {"title": "unsafe", "url": "javascript:x"}])
    write_json(tmp_path / "daily-news/data.json", data)
    sync(tmp_path)
    captured = json.loads((tmp_path / "public-pages/news/daily/2026-10-09.json").read_text())
    assert captured["total"] == 1
    assert captured["news_count"] == 1
    assert captured["x_count"] == 0
    assert captured["sources"] == {"Official": 1}


def test_snapshot_records_lossless_capture_count_provenance(tmp_path):
    data = daily_payload()
    data["items"].extend([dict(data["items"][0], url="https://example.com/model?utm_source=mail"), {"title": "bad URL", "url": "javascript:x"}])
    write_json(tmp_path / "daily-news/data.json", data)
    sync(tmp_path)
    path = tmp_path / "public-pages/news/daily/2026-10-09.json"
    capture = json.loads(path.read_text())
    assert capture["source_item_count"] == 3
    assert capture["duplicate_item_count"] == 1
    assert capture["excluded_item_count"] == 1
    assert capture["total"] + capture["duplicate_item_count"] + capture["excluded_item_count"] == capture["source_item_count"]
    before = path.read_bytes()
    sync(tmp_path)
    assert path.read_bytes() == before


@pytest.mark.parametrize("field,value", [("summary", ["not", "text"]), ("source", {"nested": "value"}), ("type", ["news"])])
def test_malformed_article_metadata_fails_before_publish(tmp_path, field, value):
    source = tmp_path / "daily-news/data.json"
    write_json(source, daily_payload())
    sync(tmp_path)
    published = tmp_path / "public-pages/news"
    before = {path.relative_to(published): path.read_bytes() for path in published.rglob("*.json")}
    write_json(source, daily_payload(**{field: value}))
    with pytest.raises(ValueError):
        sync(tmp_path)
    assert {path.relative_to(published): path.read_bytes() for path in published.rglob("*.json")} == before
