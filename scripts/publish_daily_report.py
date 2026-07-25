from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence


MANIFEST_PATH = Path(__file__).with_name("daily_report_paths.json")
MANIFEST_REPO_PATH = "scripts/daily_report_paths.json"


@dataclass(frozen=True)
class PublicationManifest:
    required: tuple[str, ...]
    optional: tuple[str, ...]

    @property
    def allowed(self) -> frozenset[str]:
        return frozenset((*self.required, *self.optional))


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
    if len(set((*required, *optional))) != len(required) + len(optional):
        raise ValueError("manifest paths must be unique")
    return PublicationManifest(required=required, optional=optional)


def load_manifest(path: Path, report_date: date) -> PublicationManifest:
    return _manifest_from_data(json.loads(path.read_text(encoding="utf-8")), report_date)


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
    outside = sorted(set(changed_paths) - manifest.allowed)
    errors.extend(f"manifest excludes changed path: {path}" for path in outside)
    return errors


def _cached_paths(repo: Path) -> tuple[str, ...]:
    result = _git(repo, ("diff", "--cached", "--name-only", "-z"))
    return tuple(path for path in result.stdout.split("\0") if path)


def _head_commit_paths(repo: Path) -> tuple[str, ...]:
    result = _git(repo, ("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", "HEAD"))
    return tuple(path for path in result.stdout.split("\0") if path)


def _push_with_one_rebase_retry(repo: Path, report_date: date) -> int:
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


def publish(repo: Path, report_date: date, message: str, *, push: bool = False) -> int:
    try:
        manifest = _load_manifest_from_head(repo, report_date)
        changed_paths = _changed_paths(repo, manifest)
        errors = validate_changes(repo, manifest, changed_paths=changed_paths)
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
    if not set(cached_paths).issubset(manifest.allowed):
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
    return _push_with_one_rebase_retry(repo, report_date) if push else 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a daily report from an explicit manifest.")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--push", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return publish(args.repo.resolve(), args.date, args.message, push=args.push)


if __name__ == "__main__":
    raise SystemExit(main())
