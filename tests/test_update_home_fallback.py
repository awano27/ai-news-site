from datetime import date
from pathlib import Path

import pytest

from scripts import update_home_fallback as subject


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<title>  &amp; 最新 AI <b>ニュース</b> | 2026-07-09 </title><h1>別題</h1>", "& 最新 AI ニュース"),
        ("<title>  </title><h1>  見出し &amp; 詳細 | 2026-07-09 </h1>", "見出し & 詳細"),
        ("<h1>日付なしの見出し</h1>", "日付なしの見出し"),
        ("<title>" + "長" * 121 + "</title>", None),
        ("<title><span> </span></title><h1> </h1>", None),
    ],
)
def test_extract_slide_title(html, expected):
    assert subject.extract_slide_title(html) == expected


def test_main_refreshes_weekday_and_latest_visible_titles(tmp_path, monkeypatch):
    slides = tmp_path / "slides"
    slides.mkdir()
    (slides / "day_slide_2026_07_09.html").write_text(
        "<title>新しい &amp; 題名 | 2026-07-09</title>", encoding="utf-8"
    )
    index = tmp_path / "index.html"
    index.write_text(
        """<!-- fallback:latest-slide --><span id="heroDate">2026-07-06 · 月</span><!-- fallback:end -->
<!-- fallback:latest-slide --><span id="heroNewsTitle">古い題名 | 2026-07-06</span><!-- fallback:end -->
<!-- fallback:latest-slide --><a class="ranking-card" href="day_slide_2026_07_06.html" aria-label="1位: 古い題名 | 2026-07-06"><!-- fallback:end -->
<!-- fallback:latest-slide --><h3 class="rc-title">古い題名 | 2026-07-06</h3><!-- fallback:end -->
<!-- fallback:latest-slide --><span>最新トピック: 古い題名 | 2026-07-06。<a href="day_slide_2026_07_06.html">今日のスライド</a>または<a href="news_archive.html">アーカイブ</a>からご覧ください。</span><!-- fallback:end -->
<!-- fallback:latest-slide --><div class="cat-card"><div class="cat-title">古いカテゴリ題名 | 2026-07-06</div><div class="cat-source"><a href="day_slide_2026_07_06.html">今日のスライドを見る →</a></div></div><!-- fallback:end -->
<!-- fallback:unrelated --><span data-sentinel="keep">2026-07-06 day_slide_2026_07_06.html</span><!-- fallback:end -->
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(subject, "SLIDES", slides)
    monkeypatch.setattr(subject, "INDEX", index)

    assert subject.main() == 0

    updated = index.read_text(encoding="utf-8")
    assert "2026-07-09 · 木" in updated
    assert '<span id="heroNewsTitle">新しい &amp; 題名</span>' in updated
    assert 'aria-label="1位: 新しい &amp; 題名"' in updated
    assert '<h3 class="rc-title">新しい &amp; 題名</h3>' in updated
    assert "新しい &amp; 題名 | 2026-07-09" not in updated
    assert (
        '<span>最新トピック: 新しい &amp; 題名。'
        '<a href="day_slide_2026_07_09.html">今日のスライド</a>'
        'または<a href="news_archive.html">アーカイブ</a>からご覧ください。</span>'
    ) in updated
    assert "day_slide_2026_07_09.html" in updated
    assert (
        '<div class="cat-card"><div class="cat-title">新しい &amp; 題名</div>'
        '<div class="cat-source"><a href="day_slide_2026_07_09.html">'
        '今日のスライドを見る →</a></div></div>'
    ) in updated
    assert (
        '<!-- fallback:unrelated --><span data-sentinel="keep">'
        '2026-07-06 day_slide_2026_07_06.html</span><!-- fallback:end -->'
    ) in updated


def test_main_preserves_existing_titles_when_extraction_fails(tmp_path, monkeypatch):
    slides = tmp_path / "slides"
    slides.mkdir()
    (slides / "day_slide_2026_07_09.html").write_text("<main>no title</main>", encoding="utf-8")
    index = tmp_path / "index.html"
    index.write_text(
        """<!-- fallback:latest-slide --><span id="heroNewsTitle">既存タイトル | 2026-07-06</span><!-- fallback:end -->
<!-- fallback:latest-slide --><h3 class="rc-title">既存ランキング | 2026-07-06</h3><!-- fallback:end -->
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(subject, "SLIDES", slides)
    monkeypatch.setattr(subject, "INDEX", index)

    subject.main()

    updated = index.read_text(encoding="utf-8")
    assert "既存タイトル | 2026-07-09" in updated
    assert "既存ランキング | 2026-07-09" in updated


SITREP_HTML = """<!-- fallback:sitrep -->
<aside class="sitrep"><a id="sitrepLink" href="day_slide_2026_07_06.html">
<span id="sitrepUpdate">古い更新</span>
<span id="sitrepDesk">古いデスク</span>
<span id="sitrepAction">古い一手</span>
</a></aside>
<!-- fallback:end -->
"""


def test_main_refreshes_sitrep_href_without_overwriting_copy(tmp_path, monkeypatch):
    slides = tmp_path / "slides"
    slides.mkdir()
    (slides / "day_slide_2026_07_09.html").write_text(
        "<title>新しい題名 | 2026-07-09</title>", encoding="utf-8"
    )
    index = tmp_path / "index.html"
    index.write_text(SITREP_HTML, encoding="utf-8")
    monkeypatch.setattr(subject, "SLIDES", slides)
    monkeypatch.setattr(subject, "INDEX", index)

    assert subject.main() == 0

    updated = index.read_text(encoding="utf-8")
    assert 'href="day_slide_2026_07_09.html"' in updated
    assert '<span id="sitrepUpdate">古い更新</span>' in updated
    assert '<span id="sitrepDesk">古いデスク</span>' in updated
    assert '<span id="sitrepAction">古い一手</span>' in updated


def test_extract_slide_twist_prefers_h1_and_does_not_truncate():
    long_h1 = "あ" * 130
    html = f"<title>短い題 | 2026-08-14</title><h1>{long_h1}</h1>"
    assert subject.extract_slide_twist(html) == long_h1


def test_extract_slide_twist_strips_inner_markup():
    html = "<h1>サプライズは<span class=\"em\">モデルじゃない</span></h1>"
    assert subject.extract_slide_twist(html) == "サプライズはモデルじゃない"


def test_extract_slide_twist_returns_none_without_h1():
    assert subject.extract_slide_twist("<title>題だけ | 2026-08-14</title>") is None


def test_extract_open_loop_reads_meta_description():
    html = (
        '<meta name="description" content="盤面を動かしたのは知能ではなかった。">'
        "<h1>サプライズはモデルじゃない</h1>"
    )
    assert subject.extract_open_loop(html) == "盤面を動かしたのは知能ではなかった。"


def test_extract_open_loop_returns_none_when_missing():
    assert subject.extract_open_loop("<h1>題</h1>") is None


INDEX_HTML_SAMPLE = """
<a class="feat-card" href="day_slides/day_slide_2026_08_14.html">
  <h3 class="feat-title">サプライズはモデルじゃない</h3>
</a>
<a class="slide-card" href="day_slides/day_slide_2026_08_14.html"><span class="slide-date">08/14</span><span class="slide-title">長い本文タイトルは使わない</span></a>
<a class="slide-card" href="day_slides/day_slide_2026_08_13.html"><span class="slide-date">08/13</span><span class="slide-title">日付じゃない</span></a>
"""


def test_titles_from_index_prefers_feat_title():
    titles = subject.titles_from_index(INDEX_HTML_SAMPLE)
    assert titles["2026-08-14"] == "サプライズはモデルじゃない"
    assert titles["2026-08-13"] == "日付じゃない"


def test_week_cards_link_only_days_with_titles():
    html = subject.week_cards_html(
        newest=date(2026, 8, 14),
        titles={"2026-08-14": "サプライズはモデルじゃない", "2026-08-13": "日付じゃない"},
    )
    assert 'href="presentations/day_slides/day_slide_2026_08_14.html"' in html
    assert "サプライズはモデルじゃない" in html
    assert "日付じゃない" in html
    assert 'href="presentations/day_slides/day_slide_2026_08_12.html"' not in html
    assert html.count('class="week-card') >= 7
    assert "is-empty" in html


def test_main_writes_week_cards_from_slides_index(tmp_path, monkeypatch):
    slides = tmp_path / "slides"
    slides.mkdir()
    (slides / "day_slide_2026_08_14.html").write_text("<h1>題</h1>", encoding="utf-8")
    slides_index = tmp_path / "day_slides_index.html"
    slides_index.write_text(INDEX_HTML_SAMPLE, encoding="utf-8")
    index = tmp_path / "index.html"
    index.write_text(
        """<!-- fallback:this-week --><div id="weekGrid" class="week-grid">old</div><!-- fallback:end -->
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(subject, "SLIDES", slides)
    monkeypatch.setattr(subject, "INDEX", index)
    monkeypatch.setattr(subject, "SLIDES_INDEX", slides_index)

    assert subject.main() == 0
    updated = index.read_text(encoding="utf-8")
    assert "サプライズはモデルじゃない" in updated
    assert 'id="weekGrid"' in updated
    assert "old" not in updated


def test_main_writes_hero_twist_and_open_loop_from_slide(tmp_path, monkeypatch):
    slides = tmp_path / "slides"
    slides.mkdir()
    (slides / "day_slide_2026_08_14.html").write_text(
        """<meta name="description" content="盤面を動かしたのは知能ではなかった。">
<title>別の短い題 | 2026-08-14</title>
<h1>サプライズは<span class="em">モデルじゃない</span></h1>
""",
        encoding="utf-8",
    )
    index = tmp_path / "index.html"
    index.write_text(
        """<!-- fallback:latest-slide --><h1 id="heroTwist">古い標語</h1><!-- fallback:end -->
<!-- fallback:latest-slide --><p id="heroWhy">古い要約</p><!-- fallback:end -->
<!-- fallback:latest-slide --><span id="heroDate">2026-08-12 · 水</span><!-- fallback:end -->
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(subject, "SLIDES", slides)
    monkeypatch.setattr(subject, "INDEX", index)

    assert subject.main() == 0

    updated = index.read_text(encoding="utf-8")
    assert '<h1 id="heroTwist">サプライズはモデルじゃない</h1>' in updated
    assert '<p id="heroWhy">盤面を動かしたのは知能ではなかった。</p>' in updated
    assert "2026-08-14 · 金" in updated
    assert "古い標語" not in updated


def test_main_leaves_twist_and_why_when_h1_or_meta_missing(tmp_path, monkeypatch):
    slides = tmp_path / "slides"
    slides.mkdir()
    (slides / "day_slide_2026_08_14.html").write_text(
        "<title>題だけ | 2026-08-14</title>", encoding="utf-8"
    )
    index = tmp_path / "index.html"
    index.write_text(
        """<!-- fallback:latest-slide --><h1 id="heroTwist">残すtwist</h1><!-- fallback:end -->
<!-- fallback:latest-slide --><p id="heroWhy">残すwhy</p><!-- fallback:end -->
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(subject, "SLIDES", slides)
    monkeypatch.setattr(subject, "INDEX", index)

    assert subject.main() == 0

    updated = index.read_text(encoding="utf-8")
    assert '<h1 id="heroTwist">残すtwist</h1>' in updated
    assert '<p id="heroWhy">残すwhy</p>' in updated


def test_main_applies_sitrep_cli_copy_and_title_fallback(tmp_path, monkeypatch):
    slides = tmp_path / "slides"
    slides.mkdir()
    (slides / "day_slide_2026_07_09.html").write_text(
        "<title>スライド題 | 2026-07-09</title>", encoding="utf-8"
    )
    index = tmp_path / "index.html"
    index.write_text(SITREP_HTML, encoding="utf-8")
    monkeypatch.setattr(subject, "SLIDES", slides)
    monkeypatch.setattr(subject, "INDEX", index)

    assert subject.main([
        "--sitrep-update", "料金表",
        "--sitrep-desk", "本番は見送る",
        "--sitrep-action-from-title",
    ]) == 0

    updated = index.read_text(encoding="utf-8")
    assert '<span id="sitrepUpdate">料金表</span>' in updated
    assert '<span id="sitrepDesk">本番は見送る</span>' in updated
    assert '<span id="sitrepAction">スライド題</span>' in updated
    assert 'href="day_slide_2026_07_09.html"' in updated
