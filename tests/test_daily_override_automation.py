from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
POWERSHELL = "powershell.exe"
RUNTIME_MARKER = "visionhub-daily-news-override-runtime.json"


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    encoding = "oem" if os.name == "nt" and args[0] == POWERSHELL else "utf-8"
    return subprocess.run(args, cwd=cwd, check=check, text=True, encoding=encoding, capture_output=True)


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
    (repo / "src" / "auto_collect" / "provider_preflight.py").write_text(
        "import json, os, pathlib, sys\n"
        "pathlib.Path('preflight_args.json').write_text(json.dumps(sys.argv[1:]))\n"
        "raise SystemExit(int(os.environ.get('TASK_PREFLIGHT_EXIT', '0')))\n",
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
    (runtime / ".git" / RUNTIME_MARKER).write_text(
        json.dumps({"checkoutPath": str(runtime.resolve())}), encoding="utf-8"
    )
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
        assert forbidden.lower() not in launcher.lower()


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
    action_arguments = plan["action"]["arguments"]
    assert action_arguments.startswith("/d /s /c ")
    assert action_arguments.endswith(f'""{checkout.resolve() / "scripts" / "run_daily_override.bat"}""')
    assert plan["action"]["workingDirectory"] == str(checkout.resolve())
    assert plan["trigger"] == {"dailyAt": "08:00"}
    assert plan["principal"] == {"logonType": "InteractiveToken"}
    assert plan["settings"] == {
        "startWhenAvailable": True,
        "wakeToRun": False,
        "multipleInstances": "IgnoreNew",
        "executionTimeLimit": "PT1H",
        "disallowStartIfOnBatteries": False,
        "stopIfGoingOnBatteries": False,
    }
    assert not checkout.exists()


def test_installer_default_replaces_the_existing_scheduled_task(tmp_path: Path) -> None:
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
        "-PlanOnly",
        cwd=ROOT,
    )

    assert json.loads(result.stdout)["taskName"] == "visionhub-daily-news-override"


def test_installer_uses_the_windows_scheduled_task_interactive_enum() -> None:
    installer = (SCRIPTS / "register_daily_override_task.ps1").read_text(encoding="utf-8")

    assert re.search(r"-LogonType\s+Interactive(?:\s|$)", installer)
    assert "-LogonType InteractiveToken" not in installer


def test_runner_rejects_a_normal_clone_without_the_runtime_marker(tmp_path: Path) -> None:
    _, _, runtime = make_runtime(tmp_path)
    (runtime / ".git" / RUNTIME_MARKER).unlink()
    log_path = tmp_path / "runner.log"

    result = run_runner(runtime, log_path)

    assert result.returncode != 0
    assert "runtime marker" in (result.stdout + result.stderr).lower()
    assert not log_path.exists()


def test_runner_rejects_a_linked_worktree_git_file_shape(tmp_path: Path) -> None:
    linked_worktree = tmp_path / "linked-worktree"
    linked_worktree.mkdir()
    (linked_worktree / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    log_path = tmp_path / "runner.log"

    result = run_runner(linked_worktree, log_path)

    assert result.returncode != 0
    assert "independent git clone" in (result.stdout + result.stderr).lower()
    assert not log_path.exists()


def test_runner_stashes_tracked_and_untracked_changes_for_recovery(tmp_path: Path) -> None:
    _, _, runtime = make_runtime(tmp_path)
    (runtime / "base.txt").write_text("dirty\n", encoding="utf-8")
    (runtime / "untracked.txt").write_text("keep me\n", encoding="utf-8")
    log_path = tmp_path / "runner.log"

    result = run_runner(runtime, log_path)

    assert result.returncode == 0, result.stderr
    stash = git(runtime, "stash", "list").stdout
    assert re.search(r"daily-override recovery \d{8}T\d{6}", stash)
    assert "untracked.txt" in git(runtime, "stash", "show", "--include-untracked", "--name-only", "stash@{0}").stdout
    stash_id = git(runtime, "rev-parse", "refs/stash").stdout.strip()
    assert stash_id in log_path.read_text(encoding="utf-8-sig")


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
        "--require-quality",
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
    assert re.search(
        r"daily-override recovery \d{8}T\d{6}",
        git(runtime, "stash", "list").stdout,
    )
    assert git(runtime, "status", "--porcelain").stdout == ""


def test_runner_discards_a_stale_override_commit_and_completes_the_run(tmp_path: Path) -> None:
    # A publish whose push lost the race to the cloud run leaves this commit behind.
    # Rebasing it the next morning conflicts forever, which is what silently stopped
    # X bookmarks from reaching daily-news for three days in 2026-07.
    _, source, runtime = make_runtime(tmp_path)
    (runtime / "base.txt").write_text("stale override\n", encoding="utf-8")
    git(runtime, "add", "base.txt")
    git(runtime, "commit", "-m", "chore(report): local override 2026-07-23")
    (source / "base.txt").write_text("cloud run\n", encoding="utf-8")
    git(source, "add", "base.txt")
    git(source, "commit", "-m", "remote change")
    git(source, "push")
    log_path = tmp_path / "runner.log"

    result = run_runner(runtime, log_path)

    assert result.returncode == 0, result.stderr
    assert git(runtime, "log", "-1", "--format=%s").stdout.strip() == "remote change"
    assert (runtime / "publisher_args.json").is_file()
    assert "Discarding leftover override commit" in log_path.read_text(encoding="utf-8")


def write_dated_files(repo: Path, iso_date: str, body: str) -> dict[str, str]:
    """Create the dated files only that day's run produces."""
    underscored = iso_date.replace("-", "_")
    dated = {
        f"daily-news/archive/{iso_date}.html": f"<p>archive {body}</p>\n",
        f"input/day/{iso_date[5:].replace('-', '')}.txt": f"input {body}\n",
        f"presentations/daily_reports/auto_daily_report_{underscored}.html": f"<p>report {body}</p>\n",
        f"presentations/daily_reports/og/{underscored}.png": f"png {body}\n",
        f"presentations/model_watch/{iso_date}.json": f'{{"watch": "{body}"}}\n',
        f"public-pages/news/daily/{iso_date}.json": f'{{"daily": "{body}"}}\n',
    }
    for relative, text in dated.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return dated


def write_override_files(repo: Path, iso_date: str, body: str) -> dict[str, str]:
    """Create the dated files a local override adds, plus the shared files it rewrites."""
    dated = write_dated_files(repo, iso_date, body)
    (repo / "base.txt").write_text(f"{body} override\n", encoding="utf-8")
    (repo / "presentations" / "daily_reports" / "index.json").write_text(f'{{"index": "{body}"}}\n', encoding="utf-8")
    return dated


def commit_leftover_override(repo: Path, iso_date: str, body: str) -> tuple[str, dict[str, str]]:
    dated = write_override_files(repo, iso_date, body)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", f"chore(report): local override {iso_date}")
    return git(repo, "rev-parse", "HEAD").stdout.strip(), dated


def commit_leftover_backfill(repo: Path, iso_date: str, body: str) -> tuple[str, dict[str, str]]:
    dated = write_dated_files(repo, iso_date, body)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", f"chore(report): backfill daily-news {iso_date}")
    return git(repo, "rev-parse", "HEAD").stdout.strip(), dated


def committed_paths(repo: Path, rev: str) -> set[str]:
    return set(git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", rev).stdout.split())


def push_conflicting_cloud_run(source: Path, extra: dict[str, str] | None = None) -> None:
    (source / "base.txt").write_text("cloud run\n", encoding="utf-8")
    for relative, text in (extra or {}).items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(source, "add", "-A")
    git(source, "commit", "-m", "remote change")
    git(source, "push")


def test_runner_rescues_dated_files_of_a_past_override_commit_before_discarding_it(tmp_path: Path) -> None:
    # 2026-10-29: override b29c8d78 lost the push race, the next morning reset it away,
    # and the dated archive/report/snapshot files had to be restored by hand (b52b3cf5).
    origin, source, runtime = make_runtime(tmp_path)
    leftover_sha, dated = commit_leftover_override(runtime, "2026-10-29", "local")
    already_restored = "public-pages/news/daily/2026-10-29.json"
    push_conflicting_cloud_run(source, {already_restored: '{"daily": "hand restored"}\n'})
    log_path = tmp_path / "runner.log"

    result = run_runner(runtime, log_path)

    assert result.returncode == 0, result.stderr
    # The backfill must reach origin only inside the publisher's HEAD:main push. Pushed
    # on its own, its input/day/*.txt triggers generate-daily-news-json.yml, whose bot
    # commit lands within a minute and rejects that day's strict publish as
    # non-fast-forward (2026-10-31: b52b3cf5 08:34:56 -> 6ed4228c 08:35:39).
    assert git(origin, "log", "-1", "--format=%s", "main").stdout.strip() == "remote change"
    assert git(runtime, "log", "-1", "--format=%s").stdout.strip() == "chore(report): backfill daily-news 2026-10-29"
    assert git(runtime, "rev-parse", "HEAD~1").stdout == git(origin, "rev-parse", "main").stdout
    rescued = committed_paths(runtime, "HEAD")
    assert rescued == set(dated) - {already_restored}
    for relative in rescued:
        assert git(runtime, "show", f"HEAD:{relative}").stdout == dated[relative]
    assert git(runtime, "show", f"HEAD:{already_restored}").stdout == '{"daily": "hand restored"}\n'
    assert git(runtime, "show", "HEAD:base.txt").stdout == "cloud run\n"
    assert git(runtime, "show", "HEAD:presentations/daily_reports/index.json", check=False).returncode != 0
    backup_ref = f"refs/override-backup/2026-10-29-{leftover_sha[:10]}"
    assert git(runtime, "rev-parse", backup_ref).stdout.strip() == leftover_sha
    assert backup_ref in log_path.read_text(encoding="utf-8")
    assert (runtime / "publisher_args.json").is_file()


def test_runner_rescues_a_leftover_backfill_again_when_its_publish_never_reached_origin(tmp_path: Path) -> None:
    # The backfill rides on that day's publisher push, so a failed publish leaves both
    # the backfill and the override behind. Next morning both are past days: rebuild
    # them on the new origin/main instead of rebasing (conflict) or dropping (data loss).
    origin, source, runtime = make_runtime(tmp_path)
    backfill_sha, backfill_dated = commit_leftover_backfill(runtime, "2026-10-29", "rescued once")
    override_sha, override_dated = commit_leftover_override(runtime, "2026-10-30", "local")
    push_conflicting_cloud_run(source)
    log_path = tmp_path / "runner.log"

    result = run_runner(runtime, log_path)

    assert result.returncode == 0, result.stderr
    assert git(origin, "log", "-1", "--format=%s", "main").stdout.strip() == "remote change"
    assert git(runtime, "log", "-3", "--format=%s").stdout.split("\n")[:3] == [
        "chore(report): backfill daily-news 2026-10-30",
        "chore(report): backfill daily-news 2026-10-29",
        "remote change",
    ]
    assert git(runtime, "rev-parse", "HEAD~2").stdout == git(origin, "rev-parse", "main").stdout
    assert committed_paths(runtime, "HEAD~1") == set(backfill_dated)
    assert committed_paths(runtime, "HEAD") == set(override_dated)
    for relative, text in {**backfill_dated, **override_dated}.items():
        assert git(runtime, "show", f"HEAD:{relative}").stdout == text
    assert git(runtime, "show", "HEAD:base.txt").stdout == "cloud run\n"
    log = log_path.read_text(encoding="utf-8")
    for iso_date, sha in (("2026-10-29", backfill_sha), ("2026-10-30", override_sha)):
        backup_ref = f"refs/override-backup/{iso_date}-{sha[:10]}"
        assert git(runtime, "rev-parse", backup_ref).stdout.strip() == sha
        assert backup_ref in log
    assert (runtime / "publisher_args.json").is_file()


def test_runner_backs_up_todays_override_commit_and_regenerates_instead_of_rebasing(tmp_path: Path) -> None:
    # A same-day rerun after a lost push used to rebase today's leftover onto the
    # cloud run and throw on the generated-artifact conflict every time.
    origin, source, runtime = make_runtime(tmp_path)
    today = date.today().isoformat()
    leftover_sha, _ = commit_leftover_override(runtime, today, "today")
    push_conflicting_cloud_run(source)
    log_path = tmp_path / "runner.log"

    result = run_runner(runtime, log_path)

    assert result.returncode == 0, result.stderr
    assert git(runtime, "log", "-1", "--format=%s").stdout.strip() == "remote change"
    assert git(origin, "log", "-1", "--format=%s", "main").stdout.strip() == "remote change"
    backup_ref = f"refs/override-backup/{today}-{leftover_sha[:10]}"
    assert git(runtime, "rev-parse", backup_ref).stdout.strip() == leftover_sha
    assert backup_ref in log_path.read_text(encoding="utf-8")
    assert (runtime / "publisher_args.json").is_file()


def test_cloud_workflow_uses_the_safe_manifest_publisher() -> None:
    workflow = (ROOT / ".github" / "workflows" / "auto-daily-report-cloud-fallback.yml").read_text(
        encoding="utf-8"
    )

    assert "- cron: '53 20 * * *'" in workflow
    assert "workflow_dispatch: {}" in workflow
    assert "permissions:\n  contents: write" in workflow
    assert "concurrency:\n  group: repo-push\n  cancel-in-progress: false" in workflow
    assert "primary:\n    runs-on: ubuntu-latest\n    timeout-minutes: 30" in workflow
    assert "env:\n      TZ: Asia/Tokyo" in workflow
    assert "python -m src.auto_collect.main --provider nvidia --force" in workflow
    assert 'git config user.name "github-actions[bot]"' in workflow
    assert 'git config user.email "41898282+github-actions[bot]@users.noreply.github.com"' in workflow
    assert "REPORT_DATE=\"$(date +%F)\"" in workflow
    publisher_command = "\n".join(
        (
            "python scripts/publish_daily_report.py \\",
            "            --repo . \\",
            '            --date "$REPORT_DATE" \\',
            '            --require-quality \\',
            '            --message "chore(report): cloud primary run $REPORT_DATE" \\',
            "            --push",
        )
    )
    assert publisher_command in workflow
    assert "- name: Warn if local override missing for 2+ days" in workflow
    assert (
        "::warning::No 'local override' commit in the last 2 days — X bookmarks may be missing "
        "on visionhub.jp/daily-news/. Check Windows Task Scheduler "
        "'visionhub-daily-news-override' on the user's PC."
    ) in workflow

    lower_workflow = workflow.lower()
    for prohibited in (
        "git add",
        "git commit",
        "git push",
        "git add -a",
        "git add -u",
        "git reset",
        "git clean",
    ):
        assert prohibited not in lower_workflow


def test_runner_blocks_generation_and_publish_when_preflight_fails(tmp_path, monkeypatch):
    _, _, runtime = make_runtime(tmp_path)
    monkeypatch.setenv("TASK_PREFLIGHT_EXIT", "1")
    result = run_runner(runtime, tmp_path / "blocked.log")
    assert result.returncode != 0
    assert (runtime / "preflight_args.json").exists()
    assert not (runtime / "pipeline_args.json").exists()
    assert not (runtime / "publisher_args.json").exists()
