from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_URL = "https://gigazine.net/news/20261017-sauna-camp-machiasobi31"


def today_jst() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()


def setup_site(tmp_path: Path, headlines: list[dict]) -> tuple[str, Path]:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts/build-homepage-latest.js", scripts)
    shutil.copy2(ROOT / "index.html", tmp_path / "index.html")

    date = today_jst()
    slides = tmp_path / "presentations/day_slides"
    slides.mkdir(parents=True)
    (slides / f"day_slide_{date.replace('-', '_')}.html").write_text(
        f"<title>Fixture slide | {date}</title><h1>Fixture slide</h1>",
        encoding="utf-8",
    )
    report = tmp_path / "public-pages/api/auto_daily_report/latest.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({"date": date, "headlines": headlines}), encoding="utf-8")
    return date, report


def build(tmp_path: Path) -> str:
    result = subprocess.run(
        ["node", str(tmp_path / "scripts/build-homepage-latest.js")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return (tmp_path / "index.html").read_text(encoding="utf-8")


def editorial(url: str, *, title: str = "編集見出し", source_date: str | None = None,
              primary_url: str | None = None, primary_label: str | None = None,
              primary_date: str | None = None) -> dict:
    return {
        "url": url,
        "title": title,
        "change": "確認した変更点です。",
        "relevance": "開発者に関係します。",
        "caution": "原文の条件を確認してください。",
        "source_date": source_date,
        "primary_url": primary_url,
        "primary_label": primary_label,
        "primary_date": primary_date,
        "evidence_label": "出典確認済み",
    }


def write_editorial(tmp_path: Path, date: str, articles: list[dict], *, report_date: str | None = None) -> None:
    config = tmp_path / "config/homepage_editorial.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        json.dumps({"report_date": report_date or date, "articles": articles}, ensure_ascii=False),
        encoding="utf-8",
    )


def briefing_fragment(html: str) -> str:
    return html.split('id="dailyHeadlines"', 1)[1].split("</ol>", 1)[0]


def test_valid_editorial_config_is_date_and_url_bound_and_escaped(tmp_path: Path) -> None:
    urls = [
        "https://example.com/ai-one",
        "https://example.com/ai-two",
        "https://example.com/unrelated-map",
    ]
    date, _ = setup_site(tmp_path, [
        {"title": "AI one", "url": urls[0], "score": 90},
        {"title": "AI two", "url": urls[1], "score": 80},
        {"title": "Map only story", "url": urls[2], "score": 99},
    ])
    write_editorial(tmp_path, date, [
        editorial(urls[0], title="<script>alert(1)</script>", source_date="2026-10-18",
                  primary_url="https://official.example/ai-one", primary_label="公式発表",
                  primary_date="2026-10-17"),
        editorial(urls[1]),
    ])

    html = build(tmp_path)
    fragment = briefing_fragment(html)
    assert fragment.count("<li>") == 2
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in fragment
    assert "<script>alert(1)</script>" not in fragment
    assert "<strong>出典確認済み:</strong> 確認した変更点です。" in fragment
    assert "運営者の見方:" in fragment
    assert "利用前に:" in fragment
    assert 'class="article-dates"' in fragment
    assert "出典確認済み" in fragment
    assert "当サイト掲載:</strong> " + date in fragment
    assert "原文掲載:</strong> 2026-10-18" in fragment
    assert "一次資料:</strong> 公式発表（2026-10-17）" in fragment
    assert "一次資料:</strong> 未確認" in fragment
    assert "Map only story" not in html


def test_stale_or_oversized_editorial_config_fails_closed(tmp_path: Path) -> None:
    url = "https://example.com/ai-one"
    date, _ = setup_site(tmp_path, [{
        "title": "AI one", "url": url, "score": 90,
        "tldr": "現在のニュースに関する要約です。",
    }])
    write_editorial(tmp_path, date, [editorial(url, title="Should not publish")], report_date="2020-01-01")

    html = build(tmp_path)
    fragment = briefing_fragment(html)
    assert "AI one" in fragment
    assert "現在のニュースに関する要約です。" in fragment
    assert "Should not publish" not in html

    write_editorial(tmp_path, date, [editorial(url)] * 4)
    html = build(tmp_path)
    assert "主要ニュース" in briefing_fragment(html)
    assert "編集見出し" not in html


def test_ai_relevance_guard_keeps_ai_and_drops_unrelated_promotions(tmp_path: Path) -> None:
    date, _ = setup_site(tmp_path, [
        {"title": "AI agent release", "url": "https://example.com/agent", "score": 90},
        {"title": "Free office suite", "url": "https://example.com/office", "score": 89},
        {"title": "Security bulletin", "url": "https://example.com/security", "score": 88},
        {"title": "Map editor", "url": "https://example.com/map", "score": 87},
    ])

    html = build(tmp_path)
    data = json.loads((tmp_path / "news/latest.json").read_text(encoding="utf-8"))
    assert "AI agent release" in html
    assert all(
        item["title"] not in html
        for rows in data.get("sections", {}).values()
        for item in rows
        if item["title"] in {"Free office suite", "Security bulletin", "Map editor"}
    )
    assert "Free office suite" not in briefing_fragment(html)
    assert "Security bulletin" not in briefing_fragment(html)
    assert "Map editor" not in briefing_fragment(html)


def test_excluded_url_invalidates_editorial_selection_without_source_leak(tmp_path: Path) -> None:
    date, _ = setup_site(tmp_path, [{"title": "Excluded AI event", "url": EXCLUDED_URL, "score": 99}])
    write_editorial(tmp_path, date, [editorial(EXCLUDED_URL, title="Excluded editorial")])

    html = build(tmp_path)
    assert "Excluded editorial" not in html
    assert "Excluded AI event" not in briefing_fragment(html)


def test_malicious_primary_url_fails_closed_without_html_injection(tmp_path: Path) -> None:
    url = "https://example.com/ai-one"
    date, _ = setup_site(tmp_path, [{"title": "AI one", "url": url, "score": 90}])
    write_editorial(tmp_path, date, [editorial(
        url,
        title="<img src=x onerror=alert(1)>",
        primary_url="javascript:alert(1)",
        primary_label="<script>bad</script>",
    )])

    html = build(tmp_path)
    assert "主要ニュース" in briefing_fragment(html)
    assert "javascript:alert(1)" not in html
    assert "onerror=alert(1)" not in html

def test_windows_template_regeneration_is_idempotent(tmp_path: Path) -> None:
    setup_site(tmp_path, [{"title": "AI agent", "url": "https://example.com/ai"}])
    index = tmp_path / "index.html"
    index.write_bytes(index.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    first = build(tmp_path)
    second = build(tmp_path)
    assert first == second
    assert second.count('http-equiv="Content-Security-Policy"') == 1
