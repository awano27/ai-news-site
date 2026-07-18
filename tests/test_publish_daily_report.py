from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

from scripts import publish_daily_report
from scripts.publish_daily_report import load_manifest, validate_changes


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "publish_daily_report.py"
MANIFEST_PATH = REPO_ROOT / "scripts" / "daily_report_paths.json"
REPORT_DATE = date(2026, 7, 18)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def create_repo(tmp_path: Path, *, include_optional: bool = False) -> tuple[Path, object]:
    repo = tmp_path / "daily-report-repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "user.email", "test@example.com")
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)
    for relative_path in manifest.required:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"baseline {relative_path}\n", encoding="utf-8")
    if include_optional:
        for relative_path in manifest.optional:
            path = repo / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"optional")
    baseline_paths = [
        *manifest.required,
        *(path for path in manifest.optional if (repo / path).is_file()),
    ]
    git(repo, "add", "--", *baseline_paths)
    git(repo, "commit", "-m", "baseline")
    return repo, manifest


def run_publisher(repo: Path, *, push: bool = False) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT),
        "--repo",
        str(repo),
        "--date",
        REPORT_DATE.isoformat(),
        "--message",
        "publish daily report",
    ]
    if push:
        command.append("--push")
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_manifest_expands_all_date_formats_and_optional_ogp() -> None:
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)

    assert "input/day/0718.txt" in manifest.required
    assert "daily-news/archive/2026-07-18.html" in manifest.required
    assert "presentations/daily_reports/auto_daily_report_2026_07_18.html" in manifest.required
    assert manifest.optional == ("presentations/daily_reports/og/2026_07_18.png",)


def test_unrelated_change_rejects_without_staging_or_losing_work(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    allowed = repo / manifest.required[0]
    unrelated = repo / "unrelated.txt"
    allowed.write_text("allowed update\n", encoding="utf-8")
    unrelated.write_text("keep this change\n", encoding="utf-8")

    result = run_publisher(repo)

    assert result.returncode != 0
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""
    assert allowed.read_text(encoding="utf-8") == "allowed update\n"
    assert unrelated.read_text(encoding="utf-8") == "keep this change\n"


def test_allowed_changes_commit_exactly_changed_manifest_paths(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    changed = (manifest.required[0], manifest.required[3])
    for relative_path in changed:
        (repo / relative_path).write_text("updated\n", encoding="utf-8")

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    committed = git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines()
    assert committed == sorted(changed)
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_missing_required_path_rejects_before_staging(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    (repo / manifest.required[0]).unlink()
    head_before = git(repo, "rev-parse", "HEAD").stdout

    result = run_publisher(repo)

    assert result.returncode != 0
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""
    assert git(repo, "rev-parse", "HEAD").stdout == head_before


def test_pre_staged_change_rejects_without_new_staged_changes(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    staged = repo / manifest.required[0]
    unstaged = repo / manifest.required[1]
    staged.write_text("already staged\n", encoding="utf-8")
    git(repo, "add", "--", manifest.required[0])
    unstaged.write_text("must remain unstaged\n", encoding="utf-8")
    before = git(repo, "diff", "--cached", "--name-only").stdout

    result = run_publisher(repo)

    assert result.returncode != 0
    assert git(repo, "diff", "--cached", "--name-only").stdout == before
    assert unstaged.read_text(encoding="utf-8") == "must remain unstaged\n"


def test_missing_optional_ogp_succeeds_and_archive_name_is_dated(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path, include_optional=False)
    archive_name = "presentations/daily_reports/auto_daily_report_2026_07_18.html"
    assert archive_name in manifest.required
    assert not (repo / manifest.optional[0]).exists()
    (repo / archive_name).write_text("updated archive\n", encoding="utf-8")

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    assert git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines() == [archive_name]


def test_validate_changes_reports_missing_required_path(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    (repo / manifest.required[-1]).unlink()

    errors = validate_changes(repo, manifest)

    assert any("missing required path" in error for error in errors)


def test_publish_stages_the_single_validated_status_snapshot(monkeypatch, tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    validated_path = manifest.required[0]
    (repo / validated_path).write_text("validated update\n", encoding="utf-8")
    (repo / "unrelated.txt").write_text("must never be staged\n", encoding="utf-8")
    snapshots = iter(((validated_path,), ("unrelated.txt",)))
    add_calls: list[tuple[str, ...]] = []
    original_git = publish_daily_report._git

    def changing_status(_: Path) -> tuple[str, ...]:
        return next(snapshots)

    def recording_git(repo_path: Path, args, *, check: bool = True):
        if args[0] == "add":
            add_calls.append(tuple(args))
        return original_git(repo_path, args, check=check)

    monkeypatch.setattr(publish_daily_report, "_status_paths", changing_status)
    monkeypatch.setattr(publish_daily_report, "_git", recording_git)

    result = publish_daily_report.publish(repo, REPORT_DATE, "publish daily report")

    assert result == 0
    assert add_calls == [("add", "--", validated_path)]
