from pathlib import Path

from src.auto_collect.html_report_parser import parse_daily_txt


def test_parse_daily_txt_keeps_last_item_in_its_section_at_section_boundary(
    tmp_path: Path,
) -> None:
    """A header must flush the preceding item before changing sections."""
    report = tmp_path / "0718.txt"
    report.write_text(
        "2026年07月18日 AIニュース\n"
        "ヘッドライン速報\n"
        "■ Headline item（速報 / スコア: 90）\n"
        "headline summary\n"
        "市場・資金動向\n"
        "■ Funding item（資金調達 / スコア: 80）\n"
        "funding summary\n"
        "GitHub Trending\n"
        "■ GitHub item（開発 / スコア: 70）\n"
        "github summary\n"
        "HuggingFace注目モデル\n"
        "■ Model item（モデル / スコア: 60）\n"
        "model summary\n",
        encoding="utf-8",
    )

    parsed = parse_daily_txt(report)

    assert [item["title"] for item in parsed["headlines"]] == ["Headline item"]
    assert [item["title"] for item in parsed["funding"]] == ["Funding item"]
    assert [item["title"] for item in parsed["github"]] == ["GitHub item"]
    assert [item["title"] for item in parsed["models"]] == ["Model item"]
    assert sum(len(parsed[section]) for section in ("headlines", "funding", "github", "models")) == 4
