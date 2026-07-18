from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
POWERSHELL = "powershell.exe"


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=check, text=True, capture_output=True)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", *args, cwd=repo, check=check)


def write_runtime_files(repo: Path) -> None:
    (repo / "scripts").mkdir()
    (repo / "src" / "auto_collect").mkdir(parents=True)
    (repo / "scripts" / "publish_daily_report.py").write_text(
        "from __future__ import annotations\n"
        "import json, pathlib, sys\n"
        "repo = pathlib.Path(sys.argv[sys.argv.index('--repo') + 1])\n"
        "(repo / 'publisher_args.json').write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n",
        encoding="utf-8",
    )
    (repo / "src" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "auto_collect" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "auto_collect" / "main.py").write_text(
        "from __future__ import annotations\n"
        "import json, pathlib, sys\n"
        "pathlib.Path('pipeline_args.json').write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n",
        encoding="utf-8",
    )
    (repo / "base.txt").write_text("base\n", encoding="utf-8")


def make_runtime(tmp_path: Path) -> tuple[Path, Path, Path]:
    origin = tmp_path / "origin.git"
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    run("git", "init", "--bare", str(origin), cwd=tmp_path)
    run("git", "init", "-b", "main", str(source), cwd=tmp_path)
    git(source, "config", "user.email", "test@example.invalid")
    git(source, "config", "user.name", "Test User")
    write_runtime_files(source)
    git(source, "add", ".")
    git(source, "commit", "-m", "initial")
    git(source, "remote", "add", "origin", str(origin))
    git(source, "push", "-u", "origin", "main")
    run("git", "clone", "--branch", "main", str(origin), str(runtime), cwd=tmp_path)
    git(runtime, "config", "user.email", "test@example.invalid")
    git(runtime, "config", "user.name", "Test User")
    return origin, source, runtime


def run_runner(repo: Path, log_path: Path) -> subprocess.CompletedProcess[str]:
    return run(
        POWERSHELL,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPTS / "run_daily_override.ps1"),
        "-RepoPath",
        str(repo),
        "-PythonPath",
        sys.executable,
        "-LogPath",
        str(log_path),
        cwd=ROOT,
        check=False,
    )


def test_batch_is_a_thin_root_relative_launcher_without_unsafe_git_commands() -> None:
    launcher = (SCRIPTS / "run_daily_override.bat").read_text(encoding="utf-8")
    assert 'for %%I in ("%~dp0..") do set "REPO=%%~fI"' in launcher
    assert "run_daily_override.ps1" in launcher
    assert 'set REPO=C:\\develop\\ai-news-site' not in launcher
    for forbidden in ("git add -u", "git add -A", "git reset", "git clean"):
        assert forbidden not in launcher.lower()


def test_installer_plan_only_emits_the_required_scheduled_task_contract(tmp_path: Path) -> None:
    checkout = tmp_path / "automation"
    result = run(
        POWERSHELL,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPTS / "register_daily_override_task.ps1"),
        "-CheckoutPath",
        str(checkout),
        "-RepositoryUrl",
        "https://github.com/example/visionhub.git",
        "-TaskName",
        "VisionHub Daily Override Test",
        "-At",
        "08:00",
        "-PlanOnly",
        cwd=ROOT,
    )
    plan = json.loads(result.stdout)
    assert plan["checkoutPath"] == str(checkout.resolve())
    assert plan["taskName"] == "VisionHub Daily Override Test"
    assert plan["action"]["execute"] == "cmd.exe"
    assert plan["action"]["workingDirectory"] == str(checkout.resolve())
    assert plan["trigger"] == {"dailyAt": "08:00"}
    assert plan["principal"] == {"logonType": "InteractiveToken"}
    assert plan["settings"] == {
        "startWhenAvailable": True,
        "multipleInstances": "IgnoreNew",
        "executionTimeLimit": "PT1H",
        "disallowStartIfOnBatteries": False,
        "stopIfGoingOnBatteries": False,
    }
    assert not checkout.exists()


def test_runner_stashes_tracked_and_untracked_changes_for_recovery(tmp_path: Path) -> None:
    _, _, runtime = make_runtime(tmp_path)
    (runtime / "base.txt").write_text("dirty\n", encoding="utf-8")
    (runtime / "untracked.txt").write_text("keep me\n", encoding="utf-8")

    result = run_runner(runtime, tmp_path / "runner.log")

    assert result.returncode == 0, result.stderr
    stash = git(runtime, "stash", "list").stdout
    assert "daily override preflight" in stash
    assert "untracked.txt" in git(runtime, "stash", "show", "--include-untracked", "--name-only", "stash@{0}").stdout


def test_runner_fast_forwards_behind_only_checkout_and_does_not_abort_without_ollama(tmp_path: Path) -> None:
    _, source, runtime = make_runtime(tmp_path)
    (source / "cloud.txt").write_text("cloud\n", encoding="utf-8")
    git(source, "add", "cloud.txt")
    git(source, "commit", "-m", "cloud update")
    git(source, "push")

    result = run_runner(runtime, tmp_path / "runner.log")

    assert result.returncode == 0, result.stderr
    assert (runtime / "cloud.txt").read_text(encoding="utf-8") == "cloud\n"
    assert json.loads((runtime / "pipeline_args.json").read_text(encoding="utf-8")) == ["--provider", "ollama", "--force"]


def test_runner_invokes_the_reviewed_publisher_with_exact_arguments(tmp_path: Path) -> None:
    _, _, runtime = make_runtime(tmp_path)
    report_date = date.today().isoformat()

    result = run_runner(runtime, tmp_path / "runner.log")

    assert result.returncode == 0, result.stderr
    assert json.loads((runtime / "publisher_args.json").read_text(encoding="utf-8")) == [
        "--repo",
        str(runtime.resolve()),
        "--date",
        report_date,
        "--message",
        f"chore(report): local override {report_date}",
        "--push",
    ]


def test_runner_aborts_a_rebase_conflict_without_losing_local_commit_or_stash(tmp_path: Path) -> None:
    _, source, runtime = make_runtime(tmp_path)
    (runtime / "base.txt").write_text("local commit\n", encoding="utf-8")
    git(runtime, "add", "base.txt")
    git(runtime, "commit", "-m", "local change")
    (runtime / "untracked.txt").write_text("preserve\n", encoding="utf-8")
    (source / "base.txt").write_text("remote commit\n", encoding="utf-8")
    git(source, "add", "base.txt")
    git(source, "commit", "-m", "remote change")
    git(source, "push")

    result = run_runner(runtime, tmp_path / "runner.log")

    assert result.returncode != 0
    assert git(runtime, "log", "-1", "--format=%s").stdout.strip() == "local change"
    assert "daily override preflight" in git(runtime, "stash", "list").stdout
    assert git(runtime, "status", "--porcelain").stdout == ""
