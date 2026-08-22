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
