from __future__ import annotations

import json
import re
from html.parser import HTMLParser
import shutil
import subprocess
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]


class Homepage(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def by_id(self, elem_id):
        matches = [(tag, attrs) for tag, attrs in self.elements if attrs.get("id") == elem_id]
        assert len(matches) == 1, f"Expected unique #{elem_id}"
        return matches[0]


def assert_archive_at_page_end(html):
    page = BeautifulSoup(html, "html.parser")
    main = page.find("main", id="main")
    archive = page.find("section", id="archive")
    assert archive is not None and archive.parent is main
    assert main.find_all(recursive=False)[-1] is archive
    assert archive.find_previous_sibling("section").get("id") == "resources"
    assert main.find_next_sibling().name == "footer"
    assert len(page.select("#archive")) == 1
    assert archive.find("h2").get_text(strip=True) == "過去のすべてのAIニュースを、ここから。"
    assert {a["href"] for a in archive.find_all("a")} == {
        "presentations/news_archive.html", "presentations/day_slides_index.html",
        "presentations/daily_reports_archive.html", "presentations/ai_ranking_report_latest.html",
    }
    assert all(a.get_text(strip=True) for a in archive.find_all("a"))
    for elem_id in ("statSlides", "statItems", "statUpdated"):
        assert len(page.select("#" + elem_id)) == 1
    search = main.select_one(".home-search")
    assert search.find("h2", id="searchHeading") is not None
    assert {a["href"] for a in search.find_all("a")} == {"daily-news/", "presentations/news_archive.html"}
    assert list(main.children).index(search) < list(main.children).index(archive)


def test_archive_is_last_main_content_with_accessible_search_links():
    assert_archive_at_page_end((ROOT / "index.html").read_text(encoding="utf-8"))


def assert_comparison_promo_removed(html):
    page = BeautifulSoup(html, "html.parser")
    assert page.select_one("#newsComparisonCard") is None
    assert page.select_one(".news-comparison-feature") is None
    assert page.select_one("#news-comparison-title") is None
    assert "news-comparison-card" not in html
    assert page.select_one("#featured-reports").find_next_sibling().get("id") == "daily-briefing"


def test_comparison_promo_is_removed_without_an_empty_section():
    assert_comparison_promo_removed((ROOT / "index.html").read_text(encoding="utf-8"))


def test_dated_comparison_article_and_sitemap_entry_remain_available():
    article_path = "presentations/ai-news-comparison-2026-10-07.html"
    article = BeautifulSoup((ROOT / article_path).read_text(encoding="utf-8"), "html.parser")
    assert "10/7 AIニュース厳選5件・通常版との比較" in article.title.get_text()
    assert article.find("h1") is not None
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://visionhub.jp/" + article_path in sitemap


def assert_entry_contract(html):
    assert_comparison_promo_removed(html)
    assert_archive_at_page_end(html)
    page = Homepage(html)
    assert [a.get("id") for t, a in page.elements if t == "h1"] == ["heroIdentity"]
    assert page.by_id("heroDescription")[0] == "p"
    for elem_id, destination in {
        "heroNewsBtn": "daily-news/",
        "comparisonCard": "presentations/ai_coding_agents_guide.html",
        "implementationCard": "articles/claim-evidence-design.html",
    }.items():
        tag, attrs = page.by_id(elem_id)
        assert tag == "a"
        assert attrs.get("href") == destination
    today_tag, today_attrs = page.by_id("heroTodayBtn")
    assert today_tag == "a"
    assert today_attrs.get("href", "").startswith("presentations/day_slides/day_slide_")
    assert "btn-primary" in today_attrs.get("class", "").split()
    assert not [a for t, a in page.elements if a.get("id") == "heroArticleBtn"]
    assert "btn-ghost" in page.by_id("heroNewsBtn")[1].get("class", "").split()
    ids = [attrs.get("id") for tag, attrs in page.elements if tag == "a"]
    assert ids.index("heroTodayBtn") < ids.index("dailyReportLink") < ids.index("heroNewsBtn")
    assert page.by_id("heroTwist")[0] == "h3"
    assert page.by_id("heroWhy")[0] == "p"
    return page


def test_build_homepage_accepts_marked_latest_slide_fallbacks(tmp_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the homepage build integration test")

    script = tmp_path / "scripts" / "build-homepage-latest.js"
    script.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "build-homepage-latest.js", script)
    shutil.copy2(ROOT / "index.html", tmp_path / "index.html")

    newest_slide = max((ROOT / "presentations" / "day_slides").glob("day_slide_????_??_??.html"))
    slide_dir = tmp_path / "presentations" / "day_slides"
    slide_dir.mkdir(parents=True)
    shutil.copy2(newest_slide, slide_dir / newest_slide.name)
    stale_api = tmp_path / "public-pages" / "api" / "auto_daily_report"
    stale_api.mkdir(parents=True)
    (stale_api / "latest.json").write_text(
        json.dumps({"date": "2026-09-04", "headlines": [{"title": "古い入力"}]}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [node, str(script)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    updated = (tmp_path / "index.html").read_text(encoding="utf-8")
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    assert_entry_contract(updated)
    # A no-JS fallback must close its own card before leaving noscript.
    for fragment in re.findall(r"<noscript>(.*?)</noscript>", updated, re.S):
        tags = re.findall(r"</?div\b[^>]*>", fragment)
        depth = 0
        for tag in tags:
            depth += -1 if tag.startswith("</") else 1
            assert depth >= 0
        assert depth == 0, "Unclosed div in noscript fallback"

    # Daily data updates only the trends card fields, while the stable entry
    # point and purpose-specific cards remain intact after regeneration.
    assert 'id="heroTwist"' in updated
    assert 'id="heroWhy"' in updated
    assert 'id="heroSlideBtn"' in updated
    assert 'id="todaySlideDate"' in updated
    assert 'href="presentations/day_slides/' + newest_slide.name + '"' in updated
    assert source.split('id="heroIdentity"', 1)[1].split("</h1>", 1)[0] in updated
    generated = json.loads((tmp_path / "news" / "latest.json").read_text(encoding="utf-8"))
    assert generated["generated_at"].startswith(newest_slide.stem.removeprefix("day_slide_").replace("_", "-"))
    assert generated["highlight"]["sources"][0]["url"].endswith(newest_slide.name)


def test_build_homepage_does_not_fabricate_output_without_a_slide(tmp_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the homepage build integration test")

    script = tmp_path / "scripts" / "build-homepage-latest.js"
    script.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "build-homepage-latest.js", script)
    index = tmp_path / "index.html"
    shutil.copy2(ROOT / "index.html", index)
    (tmp_path / "presentations" / "day_slides").mkdir(parents=True)
    news = tmp_path / "news"
    news.mkdir()
    stale = '{"generated_at":"2026-09-04T09:00:00.000000+09:00"}'
    (news / "latest.json").write_text(stale, encoding="utf-8")

    result = subprocess.run(
        [node, str(script)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    updated = index.read_text(encoding="utf-8")
    assert 'href="presentations/day_slides_index.html"' in updated
    assert 'day_slide_2026_09_05.html' not in updated
    assert "公開スライドはまだありません" in updated
    assert "公開スライドなし" in updated
    assert "スライド一覧" in updated
    assert "今日のスライドはありません" in updated
    assert (news / "latest.json").read_text(encoding="utf-8") == stale


def test_build_homepage_recovers_empty_state_when_a_slide_returns(tmp_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the homepage build integration test")

    script = tmp_path / "scripts" / "build-homepage-latest.js"
    script.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "build-homepage-latest.js", script)
    index = tmp_path / "index.html"
    shutil.copy2(ROOT / "index.html", index)
    slide_dir = tmp_path / "presentations" / "day_slides"
    slide_dir.mkdir(parents=True)

    empty = subprocess.run([node, str(script)], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert empty.returncode == 0, empty.stdout + empty.stderr
    assert "公開スライドはまだありません" in index.read_text(encoding="utf-8")

    (slide_dir / "day_slide_2026_09_05.html").write_text(
        '<meta name="description" content="復帰後の要点です。">'
        "<title>復帰テスト | 2026-09-05</title>"
        "<h1>復帰した日次見出し</h1>",
        encoding="utf-8",
    )
    restored = subprocess.run([node, str(script)], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert restored.returncode == 0, restored.stdout + restored.stderr
    updated = index.read_text(encoding="utf-8")
    assert_entry_contract(updated)
    assert "復帰した日次見出し</h3>" in updated
    assert "復帰後の要点です。</p>" in updated
    assert "公開スライドなし" not in updated
    assert "最新スライドを読む" in updated
    # 2026-09-05 is older than the real clock, so the CTA must say 最新 rather than 今日.
    assert "最新のスライドを読む" in updated
    assert "今日のスライドを読む" not in updated
    assert 'href="presentations/day_slides/day_slide_2026_09_05.html"' in updated
    assert 'href="daily-news/"' in updated
    assert 'href="articles/claim-evidence-design.html"' in updated


@pytest.mark.parametrize("old,new", [
    ('id="heroIdentity"', 'id="missingIdentity"'),
    ('id="heroNewsBtn" class="btn btn-ghost" href="daily-news/"', 'id="heroNewsBtn" class="btn btn-ghost" href="#resources"'),
    ('id="heroTodayBtn"', 'id="missingTodayBtn"'),
])
def test_entry_contract_rejects_broken_heading_or_primary_link(old, new):
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_entry_contract(html.replace(old, new, 1))


def test_daily_briefing_independent_dates_and_regeneration(tmp_path):
    script = tmp_path / "scripts/build-homepage-latest.js"
    script.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/build-homepage-latest.js", script)
    shutil.copy2(ROOT / "index.html", tmp_path / "index.html")
    api = tmp_path / "public-pages/api/auto_daily_report/latest.json"
    api.parent.mkdir(parents=True)
    report_dir = tmp_path / "presentations/daily_reports"
    report_dir.mkdir(parents=True)
    (report_dir / "auto_daily_report_2026_10_07.html").write_text("report")
    slide_dir = tmp_path / "presentations/day_slides"
    slide_dir.mkdir()
    (slide_dir / "day_slide_2026_10_06.html").write_text("<title>図解</title><h1>図解</h1>", encoding="utf-8")
    for date in ["2026-10-07", "2026-10-08"]:
        api.write_text(json.dumps({"date": date, "headlines": [
            {"title": f"AIニュース{i}<script>", "score": i, "tldr": "変更点です。", "impact": "開発者に関係します。"} for i in range(4)]}), encoding="utf-8")
        result = subprocess.run([shutil.which("node"), str(script)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        html = (tmp_path / "index.html").read_text(encoding="utf-8")
        fragment = html.split('id="dailyHeadlines"', 1)[1].split('</ol>', 1)[0]
        assert fragment.count('<li>') == 3
        assert '何が変わったか:' in fragment and '誰に関係するか:' in fragment
        assert '&lt;script&gt;' in fragment and '<script>' not in fragment
        assert f'id="dailyReportDate">{date}' in html
        assert 'id="todaySlideDate" class="main-card-date">2026-10-06' in html
    api.write_text('{}')
    subprocess.run([shutil.which("node"), str(script)], check=True, capture_output=True)
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert '主要ニュースは更新待ち' in html
    assert 'id="dailyReportDate">未確認' in html
