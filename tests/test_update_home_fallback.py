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
