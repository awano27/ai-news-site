from datetime import datetime, timedelta

import sync_daily_ai_news as sync


def test_parse_time_info_uses_reference_time():
    reference = datetime(2026, 2, 11, 12, 0, 0)

    parsed = sync.parse_time_info("3日前", now=reference)

    assert parsed == reference - timedelta(days=3)


def test_extract_news_items_from_news_card():
    html = """
    <article class="news-card" data-category="ツール">
      <a class="news-card__title" href="/posts/sample">Sample Tool Launch</a>
      <p class="news-card__summary">A practical release note.</p>
      <span class="news-card__source">Example Source</span>
      <span class="news-card__time">2日前</span>
      <ul class="news-card__taglist"><li>tool</li></ul>
    </article>
    """
    reference = datetime(2026, 2, 11, 8, 30, 0)

    items = sync.extract_news_items(html, now=reference, base_url=sync.SOURCE_URL)

    assert len(items) == 1
    item = items[0]
    assert item["title"] == "Sample Tool Launch"
    assert item["url"] == "https://awano27.github.io/posts/sample"
    assert item["category"] == "ツール"
    assert item["estimated_date"] == "2026-02-09"
    assert item["rank"] == 1


def test_extract_news_items_from_card_fallback():
    html = """
    <div class="card">
      <h3 class="card-title"><a href="https://example.com/news">Fallback Title</a></h3>
      <p class="card-text">Fallback summary.</p>
      <small class="text-muted">1時間前</small>
    </div>
    """
    reference = datetime(2026, 2, 11, 10, 0, 0)

    items = sync.extract_news_items(html, now=reference)

    assert len(items) == 1
    item = items[0]
    assert item["title"] == "Fallback Title"
    assert item["url"] == "https://example.com/news"
    assert item["category"] == sync.DEFAULT_CATEGORY
    assert item["estimated_datetime"] == "2026-02-11T09:00:00"


def test_group_news_by_date_sorts_by_score_and_resets_rank():
    items = [
        {"title": "B", "estimated_date": "2026-02-10", "score": 60, "rank": 5},
        {"title": "A", "estimated_date": "2026-02-10", "score": 90, "rank": 4},
    ]

    grouped = sync.group_news_by_date(items)

    assert list(grouped.keys()) == ["2026-02-10"]
    assert grouped["2026-02-10"][0]["title"] == "A"
    assert grouped["2026-02-10"][0]["rank"] == 1
    assert grouped["2026-02-10"][1]["rank"] == 2


def test_create_archive_format_keeps_expected_shape():
    items = [
        {
            "title": "Top",
            "url": "https://example.com/top",
            "summary": "Top summary",
            "source": "Example",
            "category": "ビジネス",
            "time_info": "1日前",
            "estimated_date": "2026-02-10",
            "estimated_datetime": "2026-02-10T00:00:00",
            "score": 88,
            "rank": 1,
        },
        {
            "title": "Second",
            "url": "https://example.com/second",
            "summary": "Second summary",
            "source": "",
            "category": "ツール",
            "time_info": "1日前",
            "estimated_date": "2026-02-10",
            "estimated_datetime": "2026-02-10T00:00:00",
            "score": 70,
            "rank": 2,
        },
    ]

    archive = sync.create_archive_format("2026-02-10", items)

    assert archive is not None
    assert archive["date"] == "2026-02-10"
    assert archive["source"] == sync.SOURCE_URL
    assert archive["count"] == 2
    assert archive["items"][0]["title"] == "AI News Digest 2026-02-10"
    assert archive["items"][0]["category_breakdown"]["business"] == 1
    assert archive["items"][0]["category_breakdown"]["tools"] == 1
