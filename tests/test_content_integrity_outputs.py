"""Offline end-to-end consumers of the corrected news record."""
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from src.auto_collect.content_integrity import CRUSOE_2026_09_05_URL, apply_financial_integrity
from src.auto_collect.formatter import DayFileFormatter
from src.auto_collect.html_report_parser import parse_daily_txt
from src.auto_collect.html_report import generate_html
from update_news_archive import extract_news_content

ROOT = Path(__file__).resolve().parents[1]


def test_corrected_dayfile_reaches_homepage_and_legacy_api(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed for the existing JSON/homepage generators")
    article = apply_financial_integrity({
        "title": "Crusoe、企業価値$30億との報道",
        "url": CRUSOE_2026_09_05_URL,
        "date": "2026-09-05", "source": "TechCrunch", "score": 85,
        "category": "Business", "tldr": "$30Bの評価で$3B調達",
        "summary": "企業価値は$30億。", "points": ["企業価値$30億"],
        "evidence": {"metrics": ["企業価値$30億"], "impact_ja": "企業価値$30億へ拡大"},
    })
    dayfile = tmp_path / "0905.txt"
    DayFileFormatter().write([article], dayfile, date(2026, 9, 5))
    content = dayfile.read_text(encoding="utf-8")
    assert "$30億" not in content
    html, report = generate_html(parse_daily_txt(dayfile))
    assert "300億米ドル" in html

    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("build-homepage-latest.js", "generate-daily-news-json.js"):
        shutil.copy2(ROOT / "scripts" / name, scripts / name)
    shutil.copy2(ROOT / "index.html", tmp_path / "index.html")
    slide_dir = tmp_path / "presentations" / "day_slides"
    slide_dir.mkdir(parents=True)
    (slide_dir / "day_slide_2026_09_05.html").write_text(
        "<html><title>固定した検証用スライド</title><h1>固定した検証用スライド</h1></html>",
        encoding="utf-8",
    )
    api = tmp_path / "public-pages" / "api" / "auto_daily_report"
    api.mkdir(parents=True)
    (api / "latest.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    snapshots = tmp_path / "public-pages" / "news"
    snapshots.mkdir(parents=True)
    (snapshots / "2026-09-05.json").write_text(json.dumps({
        "date": "2026-09-05", "items": [extract_news_content(content)]
    }, ensure_ascii=False), encoding="utf-8")
    (snapshots / "daily_index.json").write_text(json.dumps([
        {"date": "2026-09-05", "file": "2026-09-05.json"}
    ]), encoding="utf-8")
    # The existing homepage consumer has a 14-day freshness gate. Keep this
    # historical fixture deterministic without changing the production clock.
    clock = tmp_path / "fixed-clock.cjs"
    clock.write_text(
        "const RealDate = Date; global.Date = class extends RealDate {"
        "constructor(...args) { super(...(args.length ? args : ['2026-09-05T03:00:00Z'])); }"
        "static now() { return RealDate.parse('2026-09-05T03:00:00Z'); }};",
        encoding="utf-8",
    )
    for name in ("build-homepage-latest.js", "generate-daily-news-json.js"):
        result = subprocess.run([node, "--require", str(clock), str(scripts / name)], cwd=tmp_path,
                                capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stdout + result.stderr
    for relative in ("news/latest.json", "presentations/api/daily-news.json",
                     "presentations/api/daily-news-latest.json"):
        output = (tmp_path / relative).read_text(encoding="utf-8")
        assert "$30億" not in output, relative
        assert "300億米ドル" in output, relative
        assert "TechCrunch" in output, relative
    homepage = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "$30億" not in homepage


def test_explicit_conflict_is_not_bypassed_by_historical_prose():
    result = apply_financial_integrity({
        "summary": "previous round; current facts", "date": "2026-09-05",
        "financial_claims": [
            {"metric": "valuation", "currency": "USD", "event_date": "2026-09-03",
             "unit": "billion", "amount": amount} for amount in (30, 3)
        ],
    })
    assert result.get("integrity_status") == "pending_fact_check"


def test_processor_shape_without_event_date_does_not_hold_valid_amount():
    # LLMProcessor currently emits no date field; that is not a conflict.
    result = apply_financial_integrity({"summary": "企業価値は$30B。"})
    assert result.get("integrity_status") != "pending_fact_check"
    assert result["financial_claims"][0]["event_date"] == "unknown"


def test_old_dayfile_evidence_is_not_upgraded_to_fact(tmp_path):
    path = tmp_path / "0905.txt"
    path.write_text(
        "2026年09月05日 AIニュース\nヘッドライン速報\n"
        "■ Crusoe（Business / スコア: 85）\n"
        "企業価値$30億\n🇯🇵 影響: 企業価値$30億\n⚡ 今すぐ: 企業価値$30億\n"
        "🏷️ Label: Fact\nURL: " + CRUSOE_2026_09_05_URL + "\n", encoding="utf-8")
    parsed = parse_daily_txt(path)
    assert parsed["headlines"][0]["evidence_label"] == "Claim"
    html, _ = generate_html(parsed)
    assert "$30億" not in html
