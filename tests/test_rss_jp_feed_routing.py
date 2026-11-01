"""JP feeds (ITmedia AI+, GIGAZINE) must reach the article pool only through
JPCollector, whose JP_AI_KEYWORDS filter drops non-AI GIGAZINE rows.

Feeds are served from inline RSS fixtures through a fake requests session;
no network. The collectors parse with xml.etree, so the fixtures are raw RSS 2.0.
"""

from datetime import date

import pytest

from src.auto_collect import dedup
from src.auto_collect.collectors.jp_collector import JPCollector
from src.auto_collect.collectors.rss_collector import RSSAutoCollector
from src.auto_collect.config import EN_RSS_FEEDS, JP_RSS_FEEDS
from src.auto_collect.processor import LLMProcessor

TARGET = date(2026, 10, 31)
PUBDATE = "Fri, 31 Oct 2026 10:22:00 +0900"

ITMEDIA_URL = next(f["url"] for f in JP_RSS_FEEDS if f["name"] == "ITmedia AI+")
GIGAZINE_URL = next(f["url"] for f in JP_RSS_FEEDS if f["name"] == "GIGAZINE")
OPENAI_URL = next(f["url"] for f in EN_RSS_FEEDS if f["name"] == "OpenAI")

ITMEDIA_BODY = (
    "NTTデータは10月31日、生成AIで社内文書を要約する新サービスを11月から提供すると発表した。"
    "大規模言語モデルを自社データセンターで運用し、月額料金は10万円から。"
)
POKEMON_TITLE = "ポケモンセンターとコラボしたエレキギターが登場、ピカチュウの刺しゅう入り"
POKEMON_BODY = "ポケモンセンターオンラインで予約受付中。本体はメイプル材で、価格は9万円。"
GIGAZINE_AI_TITLE = "Googleが「Gemini 3」を発表、動画理解の性能が大幅に向上"
GIGAZINE_AI_BODY = "Googleは新しい大規模言語モデルを発表した。コンテキスト長は200万トークン。"


def _rss(items):
    entries = "".join(
        f"<item><title>{title}</title><link>{link}</link>"
        f"<description>{body}</description><pubDate>{PUBDATE}</pubDate></item>"
        for title, link, body in items
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<rss version="2.0"><channel><title>t</title>{entries}</channel></rss>'
    ).encode("utf-8")


FIXTURES = {
    ITMEDIA_URL: _rss([
        ("NTTデータ、生成AI要約サービスを11月提供", "https://www.itmedia.co.jp/aiplus/articles/2610/31/news001.html", ITMEDIA_BODY),
    ]),
    GIGAZINE_URL: _rss([
        (POKEMON_TITLE, "https://gigazine.net/news/20261031-pokemon-center-guitar/", POKEMON_BODY),
        (GIGAZINE_AI_TITLE, "https://gigazine.net/news/20261031-gemini-3/", GIGAZINE_AI_BODY),
    ]),
    OPENAI_URL: _rss([
        ("Introducing GPT-6", "https://openai.com/index/gpt-6/", "GPT-6 is our most capable model, available today in the API."),
    ]),
}


class _Response:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class _Session:
    def __init__(self):
        self.urls = []

    def get(self, url, **_kwargs):
        self.urls.append(url)
        # Unknown feeds (other EN sources) are empty rather than errors.
        return _Response(FIXTURES.get(url, _rss([])))


def _offline(collector):
    collector.REQUEST_DELAY = 0
    collector.session = _Session()
    return collector


class _SilentProvider:
    """Available but answers nothing, so rows with a body fall back with
    provider_unavailable while bodiless rows fall back with
    source_context_missing. Lets us check the context gate without an LLM."""
    available = True
    name = "silent"
    last_error = "provider_unavailable"

    def chat(self, _prompt):
        return None


def _pool():
    rss = _offline(RSSAutoCollector()).collect(TARGET)
    jp = _offline(JPCollector()).collect(TARGET)
    return dedup.deduplicate(rss + jp)


def test_rss_auto_collector_fetches_only_english_feeds():
    collector = _offline(RSSAutoCollector())
    rows = collector.collect(TARGET)

    assert ITMEDIA_URL not in collector.session.urls
    assert GIGAZINE_URL not in collector.session.urls
    assert {r["rss_source"] for r in rows} == {"OpenAI"}


def test_non_ai_gigazine_article_is_excluded_from_pool():
    titles = [r["name"] for r in _pool()]

    assert POKEMON_TITLE not in titles
    assert GIGAZINE_AI_TITLE in titles


def test_itmedia_rows_keep_body_source_and_date_via_jp_collector():
    pool = _pool()
    itmedia = [r for r in pool if r["rss_source"] == "ITmedia AI+"]

    assert len(itmedia) == 1
    row = itmedia[0]
    assert row["description"] == ITMEDIA_BODY
    assert row["tagline"] == ITMEDIA_BODY[:200]
    assert row["published_at"] == "2026-10-31T10:22:00+09:00"
    # URL normalisation belongs to scripts/collectors/base.py; only the article identity matters here.
    assert row["links"]["official"].endswith("itmedia.co.jp/aiplus/articles/2610/31/news001.html")
    assert "merged_from" not in row  # single copy, no second fetch of the same feed

    processed = LLMProcessor(_SilentProvider())._process_one(row)
    assert processed["processing_error"] != "source_context_missing"
    assert processed["source"] == "ITmedia AI+"
    assert processed["published_at"] == "2026-10-31T10:22:00+09:00"


def test_jp_feeds_are_fetched_once_across_collectors():
    rss = _offline(RSSAutoCollector())
    jp = _offline(JPCollector())
    rss.collect(TARGET)
    jp.collect(TARGET)

    fetched = rss.session.urls + jp.session.urls
    assert fetched.count(ITMEDIA_URL) == 1
    assert fetched.count(GIGAZINE_URL) == 1
