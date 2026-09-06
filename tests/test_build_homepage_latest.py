from __future__ import annotations

import json
import re
from html.parser import HTMLParser
import shutil
import subprocess
from pathlib import Path

import pytest


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


def assert_entry_contract(html):
    page = Homepage(html)
    assert [a.get("id") for t, a in page.elements if t == "h1"] == ["heroIdentity"]
    assert page.by_id("heroDescription")[0] == "p"
    for elem_id, destination in {
        "heroNewsBtn": "daily-news/",
        "heroArticleBtn": "articles/claim-evidence-design.html",
        "comparisonCard": "presentations/ai_coding_agents_guide.html",
        "implementationCard": "articles/claim-evidence-design.html",
    }.items():
        tag, attrs = page.by_id(elem_id)
        assert tag == "a"
        assert attrs.get("href") == destination
    assert "btn-primary" in page.by_id("heroArticleBtn")[1].get("class", "").split()
    assert "btn-ghost" in page.by_id("heroNewsBtn")[1].get("class", "").split()
    ids = [attrs.get("id") for tag, attrs in page.elements if tag == "a"]
    assert ids.index("heroArticleBtn") < ids.index("heroNewsBtn")
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
    assert 'href="presentations/day_slides/day_slide_2026_09_05.html"' in updated
    assert 'href="daily-news/"' in updated
    assert 'href="articles/claim-evidence-design.html"' in updated


@pytest.mark.parametrize("old,new", [
    ('id="heroIdentity"', 'id="missingIdentity"'),
    ('href="daily-news/"', 'href="#resources"'),
    ('href="articles/claim-evidence-design.html"', 'href="#resources"'),
])
def test_entry_contract_rejects_broken_heading_or_primary_link(old, new):
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_entry_contract(html.replace(old, new, 1))
