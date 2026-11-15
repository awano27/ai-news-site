import re
from pathlib import Path

from scripts.build_sitemap import BASE_URL, ROOT, collect_urls, opts_out_of_indexing
from src.auto_collect.daily_news_page import archive_page_html


def listed() -> set[str]:
    return {entry["loc"].removeprefix(BASE_URL + "/") for entry in collect_urls()}


def local_file(rel: str) -> Path:
    return ROOT / (rel + "index.html" if rel == "" or rel.endswith("/") else rel)


def test_no_listed_page_opts_out_of_indexing():
    offenders = [rel for rel in listed() if opts_out_of_indexing(local_file(rel))]
    assert offenders == []


def test_dated_ranking_snapshots_yield_to_the_latest_page():
    urls = listed()
    assert not [u for u in urls if re.search(r"presentations/ai_ranking_report_\d{8}\.html", u)]
    assert "presentations/ai_ranking_report_latest.html" in urls


def test_every_dated_day_slide_is_listed_and_no_variant_is():
    slides = {p.name for p in (ROOT / "presentations/day_slides").glob("day_slide_*.html")}
    dated = {n for n in slides if re.fullmatch(r"day_slide_\d{4}_\d{2}_\d{2}\.html", n)}
    in_sitemap = {u.rsplit("/", 1)[1] for u in listed() if u.startswith("presentations/day_slides/")}
    assert in_sitemap == dated


def test_every_daily_report_is_listed():
    reports = {p.name for p in (ROOT / "presentations/daily_reports").glob("auto_daily_report_*.html")}
    in_sitemap = {u.rsplit("/", 1)[1] for u in listed() if u.startswith("presentations/daily_reports/")}
    assert reports and reports <= in_sitemap


def test_off_topic_presentations_are_not_listed():
    urls = listed()
    for name in ("sp500_trump_chart_2026v2.html", "infra_plan_proposal.html",
                 "dashboard_resn.html", "index_modern.html"):
        assert f"presentations/{name}" not in urls


ARCHIVE_URL = "https://visionhub.jp/daily-news/archive/2026-11-14.html"
LATEST_HEAD = (
    '<head>\n<meta property="og:url" content="https://visionhub.jp/daily-news/">\n'
    '<link rel="canonical" href="https://visionhub.jp/daily-news/">\n</head>'
)


def test_archive_snapshot_names_itself_as_canonical():
    out = archive_page_html(LATEST_HEAD, "2026-11-14")
    assert f'<link rel="canonical" href="{ARCHIVE_URL}">' in out
    assert f'<meta property="og:url" content="{ARCHIVE_URL}">' in out
    assert 'href="https://visionhub.jp/daily-news/"' not in out


def test_archive_snapshot_without_canonical_gains_exactly_one():
    out = archive_page_html("<head>\n<title>t</title>\n</head><body></body>", "2026-11-14")
    assert out.count('rel="canonical"') == 1
    assert f'href="{ARCHIVE_URL}"' in out
    assert archive_page_html(out, "2026-11-14") == out


def test_committed_archive_snapshots_are_self_canonical():
    for path in (ROOT / "daily-news/archive").glob("20*.html"):
        head = path.read_text(encoding="utf-8")[:20_000]
        assert f'<link rel="canonical" href="https://visionhub.jp/daily-news/archive/{path.name}">' in head, path.name
