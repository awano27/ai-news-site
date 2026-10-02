import json
import subprocess
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.auto_collect import main as auto_collect_main


class StaticCollector:
    def __init__(self, items):
        self.items = items

    def collect(self, _today):
        return self.items


class UnavailableNvidiaProvider:
    name = "nvidia"
    available = False

    def chat(self, _prompt):
        raise AssertionError("unavailable provider must not be called")


def install_deterministic_pipeline(
    monkeypatch,
    tmp_path,
    *,
    headlines,
    github,
    archive_returncode=0,
    html_mode="write",
):
    """Replace collection and rendering boundaries with deterministic fakes."""
    monkeypatch.setattr(auto_collect_main, "setup_logging", lambda: None)
    monkeypatch.setattr(
        auto_collect_main,
        "parse_args",
        lambda: SimpleNamespace(provider="nvidia", force=True, run_id="test-run-123"),
    )
    input_dir = tmp_path / "input" / "day"
    monkeypatch.setattr(auto_collect_main, "INPUT_DAY_DIR", input_dir)
    monkeypatch.setattr(auto_collect_main, "PROJECT_ROOT", tmp_path)
    (tmp_path / "update_news_archive.py").write_text("# fixture\n", encoding="utf-8")

    monkeypatch.setattr(
        auto_collect_main, "RSSAutoCollector", lambda: StaticCollector(headlines)
    )
    for collector_name in (
        "HNAutoCollector",
        "JPCollector",
        "ArxivCollector",
        "XBookmarksCollector",
        "BenchmarkCollector",
        "FundingCollector",
    ):
        monkeypatch.setattr(
            auto_collect_main, collector_name, lambda: StaticCollector([])
        )
    monkeypatch.setattr(
        auto_collect_main, "GitHubTrendingCollector", lambda: StaticCollector(github)
    )

    captured_writes = []

    class CapturingFormatter:
        def write(self, articles, output_path, _today, **sections):
            captured_writes.append((articles, sections))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                f"{_today:%Y年%m月%d日}のAIニュース速報 - fixture\n",
                encoding="utf-8",
            )

    monkeypatch.setattr(auto_collect_main, "DayFileFormatter", CapturingFormatter)

    report_date = date.today()
    html_paths = (
        tmp_path / "presentations" / "auto_daily_report.html",
        tmp_path / "presentations" / "auto_daily_report.json",
        tmp_path
        / "presentations"
        / "daily_reports"
        / f"auto_daily_report_{report_date:%Y_%m_%d}.html",
        tmp_path / "presentations" / "daily_reports" / "index.json",
        tmp_path / "presentations" / "daily_reports" / "searchable.json",
        tmp_path / "public-pages" / "api" / "auto_daily_report" / "latest.json",
    )
    daily_news_paths = (
        tmp_path / "daily-news" / "index.html",
        tmp_path / "daily-news" / "data.json",
        tmp_path / "daily-news" / "archive" / f"{report_date}.html",
    )
    archive_paths = (
        tmp_path / "public-pages" / "news" / f"{report_date}.json",
        tmp_path / "public-pages" / "news" / "archive_index.json",
        tmp_path / "public-pages" / "news" / "version.json",
    )

    def write_valid_artifact(path: Path) -> None:
        relative = path.relative_to(tmp_path).as_posix()
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".html":
            path.write_text(
                f'<html><head><meta name="report:date" content="{report_date}"></head>'
                "<body>fixture</body></html>\n",
                encoding="utf-8",
            )
            return
        if relative == f"public-pages/news/{report_date}.json":
            data = {"date": str(report_date), "items": [{"title": "fixture"}]}
        elif relative == "public-pages/news/archive_index.json":
            data = [{"date": str(report_date), "file": f"{report_date}.json"}]
        elif relative == "public-pages/news/version.json":
            data = {"updated": f"{report_date} 00:00:00", "total_entries": 1}
        elif relative in {
            "presentations/daily_reports/index.json",
            "presentations/daily_reports/searchable.json",
        }:
            data = {
                "generated": str(report_date),
                "reports": [
                    {
                        "date": str(report_date),
                        "file": f"auto_daily_report_{report_date:%Y_%m_%d}.html",
                    }
                ],
            }
        else:
            data = {"date": str(report_date), "items": [{"title": "fixture"}]}
        path.write_text(json.dumps(data), encoding="utf-8")

    if html_mode == "stale":
        for path in html_paths:
            write_valid_artifact(path)

    def generate_html(_path):
        if html_mode == "raise":
            raise RuntimeError("injected HTML failure")
        if html_mode != "stale":
            for path in html_paths:
                write_valid_artifact(path)
            if html_mode == "malformed_json":
                html_paths[1].write_text("{", encoding="utf-8")
            elif html_mode == "empty_html":
                html_paths[0].write_text("", encoding="utf-8")
            elif html_mode == "wrong_date":
                html_paths[0].write_text(
                    '<meta name="report:date" content="2000-01-01">',
                    encoding="utf-8",
                )
        return html_paths[0]

    def generate_daily(*_args, **_kwargs):
        for path in daily_news_paths:
            write_valid_artifact(path)
        return daily_news_paths[0]

    def run_archive(*_args, **_kwargs):
        if archive_returncode == 0:
            for path in archive_paths:
                write_valid_artifact(path)
        return subprocess.CompletedProcess([], archive_returncode)

    monkeypatch.setattr(auto_collect_main, "generate_html_report", generate_html)
    monkeypatch.setattr(auto_collect_main, "generate_daily_news", generate_daily)
    monkeypatch.setattr(auto_collect_main.subprocess, "run", run_archive)
    return captured_writes


def test_unavailable_nvidia_uses_heuristic_fallback(monkeypatch, tmp_path):
    writes = install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[
            {
                "name": "New GPT model released",
                "tagline": "A deterministic fallback item",
                "source_rank": 1,
                "links": {"official": "https://example.com/official"},
            }
        ],
        github=[],
    )
    monkeypatch.setattr(
        auto_collect_main, "make_provider", lambda _name: UnavailableNvidiaProvider()
    )

    auto_collect_main.main()

    assert len(writes) == 1
    headline_items, _sections = writes[0]
    assert headline_items[0]["title"] == "New GPT model released"
    assert headline_items[0]["score"] == 60


def test_empty_headline_and_github_sources_exit_before_provider(monkeypatch, tmp_path):
    install_deterministic_pipeline(monkeypatch, tmp_path, headlines=[], github=[])

    def fail_if_provider_is_built(_name):
        pytest.fail("provider must not be constructed for an empty report")

    monkeypatch.setattr(auto_collect_main, "make_provider", fail_if_provider_is_built)

    with pytest.raises(SystemExit) as exc_info:
        auto_collect_main.main()

    assert exc_info.value.code == 1


def test_archive_subprocess_failure_marks_run_unpublishable(monkeypatch, tmp_path):
    install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[{"name": "headline", "links": {"official": "https://example.com"}}],
        github=[],
        archive_returncode=7,
    )
    monkeypatch.setattr(
        auto_collect_main, "make_provider", lambda _name: UnavailableNvidiaProvider()
    )

    with pytest.raises(SystemExit) as exc_info:
        auto_collect_main.main()

    assert exc_info.value.code == 1
    manifest_path = (
        tmp_path
        / "public-pages"
        / "api"
        / "auto_daily_report"
        / "run"
        / f"{date.today()}.json"
    )
    result = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result["date"] == date.today().isoformat()
    assert result["run_id"] == "test-run-123"
    assert result["phases"]["archive"]["success"] is False
    assert result["failure_count"] >= 1
    assert result["publication_ready"] is False


def test_stale_same_day_html_is_not_accepted_as_current_run_output(monkeypatch, tmp_path):
    install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[{"name": "headline", "links": {"official": "https://example.com"}}],
        github=[],
        html_mode="stale",
    )
    monkeypatch.setattr(
        auto_collect_main, "make_provider", lambda _name: UnavailableNvidiaProvider()
    )

    with pytest.raises(SystemExit) as exc_info:
        auto_collect_main.main()

    assert exc_info.value.code == 1
    manifest_path = (
        tmp_path
        / "public-pages"
        / "api"
        / "auto_daily_report"
        / "run"
        / f"{date.today()}.json"
    )
    result = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result["phases"]["html_report"]["success"] is False
    assert any(
        artifact["path"] == "presentations/auto_daily_report.html"
        and artifact["fresh"] is False
        for artifact in result["artifacts"]
    )
    assert result["publication_ready"] is False


def test_html_generation_exception_marks_run_unpublishable(monkeypatch, tmp_path):
    install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[{"name": "headline", "links": {"official": "https://example.com"}}],
        github=[],
        html_mode="raise",
    )
    monkeypatch.setattr(
        auto_collect_main, "make_provider", lambda _name: UnavailableNvidiaProvider()
    )

    with pytest.raises(SystemExit) as exc_info:
        auto_collect_main.main()

    assert exc_info.value.code == 1
    manifest_path = (
        tmp_path
        / "public-pages"
        / "api"
        / "auto_daily_report"
        / "run"
        / f"{date.today()}.json"
    )
    result = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result["phases"]["html_report"]["success"] is False
    assert result["failure_count"] == 2
    assert result["required_failure_count"] == 1
    assert result["publication_ready"] is False


@pytest.mark.parametrize("html_mode", ["malformed_json", "empty_html", "wrong_date"])
def test_invalid_generated_content_marks_run_unpublishable(
    monkeypatch, tmp_path, html_mode
):
    install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[{"name": "headline", "links": {"official": "https://example.com"}}],
        github=[],
        html_mode=html_mode,
    )
    monkeypatch.setattr(
        auto_collect_main, "make_provider", lambda _name: UnavailableNvidiaProvider()
    )

    with pytest.raises(SystemExit) as exc_info:
        auto_collect_main.main()

    assert exc_info.value.code == 1
    result_path = (
        tmp_path
        / "public-pages"
        / "api"
        / "auto_daily_report"
        / "run"
        / f"{date.today()}.json"
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["phases"]["html_report"]["success"] is False
    assert result["required_failure_count"] == 1
    assert result["publication_ready"] is False


def test_successful_run_writes_publishable_result_manifest(monkeypatch, tmp_path):
    install_deterministic_pipeline(
        monkeypatch,
        tmp_path,
        headlines=[{"name": "headline", "links": {"official": "https://example.com"}}],
        github=[],
    )
    monkeypatch.setattr(
        auto_collect_main, "make_provider", lambda _name: UnavailableNvidiaProvider()
    )

    auto_collect_main.main()

    manifest_path = (
        tmp_path
        / "public-pages"
        / "api"
        / "auto_daily_report"
        / "run"
        / f"{date.today()}.json"
    )
    result = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result["date"] == date.today().isoformat()
    assert result["run_id"] == "test-run-123"
    assert set(result["phases"]) == {
        "report_text",
        "archive",
        "html_report",
        "daily_news",
        "og_image",
    }
    assert result["failure_count"] == 1
    assert result["required_failure_count"] == 0
    assert result["phases"]["og_image"] == {"required": False, "success": False}
    assert result["publication_ready"] is True
    assert all(
        {"path", "phase", "required", "exists", "fresh", "valid", "size", "sha256", "mtime_ns"}
        <= set(artifact)
        for artifact in result["artifacts"]
    )
