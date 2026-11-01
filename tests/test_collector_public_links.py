"""Collected links must be published verbatim; normalisation belongs to dedup only.

itmedia.co.jp drops the path when redirecting to www.itmedia.co.jp, and
youtube.com/watch?v= and news.ycombinator.com/item?id= need their query, so
the URL that readers click must be the one the source gave us.
"""

import xml.etree.ElementTree as ET
from datetime import date

from scripts.collectors.base import BaseCollector
from scripts.collectors.rss import RSSCollector
from src.auto_collect import dedup


class _StubCollector(BaseCollector):
    def __init__(self):
        pass  # no HTTP session needed

    @property
    def source_name(self):
        return "stub"

    def collect(self, target_date=None):
        return []


ITMEDIA = "https://www.itmedia.co.jp/aiplus/article/2610/30/2000002738/"
YOUTUBE = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
HN_ITEM = "https://news.ycombinator.com/item?id=45678901"


def test_create_tool_dict_keeps_official_url_verbatim():
    tool = _StubCollector().create_tool_dict("ITmedia", "tagline", ITMEDIA, ["ai"])
    assert tool["links"]["official"] == ITMEDIA


def test_create_tool_dict_keeps_query_strings_in_official_and_extra_links():
    tool = _StubCollector().create_tool_dict(
        "Video", "tagline", YOUTUBE, ["ai"], extra_links={"hn": HN_ITEM}
    )
    assert tool["links"] == {"official": YOUTUBE, "hn": HN_ITEM}


def test_rss_item_link_reaches_links_official_unchanged():
    target = date(2026, 10, 30)
    rss = ET.fromstring(
        "<rss><channel><item>"
        "<title>生成AI記事</title>"
        f"<link>{ITMEDIA}</link>"
        "<description>desc</description>"
        "<pubDate>Thu, 30 Oct 2026 09:00:00 +0900</pubDate>"
        "</item></channel></rss>"
    )
    collector = RSSCollector.__new__(RSSCollector)
    items = collector._parse_rss(rss, "ITmedia AI+", "AI News", 1, target)
    assert [item["links"]["official"] for item in items] == [ITMEDIA]


def _article(name, url):
    return _StubCollector().create_tool_dict(name, "tagline", url, ["ai"])


def test_dedup_collapses_www_trailing_slash_and_tracking_variants_of_a_raw_url():
    variants = [
        "https://www.example.com/news/story/",
        "https://example.com/news/story",
        "https://www.example.com/news/story?utm_source=rss&utm_medium=feed",
    ]
    # Unrelated titles so only the URL key can merge them.
    titles = ["Quarterly chip exports", "Museum reopens east wing", "Ferry timetable changes"]
    articles = [_article(title, url) for title, url in zip(titles, variants)]
    survivors = dedup.deduplicate(articles)
    assert len(survivors) == 1
    assert survivors[0]["links"]["official"] == variants[0]
    assert survivors[0]["merged_from"] == ["stub"]


def test_dedup_keeps_distinct_youtube_videos_apart():
    articles = [
        _article("Talk one", "https://www.youtube.com/watch?v=aaaaaaaaaaa"),
        _article("Keynote two", "https://www.youtube.com/watch?v=bbbbbbbbbbb"),
    ]
    assert len(dedup.deduplicate(articles)) == 2


def test_dedup_across_sections_matches_raw_url_variants():
    headlines = [{"title": "Crusoe raises", "url": "https://www.example.com/a/b/"}]
    funding = [{"title": "Totally different headline", "url": "https://example.com/a/b?utm_source=x"}]
    kept_headlines, kept_funding, _, _ = dedup.dedup_across_sections(headlines=headlines, funding=funding)
    assert len(kept_headlines) == 1
    assert kept_funding == []
