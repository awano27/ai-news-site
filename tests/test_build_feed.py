from __future__ import annotations

from datetime import date
from pathlib import Path

from scripts.build_feed import (
    atom_updated,
    build_feed_xml,
    collect_entries,
    extract_slide_meta,
    parse_slide_date,
)


def test_parse_slide_date():
    assert parse_slide_date("day_slide_2026_08_21.html") == date(2026, 8, 21)
    assert parse_slide_date("readme.html") is None


def test_extract_title_strips_trailing_date():
    html = (
        "<html><head>"
        "<title>Ox Alpha — stealth frontier | 2026-08-21</title>"
        '<meta name="description" content="A summary.">'
        "</head></html>"
    )
    title, summary = extract_slide_meta(html)
    assert title == "Ox Alpha — stealth frontier"
    assert summary == "A summary."


def test_escape_ampersand_and_lt_in_feed_xml():
    xml = build_feed_xml(
        [
            {
                "title": "A & B <C>",
                "summary": "x < y & z",
                "url": "https://visionhub.jp/presentations/day_slides/day_slide_2026_08_21.html",
                "updated": atom_updated(date(2026, 8, 21)),
            }
        ]
    )
    assert "A &amp; B &lt;C&gt;" in xml
    assert "x &lt; y &amp; z" in xml
    assert "A & B" not in xml
    assert "<C>" not in xml


def test_updated_is_fixed_jst_not_clock():
    assert atom_updated(date(2026, 8, 21)) == "2026-08-21T07:00:00+09:00"
    xml = build_feed_xml(
        [
            {
                "title": "T",
                "summary": "",
                "url": "https://visionhub.jp/presentations/day_slides/day_slide_2026_08_21.html",
                "updated": atom_updated(date(2026, 8, 21)),
            }
        ]
    )
    assert xml.count("2026-08-21T07:00:00+09:00") >= 2
    assert "datetime.now" not in xml


def test_collect_skips_missing_file(tmp_path: Path, capsys):
    ghost = tmp_path / "day_slide_2026_01_01.html"
    # not created
    listed = collect_entries(tmp_path)
    assert listed == []
    ghost.write_text("<html><head><title>Gone | 2026-01-01</title></head></html>", encoding="utf-8")
    ghost.unlink()
    assert collect_entries(tmp_path) == []


def test_collect_skips_slide_without_title(tmp_path: Path):
    p = tmp_path / "day_slide_2026_08_20.html"
    p.write_text("<html><head><meta name='description' content='x'></head></html>", encoding="utf-8")
    assert collect_entries(tmp_path) == []


def test_collect_newest_first_limit_30(tmp_path: Path):
    for day in range(1, 36):
        d = date(2026, 7, day) if day <= 31 else date(2026, 8, day - 31)
        name = f"day_slide_{d:%Y_%m_%d}.html"
        (tmp_path / name).write_text(
            f"<html><head><title>Slide {d.isoformat()} | {d.isoformat()}</title>"
            f'<meta name="description" content="s{day}"></head></html>',
            encoding="utf-8",
        )
    entries = collect_entries(tmp_path)
    assert len(entries) == 30
    assert entries[0]["title"] == "Slide 2026-08-04"
    assert entries[-1]["title"] == "Slide 2026-07-06"
