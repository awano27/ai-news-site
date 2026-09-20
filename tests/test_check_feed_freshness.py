from __future__ import annotations

from datetime import date
from pathlib import Path

from scripts.check_feed_freshness import (
    check,
    feed_updated_date,
    main,
    newest_feed_entry_date,
    newest_slide_date,
)


def _feed(updated: str, entry_dates: list[str]) -> str:
    entries = "".join(
        "<entry>"
        f'<link href="https://visionhub.jp/presentations/day_slides/day_slide_{d.replace("-", "_")}.html" rel="alternate"/>'
        f"<updated>{d}T07:00:00+09:00</updated>"
        "</entry>"
        for d in entry_dates
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        f"<updated>{updated}T07:00:00+09:00</updated>"
        f"{entries}</feed>"
    )


def _slides(tmp_path: Path, dates: list[str]) -> Path:
    slides = tmp_path / "day_slides"
    slides.mkdir()
    for d in dates:
        (slides / f"day_slide_{d.replace('-', '_')}.html").write_text("<html></html>", encoding="utf-8")
    (slides / "day_slide_skills.html").write_text("<html></html>", encoding="utf-8")
    return slides


def test_newest_slide_date_ignores_non_dated_files(tmp_path: Path):
    slides = _slides(tmp_path, ["2026-09-18", "2026-09-20", "2026-09-19"])
    assert newest_slide_date(slides) == date(2026, 9, 20)


def test_newest_feed_entry_date_and_updated():
    text = _feed("2026-09-20", ["2026-09-20", "2026-09-19"])
    assert newest_feed_entry_date(text) == date(2026, 9, 20)
    assert feed_updated_date(text) == date(2026, 9, 20)


def test_check_passes_when_feed_matches_newest_slide(tmp_path: Path):
    slides = _slides(tmp_path, ["2026-09-19", "2026-09-20"])
    feed = tmp_path / "feed.xml"
    feed.write_text(_feed("2026-09-20", ["2026-09-20", "2026-09-19"]), encoding="utf-8")
    assert check(feed, slides) == []
    assert main(["--feed", str(feed), "--slides", str(slides)]) == 0


def test_check_fails_when_feed_lags_behind_slides(tmp_path: Path):
    slides = _slides(tmp_path, ["2026-08-21", "2026-09-20"])
    feed = tmp_path / "feed.xml"
    feed.write_text(_feed("2026-08-21", ["2026-08-21"]), encoding="utf-8")
    problems = check(feed, slides)
    assert len(problems) == 2
    assert "older than newest slide 2026-09-20" in problems[0]
    assert main(["--feed", str(feed), "--slides", str(slides)]) == 1


def test_check_fails_when_feed_has_no_entries(tmp_path: Path):
    slides = _slides(tmp_path, ["2026-09-20"])
    feed = tmp_path / "feed.xml"
    feed.write_text(_feed("2026-09-20", []), encoding="utf-8")
    assert check(feed, slides) == ["feed has no day-slide entries"]


def test_check_reports_missing_feed(tmp_path: Path):
    slides = _slides(tmp_path, ["2026-09-20"])
    assert check(tmp_path / "missing.xml", slides)[0].startswith("feed missing")
