import json
from datetime import date

from src.auto_collect import report_dashboard as rd
from src.auto_collect.collectors import model_watch as mw

RSS = """<rss><channel>
<item><title><![CDATA[Introducing GPT-7]]></title><link>https://openai.com/index/gpt-7</link><pubDate>Thu, 15 Oct 2026 19:00:00 GMT</pubDate></item>
<item><title><![CDATA[Amp puts AI agents to work with OpenAI models]]></title><link>https://openai.com/index/amp</link><pubDate>Thu, 15 Oct 2026 12:00:00 GMT</pubDate></item>
<item><title><![CDATA[GPT-6 and Intelligent UI]]></title><link>https://openai.com/index/gpt-6</link><pubDate>Wed, 07 Oct 2026 12:00:00 GMT</pubDate></item>
</channel></rss>"""

CHANGELOG = """<h2 id="10-15-2026">October 15, 2026</h2><ul><li><p><strong>Gemini 3.7 Flash deprecation</strong>: shuts down on
<b>December 31, 2026</b>.</p></li></ul><h2>October 14, 2026</h2><ul><li>Fast mode for Claude Opus 5.5 is now available.</li></ul>"""

CARDS = """<div><h2>Featured headline</h2><time>Oct 15, 2026</time><p>body</p></div>
<a><time>Oct 9, 2026</time><h4>Introducing Grok Voice 3.0</h4></a>"""


def test_rss_and_dated_html_parsers():
    assert [e["title"] for e in mw.parse_rss(RSS)][:1] == ["Introducing GPT-7"]
    entries = mw.parse_dated_html(CHANGELOG)
    assert [(e["date"], e["title"]) for e in entries] == [
        ("2026-10-15", "Gemini 3.7 Flash deprecation"),
        ("2026-10-14", "Fast mode for Claude Opus 5.5 is now available."),
    ]  # the in-sentence December date is not an entry
    assert [e["title"] for e in mw.parse_dated_html(CARDS)] == ["Featured headline", "Introducing Grok Voice 3.0"]


def test_launch_needs_a_model_name_and_customer_stories_are_ignored():
    assert mw.is_model_news("Introducing GPT-7")
    assert not mw.is_model_news("Amp puts AI agents to work with OpenAI models")
    assert not (mw.LAUNCH_RE.search("Fast mode for Claude Opus 5.5 is now available")
                and mw.NAME_RE.search("Fast mode for Claude Opus 5.5 is now available"))


def _fake_fetch(pages):
    def fetch(url):
        if url not in pages:
            raise ConnectionError(url)
        return pages[url]
    return fetch


def test_build_watch_statuses_from_dated_sources():
    catalogue = {"data": [
        {"id": "google/gemini-5", "name": "Gemini 5", "created": 1760486400},  # 2025-10-15 UTC -> old
        {"id": "x-ai/grok-5", "name": "Grok 5", "created": 1792022400},  # 2026-10-15 UTC
        {"id": "x-ai/grok-5:batch", "created": 1792022400},
    ]}
    fetch = _fake_fetch({
        mw.OPENROUTER_URL: json.dumps(catalogue),
        "https://openai.com/news/rss.xml": RSS,
        "https://ai.google.dev/gemini-api/docs/changelog": CHANGELOG,
        "https://blog.google/technology/ai/rss/": "<rss></rss>",
    })
    watch = mw.build_watch(date(2026, 10, 15), fetch=fetch)
    by = {v["key"]: v for v in watch["vendors"]}

    assert by["openai"]["status"] == "launch"
    assert by["google"]["status"] == "update"
    assert by["xai"]["status"] == "launch" and [m["id"] for m in by["xai"]["new_models"]] == ["x-ai/grok-5"]
    assert by["anthropic"]["status"] == "error" and by["anthropic"]["errors"]

    html = rd.render_model_watch(watch)
    assert 'id="model-watch"' in html and "新モデル" in html and "取得失敗" in html
    assert rd.watch_summary(watch).startswith("モデル監視：OpenAI・xAI (Grok) に新モデル")
