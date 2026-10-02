from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from src.auto_collect import main as auto_collect_main
from scripts import publish_daily_report
from scripts.publish_daily_report import load_manifest, validate_changes


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "publish_daily_report.py"
MANIFEST_PATH = REPO_ROOT / "scripts" / "daily_report_paths.json"
REPORT_DATE = date(2026, 7, 18)
RUN_ID = "test-run-20260718"
RUN_MANIFEST_PATH = (
    f"public-pages/api/auto_daily_report/run/{REPORT_DATE.isoformat()}.json"
)


def write_valid_artifact(repo: Path, relative_path: str, marker: str = "fixture") -> None:
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if relative_path == RUN_MANIFEST_PATH:
        return
    if path.suffix == ".html":
        path.write_text(
            f'<html><head><meta name="report:date" content="{REPORT_DATE}"></head>'
            f"<body>{marker}</body></html>\n",
            encoding="utf-8",
        )
        return
    if relative_path == f"input/day/{REPORT_DATE:%m%d}.txt":
        path.write_text(
            f"{REPORT_DATE:%Y年%m月%d日}のAIニュース速報 - {marker}\n",
            encoding="utf-8",
        )
        return
    if relative_path == f"public-pages/news/{REPORT_DATE}.json":
        data = {"date": str(REPORT_DATE), "items": [{"title": marker}]}
    elif relative_path == "public-pages/news/archive_index.json":
        data = [{"date": str(REPORT_DATE), "file": f"{REPORT_DATE}.json"}]
    elif relative_path == "public-pages/news/version.json":
        data = {"updated": f"{REPORT_DATE} 00:00:00", "total_entries": 1}
    elif relative_path in {
        "presentations/daily_reports/index.json",
        "presentations/daily_reports/searchable.json",
    }:
        data = {
            "generated": str(REPORT_DATE),
            "reports": [
                {
                    "date": str(REPORT_DATE),
                    "file": f"auto_daily_report_{REPORT_DATE:%Y_%m_%d}.html",
                }
            ],
            "marker": marker,
        }
    else:
        data = {"date": str(REPORT_DATE), "items": [{"title": marker}]}
    path.write_text(json.dumps(data), encoding="utf-8")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def write_run_manifest(
    repo: Path,
    manifest,
    *,
    run_id: str = RUN_ID,
    publication_ready: bool = True,
) -> None:
    phase_for_path = {
        "input/day/": "report_text",
        "public-pages/news/": "archive",
        "presentations/": "html_report",
        "public-pages/api/auto_daily_report/latest.json": "html_report",
        "daily-news/": "daily_news",
    }
    artifacts = []
    for relative_path in manifest.required:
        if relative_path == RUN_MANIFEST_PATH:
            continue
        path = repo / relative_path
        content = path.read_bytes()
        phase = next(
            phase_name
            for prefix, phase_name in phase_for_path.items()
            if relative_path.startswith(prefix)
        )
        artifacts.append(
            {
                "path": relative_path,
                "phase": phase,
                "required": True,
                "exists": True,
                "fresh": True,
                "valid": True,
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "mtime_ns": path.stat().st_mtime_ns,
            }
        )
    phases = {
        phase: {"required": True, "success": publication_ready}
        for phase in ("report_text", "archive", "html_report", "daily_news")
    }
    phases["og_image"] = {"required": False, "success": False}
    auto_collect_main._write_run_result(
        repo,
        REPORT_DATE,
        run_id,
        datetime.now(timezone.utc),
        phases,
        artifacts,
    )


def create_repo(tmp_path: Path, *, include_optional: bool = False) -> tuple[Path, object]:
    repo = tmp_path / "daily-report-repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "user.email", "test@example.com")
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)
    repo_manifest = repo / "scripts" / "daily_report_paths.json"
    repo_manifest.parent.mkdir(parents=True, exist_ok=True)
    repo_manifest.write_text(MANIFEST_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    for relative_path in manifest.required:
        write_valid_artifact(repo, relative_path, "baseline")
    write_run_manifest(repo, manifest)
    if include_optional:
        for relative_path in manifest.optional:
            if "*" in relative_path:  # a glob names no single file to create
                continue
            path = repo / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"optional")
    baseline_paths = [
        "scripts/daily_report_paths.json",
        *manifest.required,
        *(path for path in manifest.optional if (repo / path).is_file()),
    ]
    git(repo, "add", "--", *baseline_paths)
    git(repo, "commit", "-m", "baseline")
    return repo, manifest


def run_publisher(
    repo: Path,
    *,
    push: bool = False,
    run_id: str = RUN_ID,
    refresh_manifest: bool = True,
) -> subprocess.CompletedProcess[str]:
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)
    if refresh_manifest:
        write_run_manifest(repo, manifest)
    command = [
        sys.executable,
        str(SCRIPT),
        "--repo",
        str(repo),
        "--date",
        REPORT_DATE.isoformat(),
        "--run-id",
        run_id,
        "--message",
        "publish daily report",
    ]
    if push:
        command.append("--push")
    return subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_manifest_expands_all_date_formats_and_optional_ogp() -> None:
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)

    assert "input/day/0718.txt" in manifest.required
    assert "daily-news/archive/2026-07-18.html" in manifest.required
    assert "presentations/daily_reports/auto_daily_report_2026_07_18.html" in manifest.required
    assert RUN_MANIFEST_PATH in manifest.required
    assert manifest.optional == (
        "presentations/daily_reports/og/2026_07_18.png",
        "public-pages/news/*.json",
    )


def test_historical_news_json_is_allowed_but_other_strays_are_not() -> None:
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)

    # update_news_archive.py regenerates any past date whose input txt looks newer.
    assert manifest.matches("public-pages/news/2026-06-07.json")
    assert manifest.matches("public-pages/news/2026-07-18.json")
    # The glob must not widen past one path segment, nor past that one directory.
    assert not manifest.matches("public-pages/news/nested/2026-06-07.json")
    assert not manifest.matches("public-pages/news/2026-06-07.json.bak")
    assert not manifest.matches("public-pages/api/stray.json")
    assert not manifest.matches(".env")


def test_required_manifest_entry_rejects_a_glob(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"required": ["public-pages/news/*.json"], "optional": []}),
        encoding="utf-8",
    )

    try:
        load_manifest(manifest_path, REPORT_DATE)
    except ValueError as error:
        assert "must not contain" in str(error)
    else:  # pragma: no cover - guards against a silently accepted glob
        raise AssertionError("a globbed required path must be rejected")


def test_regenerated_historical_news_json_publishes_with_the_day(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    today_path = "public-pages/news/2026-07-18.json"
    historical_path = "public-pages/news/2026-06-07.json"
    assert today_path in manifest.required
    write_valid_artifact(repo, today_path, "today")
    (repo / historical_path).write_text("regenerated by update_news_archive\n", encoding="utf-8")

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    committed = git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines()
    assert committed == sorted((today_path, historical_path, RUN_MANIFEST_PATH))


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
        write_valid_artifact(repo, relative_path, "updated")

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    committed = git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines()
    assert committed == sorted((*changed, RUN_MANIFEST_PATH))
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_missing_required_path_rejects_before_staging(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    (repo / manifest.required[0]).unlink()
    head_before = git(repo, "rev-parse", "HEAD").stdout

    result = run_publisher(repo, refresh_manifest=False)

    assert result.returncode != 0
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""
    assert git(repo, "rev-parse", "HEAD").stdout == head_before


def test_wrong_run_id_rejects_before_staging(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    changed = repo / manifest.required[0]
    changed.write_text("fresh output\n", encoding="utf-8")
    write_run_manifest(repo, manifest, run_id=RUN_ID)

    result = run_publisher(repo, run_id="different-run", refresh_manifest=False)

    assert result.returncode != 0
    assert "run_id" in result.stderr
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_unpublishable_run_manifest_rejects_before_staging(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    changed = repo / manifest.required[0]
    changed.write_text("fresh output\n", encoding="utf-8")
    write_run_manifest(repo, manifest, publication_ready=False)

    result = run_publisher(repo, refresh_manifest=False)

    assert result.returncode != 0
    assert "not publication-ready" in result.stderr
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_artifact_changed_after_run_manifest_rejects_before_staging(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    changed = repo / manifest.required[0]
    changed.write_text("fresh output\n", encoding="utf-8")
    write_run_manifest(repo, manifest)
    changed.write_text("tampered after generation\n", encoding="utf-8")

    result = run_publisher(repo, refresh_manifest=False)

    assert result.returncode != 0
    assert "hash mismatch" in result.stderr
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


@pytest.mark.parametrize(
    ("relative_path", "invalid_content", "expected_error"),
    [
        ("presentations/auto_daily_report.json", "{", "invalid JSON artifact"),
        ("presentations/auto_daily_report.html", "", "empty required artifact"),
        (
            "daily-news/data.json",
            json.dumps({"date": "2000-01-01", "items": [{"title": "wrong"}]}),
            "artifact date mismatch",
        ),
    ],
)
def test_semantically_invalid_current_run_artifact_rejects_before_staging(
    tmp_path: Path,
    relative_path: str,
    invalid_content: str,
    expected_error: str,
) -> None:
    repo, manifest = create_repo(tmp_path)
    (repo / relative_path).write_text(invalid_content, encoding="utf-8")
    write_run_manifest(repo, manifest)

    result = run_publisher(repo, refresh_manifest=False)

    assert result.returncode != 0
    assert expected_error in result.stderr
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_run_manifest_requires_the_known_required_phases(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    write_run_manifest(repo, manifest)
    result_path = repo / RUN_MANIFEST_PATH
    result_data = json.loads(result_path.read_text(encoding="utf-8"))
    result_data["phases"] = {}
    result_path.write_text(json.dumps(result_data), encoding="utf-8")

    result = run_publisher(repo, refresh_manifest=False)

    assert result.returncode != 0
    assert "missing required phase" in result.stderr
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_run_manifest_failure_count_must_match_required_phase_failures(
    tmp_path: Path,
) -> None:
    repo, manifest = create_repo(tmp_path)
    write_run_manifest(repo, manifest)
    result_path = repo / RUN_MANIFEST_PATH
    result_data = json.loads(result_path.read_text(encoding="utf-8"))
    result_data["failure_count"] = 9
    result_path.write_text(json.dumps(result_data), encoding="utf-8")

    result = run_publisher(repo, refresh_manifest=False)

    assert result.returncode != 0
    assert "failure_count" in result.stderr
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


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
    write_valid_artifact(repo, archive_name, "updated archive")

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    run_result = json.loads((repo / RUN_MANIFEST_PATH).read_text(encoding="utf-8"))
    assert run_result["failure_count"] == 1
    assert run_result["required_failure_count"] == 0
    assert git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines() == sorted(
        (archive_name, RUN_MANIFEST_PATH)
    )


def test_ignored_required_file_is_discovered_and_force_added(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    ignored_path = manifest.required[0]
    (repo / ".gitignore").write_text("input/\n", encoding="utf-8")
    git(repo, "rm", "--cached", "--", ignored_path)
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "ignore generated input")

    assert git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout == ""
    assert (repo / ignored_path).is_file()

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    assert git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines() == sorted(
        (ignored_path, RUN_MANIFEST_PATH)
    )


def test_dirty_manifest_cannot_self_allow_an_ignored_secret(
    monkeypatch, tmp_path: Path
) -> None:
    repo, _manifest = create_repo(tmp_path)
    repo_manifest = repo / "scripts" / "daily_report_paths.json"
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "scripts/daily_report_paths.json")
    git(repo, "commit", "-m", "track publication policy")

    dirty_policy = json.loads(repo_manifest.read_text(encoding="utf-8"))
    dirty_policy["optional"].extend(["scripts/daily_report_paths.json", ".env"])
    repo_manifest.write_text(json.dumps(dirty_policy), encoding="utf-8")
    secret = repo / ".env"
    secret.write_text("TOP_SECRET=must-not-commit\n", encoding="utf-8")
    head_before = git(repo, "rev-parse", "HEAD").stdout
    monkeypatch.setattr(publish_daily_report, "MANIFEST_PATH", repo_manifest)

    write_run_manifest(repo, load_manifest(MANIFEST_PATH, REPORT_DATE))
    result = publish_daily_report.publish(
        repo, REPORT_DATE, RUN_ID, "publish daily report"
    )

    assert result != 0
    assert git(repo, "rev-parse", "HEAD").stdout == head_before
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""
    assert secret.read_text(encoding="utf-8") == "TOP_SECRET=must-not-commit\n"


def test_rebase_retry_revalidates_a_tightened_remote_manifest(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    origin = tmp_path / "origin.git"
    writer = tmp_path / "policy-writer"
    git(tmp_path, "init", "--bare", str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-u", "origin", "HEAD:main")
    git(tmp_path, "--git-dir", str(origin), "symbolic-ref", "HEAD", "refs/heads/main")
    git(tmp_path, "clone", str(origin), str(writer))
    git(writer, "config", "user.name", "Policy Writer")
    git(writer, "config", "user.email", "policy@example.com")

    removed_path = manifest.required[0]
    writer_manifest = writer / "scripts" / "daily_report_paths.json"
    tightened = json.loads(writer_manifest.read_text(encoding="utf-8"))
    tightened["required"].remove("input/day/{MMDD}.txt")
    writer_manifest.write_text(json.dumps(tightened), encoding="utf-8")
    git(writer, "add", "scripts/daily_report_paths.json")
    git(writer, "commit", "-m", "tighten publication policy")
    git(writer, "push", "origin", "main")

    (repo / removed_path).write_text("must not cross tightened policy\n", encoding="utf-8")

    result = run_publisher(repo, push=True)

    assert result.returncode != 0
    remote_subject = git(
        tmp_path,
        "--git-dir",
        str(origin),
        "log",
        "-1",
        "--format=%s",
        "refs/heads/main",
    ).stdout.strip()
    assert remote_subject == "tighten publication policy"


def test_validate_changes_reports_missing_required_path(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    (repo / manifest.required[-1]).unlink()

    errors = validate_changes(repo, manifest)

    assert any("missing required path" in error for error in errors)


def test_publish_stages_the_single_validated_status_snapshot(monkeypatch, tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    validated_path = manifest.required[0]
    write_valid_artifact(repo, validated_path, "validated update")
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

    write_run_manifest(repo, manifest)
    result = publish_daily_report.publish(
        repo, REPORT_DATE, RUN_ID, "publish daily report"
    )

    assert result == 0
    assert add_calls == [("add", "-f", "--", validated_path)]
