from __future__ import annotations

import argparse
import functools
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

SCRIPT_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_REPO_ROOT))

from src.auto_collect.output_validation import validate_output_artifacts


MANIFEST_PATH = Path(__file__).with_name("daily_report_paths.json")
MANIFEST_REPO_PATH = "scripts/daily_report_paths.json"
RUN_RESULT_TEMPLATE = "public-pages/api/auto_daily_report/run/{YYYY-MM-DD}.json"
REQUIRED_RUN_PHASES = ("report_text", "archive", "html_report", "daily_news")


@functools.lru_cache(maxsize=None)
def _pattern_matcher(pattern: str) -> re.Pattern[str]:
    """Compile a manifest entry, where `*` matches within a single path segment.

    update_news_archive.py rewrites public-pages/news/<date>.json for every
    input/day/*.txt whose mtime overtakes its JSON, so a git operation that
    refreshes old day files drags historical dates into the run. Pinning the
    manifest to the report date alone rejected the whole publish when that
    happened (2026-07-20, which cost that day's X posts), hence the glob.
    """
    return re.compile("[^/]*".join(re.escape(part) for part in pattern.split("*")) + r"\Z")


@dataclass(frozen=True)
class PublicationManifest:
    required: tuple[str, ...]
    optional: tuple[str, ...]

    @property
    def allowed(self) -> tuple[str, ...]:
        """Manifest entries as Git pathspecs. Optional entries may contain a `*` glob."""
        return (*self.required, *self.optional)

    def matches(self, path: str) -> bool:
        return any(_pattern_matcher(pattern).match(path) for pattern in self.allowed)


def _expand_path(template: str, report_date: date) -> str:
    values = {
        "MMDD": report_date.strftime("%m%d"),
        "YYYY-MM-DD": report_date.isoformat(),
        "YYYY_MM_DD": report_date.strftime("%Y_%m_%d"),
    }
    expanded = template
    for key, value in values.items():
        expanded = expanded.replace("{" + key + "}", value)
    relative = Path(expanded)
    if relative.is_absolute() or ".." in relative.parts or expanded != relative.as_posix():
        raise ValueError(f"manifest path must be a safe relative POSIX path: {template}")
    return expanded


def _manifest_from_data(data: object, report_date: date) -> PublicationManifest:
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    if set(data) != {"required", "optional"}:
        raise ValueError("manifest must contain exactly required and optional lists")
    if not all(isinstance(data[key], list) and all(isinstance(item, str) for item in data[key]) for key in data):
        raise ValueError("manifest paths must be lists of strings")
    required = tuple(_expand_path(item, report_date) for item in data["required"])
    optional = tuple(_expand_path(item, report_date) for item in data["optional"])
    # Required entries are checked with is_file(), so they must name one real path.
    globbed = [item for item in required if "*" in item]
    if globbed:
        raise ValueError(f"required manifest paths must not contain '*': {globbed}")
    if len(set((*required, *optional))) != len(required) + len(optional):
        raise ValueError("manifest paths must be unique")
    return PublicationManifest(required=required, optional=optional)


def load_manifest(path: Path, report_date: date) -> PublicationManifest:
    return _manifest_from_data(json.loads(path.read_text(encoding="utf-8")), report_date)


def _run_result_path(report_date: date) -> str:
    return _expand_path(RUN_RESULT_TEMPLATE, report_date)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_run_result(
    repo: Path,
    manifest: PublicationManifest,
    report_date: date,
    run_id: str,
) -> list[str]:
    errors: list[str] = []
    relative_result_path = _run_result_path(report_date)
    if relative_result_path not in manifest.required:
        return [f"publication manifest is missing run result: {relative_result_path}"]
    result_path = repo / relative_result_path
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"could not read run result {relative_result_path}: {error}"]
    if not isinstance(data, dict):
        return ["run result must be a JSON object"]
    if data.get("schema_version") != 1:
        errors.append("run result schema_version must be 1")
    if data.get("date") != report_date.isoformat():
        errors.append("run result date does not match requested publication date")
    if data.get("run_id") != run_id:
        errors.append("run result run_id does not match requested run_id")
    if data.get("publication_ready") is not True:
        errors.append("run result is not publication-ready")

    timestamps: list[datetime] = []
    for field in ("started_at", "completed_at"):
        value = data.get(field)
        try:
            parsed = datetime.fromisoformat(value) if isinstance(value, str) else None
        except ValueError:
            parsed = None
        if parsed is None or parsed.tzinfo is None:
            errors.append(f"run result {field} must be a timezone-aware ISO timestamp")
        else:
            timestamps.append(parsed)
    if len(timestamps) == 2 and timestamps[1] < timestamps[0]:
        errors.append("run result completed_at precedes started_at")

    phases = data.get("phases")
    required_phase_failures = 0
    total_phase_failures = 0
    if not isinstance(phases, dict):
        errors.append("run result phases must be an object")
        required_phase_failures = len(REQUIRED_RUN_PHASES)
        total_phase_failures = len(REQUIRED_RUN_PHASES)
    else:
        for name in REQUIRED_RUN_PHASES:
            phase = phases.get(name)
            if not isinstance(phase, dict):
                errors.append(f"run result is missing required phase: {name}")
                required_phase_failures += 1
                total_phase_failures += 1
                continue
            if phase.get("required") is not True:
                errors.append(f"run result phase is not marked required: {name}")
            if phase.get("success") is not True:
                errors.append(f"required run phase failed: {name}")
                required_phase_failures += 1
                total_phase_failures += 1
        for name, phase in phases.items():
            if name in REQUIRED_RUN_PHASES:
                continue
            if not isinstance(phase, dict):
                errors.append(f"run result phase is invalid: {name}")
            elif phase.get("required") is True:
                errors.append(f"run result contains unknown required phase: {name}")
            elif phase.get("success") is not True:
                total_phase_failures += 1

    failure_count = data.get("failure_count")
    if not isinstance(failure_count, int) or isinstance(failure_count, bool):
        errors.append("run result failure_count must be an integer")
    elif failure_count != total_phase_failures:
        errors.append(
            "run result failure_count does not match failed phases"
        )
    required_failure_count = data.get("required_failure_count")
    if not isinstance(required_failure_count, int) or isinstance(required_failure_count, bool):
        errors.append("run result required_failure_count must be an integer")
    elif required_failure_count != required_phase_failures:
        errors.append(
            "run result required_failure_count does not match failed required phases"
        )
    if data.get("publication_ready") is True and required_phase_failures:
        errors.append("publication-ready run result contains failed required phases")

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("run result artifacts must be a list")
        return errors
    by_path: dict[str, dict] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
            errors.append("run result contains an invalid artifact record")
            continue
        relative_path = artifact["path"]
        relative = Path(relative_path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative_path != relative.as_posix()
            or not manifest.matches(relative_path)
        ):
            errors.append(f"run result artifact is outside the publication manifest: {relative_path}")
            continue
        if relative_path in by_path:
            errors.append(f"run result contains a duplicate artifact: {relative_path}")
            continue
        by_path[relative_path] = artifact

    expected = set(manifest.required) - {relative_result_path}
    for relative_path in sorted(expected):
        artifact = by_path.get(relative_path)
        if artifact is None:
            errors.append(f"run result is missing required artifact: {relative_path}")
            continue
        if artifact.get("required") is not True:
            errors.append(f"run result artifact is not marked required: {relative_path}")
        if artifact.get("valid") is not True:
            errors.append(f"run result artifact is not marked valid: {relative_path}")
        if artifact.get("exists") is not True or artifact.get("fresh") is not True:
            errors.append(f"run result artifact is not a fresh current-run output: {relative_path}")
        path = repo / relative_path
        if not path.is_file():
            errors.append(f"run result artifact is missing: {relative_path}")
            continue
        expected_size = artifact.get("size")
        if not isinstance(expected_size, int) or path.stat().st_size != expected_size:
            errors.append(f"run result artifact size mismatch: {relative_path}")
        expected_mtime = artifact.get("mtime_ns")
        if not isinstance(expected_mtime, int) or path.stat().st_mtime_ns != expected_mtime:
            errors.append(f"run result artifact mtime mismatch: {relative_path}")
        expected_hash = artifact.get("sha256")
        if not isinstance(expected_hash, str) or _sha256(path) != expected_hash:
            errors.append(f"run result artifact hash mismatch: {relative_path}")
    errors.extend(validate_output_artifacts(repo, sorted(expected), report_date))
    return errors


def _git(repo: Path, args: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _load_manifest_from_head(repo: Path, report_date: date) -> PublicationManifest:
    result = _git(repo, ("show", f"HEAD:{MANIFEST_REPO_PATH}"))
    return _manifest_from_data(json.loads(result.stdout), report_date)


def _status_paths(repo: Path) -> tuple[str, ...]:
    result = _git(repo, ("status", "--porcelain=v1", "-z", "--untracked-files=all"))
    records = result.stdout.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise ValueError(f"unexpected git status record: {record!r}")
        status, path = record[:2], record[3:]
        paths.append(path)
        if "R" in status or "C" in status:
            if index >= len(records) or not records[index]:
                raise ValueError("rename or copy status record is missing its source path")
            paths.append(records[index])
            index += 1
    return tuple(paths)


def _has_staged_changes(repo: Path) -> bool:
    result = _git(repo, ("diff", "--cached", "--quiet"), check=False)
    if result.returncode in (0, 1):
        return result.returncode == 1
    raise RuntimeError(result.stderr.strip() or "could not inspect the Git index")


def _ignored_manifest_paths(repo: Path, manifest: PublicationManifest) -> tuple[str, ...]:
    result = _git(
        repo,
        (
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
            "--",
            *sorted(manifest.allowed),
        ),
    )
    return tuple(path for path in result.stdout.split("\0") if path)


def _changed_paths(repo: Path, manifest: PublicationManifest) -> tuple[str, ...]:
    visible = _status_paths(repo)
    ignored = _ignored_manifest_paths(repo, manifest)
    return tuple(dict.fromkeys((*visible, *ignored)))


def validate_changes(
    repo: Path,
    manifest: PublicationManifest,
    *,
    changed_paths: tuple[str, ...] | None = None,
) -> list[str]:
    errors: list[str] = []
    if not repo.is_dir():
        return [f"repository does not exist: {repo}"]
    for relative_path in manifest.required:
        if not (repo / relative_path).is_file():
            errors.append(f"missing required path: {relative_path}")
    try:
        if _has_staged_changes(repo):
            errors.append("pre-existing staged changes are not allowed")
        if changed_paths is None:
            changed_paths = _changed_paths(repo, manifest)
    except (RuntimeError, subprocess.CalledProcessError, ValueError) as error:
        errors.append(str(error))
        return errors
    outside = sorted(path for path in set(changed_paths) if not manifest.matches(path))
    errors.extend(f"manifest excludes changed path: {path}" for path in outside)
    return errors


def _cached_paths(repo: Path) -> tuple[str, ...]:
    result = _git(repo, ("diff", "--cached", "--name-only", "-z"))
    return tuple(path for path in result.stdout.split("\0") if path)


def _head_commit_paths(repo: Path) -> tuple[str, ...]:
    result = _git(repo, ("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", "HEAD"))
    return tuple(path for path in result.stdout.split("\0") if path)


def _push_with_one_rebase_retry(repo: Path, report_date: date, run_id: str) -> int:
    initial_push = _git(repo, ("push", "origin", "HEAD:main"), check=False)
    if initial_push.returncode == 0:
        return 0
    fetch = _git(repo, ("fetch", "origin", "main"), check=False)
    if fetch.returncode != 0:
        print(fetch.stderr.strip() or "git fetch origin main failed", file=sys.stderr)
        return 1
    # The replayed commit is the override itself, so it must win over the cloud run
    # that landed on origin/main while the pipeline was running. In a rebase "theirs"
    # is the commit being replayed; the manifest already constrains its paths to
    # generated daily-report artifacts, and validation below re-checks the result.
    rebase = _git(repo, ("rebase", "-X", "theirs", "origin/main"), check=False)
    if rebase.returncode != 0:
        _git(repo, ("rebase", "--abort"), check=False)
        print(rebase.stderr.strip() or "git rebase origin/main failed", file=sys.stderr)
        return 1
    try:
        rebased_manifest = _load_manifest_from_head(repo, report_date)
        rebased_paths = _head_commit_paths(repo)
        errors = validate_changes(repo, rebased_manifest, changed_paths=rebased_paths)
        errors.extend(validate_run_result(repo, rebased_manifest, report_date, run_id))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"post-rebase publication validation failed: {error}", file=sys.stderr)
        return 1
    if not rebased_paths:
        print("post-rebase publication commit has no changed paths", file=sys.stderr)
        return 1
    if errors:
        print("post-rebase publication rejected:\n" + "\n".join(errors), file=sys.stderr)
        return 1
    retry = _git(repo, ("push", "origin", "HEAD:main"), check=False)
    if retry.returncode != 0:
        print(retry.stderr.strip() or "git push retry failed", file=sys.stderr)
        return 1
    return 0


def publish(
    repo: Path,
    report_date: date,
    run_id: str,
    message: str,
    *,
    push: bool = False,
) -> int:
    try:
        manifest = _load_manifest_from_head(repo, report_date)
        changed_paths = _changed_paths(repo, manifest)
        errors = validate_changes(repo, manifest, changed_paths=changed_paths)
        errors.extend(validate_run_result(repo, manifest, report_date, run_id))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    if not changed_paths:
        print("no manifest paths have changed", file=sys.stderr)
        return 1
    _git(repo, ("add", "-f", "--", *changed_paths))
    cached_paths = _cached_paths(repo)
    if not all(manifest.matches(path) for path in cached_paths):
        print("staging produced paths outside the manifest", file=sys.stderr)
        return 1
    if not cached_paths:
        print("no manifest paths were staged", file=sys.stderr)
        return 1
    try:
        _git(repo, ("commit", "-m", message))
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip() or "git commit failed", file=sys.stderr)
        return 1
    return _push_with_one_rebase_retry(repo, report_date, run_id) if push else 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a daily report from an explicit manifest.")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--push", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return publish(
        args.repo.resolve(), args.date, args.run_id, args.message, push=args.push
    )


if __name__ == "__main__":
    raise SystemExit(main())
