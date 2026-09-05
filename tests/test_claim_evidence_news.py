"""Fixed-fixture coverage for claim evidence in the Daily News pipeline."""

from __future__ import annotations

from datetime import date
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from src.auto_collect import daily_news_page
from src.auto_collect.content_integrity import (
    CRUSOE_2026_09_05_URL,
    apply_article_correction,
)
from src.auto_collect.formatter import DayFileFormatter
from src.auto_collect.html_report_parser import parse_daily_txt
from update_news_archive import extract_news_content


ROOT = Path(__file__).resolve().parents[1]


def _legacy_dayfile(include_claim_evidence: bool) -> str:
    metadata = (
        '🔎 Claim Evidence: {"sources":[{"url":"https://metadata.example/source"}],'
        '"note":"公式発表ではない"}\n'
        if include_claim_evidence else ""
    )
    return (
        "2026年09月05日のAIニュース\n"
        "■ Legacy article\n"
        "通常の要約本文\n"
        "・保持するポイント\n"
        "URL: https://example.test/article\n"
        + metadata
    )


def test_legacy_archive_extractor_ignores_claim_evidence_metadata_line() -> None:
    """A new metadata line must not alter the existing text archive shape."""
    without_metadata = extract_news_content(_legacy_dayfile(False))
    with_metadata = extract_news_content(_legacy_dayfile(True))

    assert with_metadata == without_metadata
    assert "Claim Evidence" not in with_metadata["summary"]
    assert with_metadata["extracted_urls_count"] == 1


def test_raw_fallback_strips_claim_evidence_metadata_line(tmp_path: Path) -> None:
    """The compatibility fallback must not expose embedded evidence JSON."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the raw fallback fixture")
    plain = tmp_path / "plain.txt"
    metadata = tmp_path / "metadata.txt"
    plain.write_text(_legacy_dayfile(False), encoding="utf-8")
    metadata.write_text(_legacy_dayfile(True), encoding="utf-8")
    expression = (
        "const {parseNewsFile}=require(process.argv[1]);"
        "console.log(JSON.stringify(parseNewsFile(process.argv[2], '0905.txt')));"
    )

    def parse(path: Path) -> dict:
        result = subprocess.run(
            [node, "-e", expression, str(ROOT / "scripts" / "generate-daily-news-json.js"), str(path)],
            text=True, encoding="utf-8", capture_output=True, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)

    assert parse(metadata) == parse(plain)


def test_crusoe_evidence_survives_correction_dayfile_and_parser(tmp_path) -> None:
    """The cited reporting record must survive a text round-trip unchanged."""
    corrected = apply_article_correction(
        {
            "url": CRUSOE_2026_09_05_URL,
            "title": "legacy title",
            "tldr": "legacy tldr",
            "summary": "legacy summary",
            "category": "Business",
            "source": "TechCrunch",
            "score": 85,
        }
    )
    expected = corrected["claim_evidence"]
    assert expected["claims"][0]["basis"] == "reporting"
    assert expected["claims"][0]["status"] == "matched"
    assert expected["claims"][0]["verification"]["checked_at"] == "2026-09-05"
    assert expected["claims"][0]["verification"]["method"] == "ai_document_review"
    assert "Bloomberg原報を直接確認していない" in expected["claims"][0]["uncertainty"]

    dayfile = tmp_path / "0905.txt"
    DayFileFormatter().write([corrected], dayfile, date(2026, 9, 5))
    parsed = parse_daily_txt(dayfile)["headlines"][0]

    assert parsed["claim_evidence"] == expected
    assert parsed["category"] == "Business"
    assert parsed["source"] == "TechCrunch（Bloomberg報道）"
    assert parsed["evidence_label"] == "Claim"


def test_legacy_dayfile_without_claim_evidence_remains_valid(tmp_path) -> None:
    """Absent optional metadata must not manufacture an evidence badge."""
    dayfile = tmp_path / "0905.txt"
    dayfile.write_text(
        "2026年09月05日 AIニュース\nヘッドライン速報\n"
        "■ Legacy（Business / スコア: 85）\nsummary\nURL: https://example.test/legacy\n",
        encoding="utf-8",
    )

    parsed = parse_daily_txt(dayfile)["headlines"][0]
    assert parsed.get("claim_evidence") is None
    assert parsed["evidence_label"] == ""


def test_timeline_keeps_claim_evidence_in_json_and_renders_it(monkeypatch, tmp_path) -> None:
    """The visible timeline block and its JSON mirror use the same bundle."""
    output_dir = tmp_path / "daily-news"
    monkeypatch.setattr(daily_news_page, "DAILY_NEWS_DIR", output_dir)
    monkeypatch.setattr(daily_news_page, "ARCHIVE_DIR", output_dir / "archive")
    article = apply_article_correction(
        {
            "url": CRUSOE_2026_09_05_URL,
            "title": "legacy title",
            "tldr": "legacy tldr",
            "summary": "legacy summary",
            "category": "Business",
            "source": "TechCrunch",
            "score": 85,
        }
    )

    daily_news_page.generate_daily_news(date(2026, 9, 5), [article])

    payload = (output_dir / "data.json").read_text(encoding="utf-8")
    item = json.loads(payload)["items"][0]
    page = (output_dir / "index.html").read_text(encoding="utf-8")
    assert '"claim_evidence"' in payload
    assert "ai_document_review" in payload
    assert "claim-evidence" in page
    assert "Bloomberg報道" in page
    assert item["source"] == "TechCrunch（Bloomberg報道）"
