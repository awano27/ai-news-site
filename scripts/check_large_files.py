#!/usr/bin/env python3
"""Reject newly added Git blobs larger than 5 MiB."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAX_BYTES = 5 * 1024 * 1024
SHA_RE = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\Z")


class CheckError(Exception):
    """An expected validation error that is safe to show in CI logs."""


def try_git(*args: str) -> bytes | None:
    """Run Git without exposing stderr, which can contain a remote URL/token."""
    try:
        completed = subprocess.run(
            ["git", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CheckError("git is not installed or not on PATH") from exc
    return completed.stdout if completed.returncode == 0 else None


def run_git(*args: str) -> bytes:
    output = try_git(*args)
    if output is None:
        raise CheckError("a required git operation failed")
    return output


def added_paths(revision_range: str | None) -> list[str]:
    args = ["diff"]
    if revision_range is None:
        args.append("--cached")
    args.extend(["--diff-filter=A", "--name-only", "-z"])
    if revision_range is not None:
        args.append(revision_range)
    output = run_git(*args)
    return [part.decode("utf-8", errors="surrogateescape") for part in output.split(b"\0") if part]


def blob_size(path: str, revision_range: str | None) -> int:
    if revision_range is None:
        object_name = f":{path}"
    else:
        if ".." not in revision_range:
            raise CheckError("--range must use A..B Git revision syntax")
        target_revision = revision_range.rsplit("..", 1)[1]
        if not target_revision:
            raise CheckError("--range must include the target revision B")
        object_name = f"{target_revision}:{path}"
    return int(run_git("cat-file", "-s", object_name).strip())


def format_size(size: int) -> str:
    return f"{size / (1024 * 1024):.2f} MiB"


def event_value(event: dict[str, Any], keys: tuple[str, ...], label: str) -> str:
    value: Any = event
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise CheckError(f"missing {label}")
        value = value[key]
    if not isinstance(value, str) or not value:
        raise CheckError(f"missing {label}")
    return value


def parse_sha(value: str, label: str, *, allow_zero: bool = False) -> tuple[str, bool]:
    if not SHA_RE.fullmatch(value):
        raise CheckError(f"invalid {label} SHA")
    normalized = value.lower()
    zero = set(normalized) == {"0"}
    if zero and not allow_zero:
        raise CheckError(f"invalid {label} SHA")
    return normalized, zero


def ensure_commit(sha: str, label: str) -> str:
    """Resolve a commit locally, then fetch its exact validated SHA if needed."""
    resolved = try_git("rev-parse", "--verify", f"{sha}^{{commit}}")
    if resolved is None:
        try_git("fetch", "--no-tags", "origin", sha)
        resolved = try_git("rev-parse", "--verify", f"{sha}^{{commit}}")
    if resolved is None:
        raise CheckError(f"cannot resolve {label} commit")
    return resolved.decode("ascii", errors="strict").strip()


def fetch_default_branch(branch: str) -> str:
    branch_ref = f"refs/heads/{branch}"
    if not branch or try_git("check-ref-format", branch_ref) is None:
        raise CheckError("invalid repository.default_branch")
    remote_ref = f"refs/remotes/origin/{branch}"
    refspec = f"{branch_ref}:{remote_ref}"
    if try_git("fetch", "--no-tags", "origin", refspec) is None:
        raise CheckError("cannot fetch repository.default_branch")
    resolved = try_git("rev-parse", "--verify", f"{remote_ref}^{{commit}}")
    if resolved is None:
        raise CheckError("cannot resolve repository.default_branch")
    return resolved.decode("ascii", errors="strict").strip()


def resolve_merge_base(default_tip: str, target: str) -> str:
    resolved = try_git("merge-base", default_tip, target)
    if resolved is None:
        raise CheckError("zero-before push has no common ancestor with repository.default_branch")
    return resolved.decode("ascii", errors="strict").strip()


@dataclass(frozen=True)
class EventRange:
    before: str
    after: str
    base: str
    reason: str

    @property
    def revision_range(self) -> str:
        return f"{self.base}..{self.after}"


def load_event(path: str) -> dict[str, Any]:
    try:
        event = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckError("invalid event JSON") from exc
    if not isinstance(event, dict):
        raise CheckError("invalid event JSON")
    return event


def event_range(path: str, event_name: str) -> EventRange:
    event = load_event(path)
    if event_name == "pull_request":
        before_raw = event_value(event, ("pull_request", "base", "sha"), "pull request base")
        after_raw = event_value(event, ("pull_request", "head", "sha"), "pull request head")
        before, _ = parse_sha(before_raw, "pull request base")
        after, _ = parse_sha(after_raw, "pull request head")
        return EventRange(
            before,
            ensure_commit(after, "pull request head"),
            ensure_commit(before, "pull request base"),
            "pull-request-base",
        )

    before_raw = event_value(event, ("before",), "push before")
    after_raw = event_value(event, ("after",), "push after")
    before, before_is_zero = parse_sha(before_raw, "push before", allow_zero=True)
    after, after_is_zero = parse_sha(after_raw, "push after", allow_zero=True)
    if after_is_zero:
        raise CheckError("push deletion events are not supported")
    target = ensure_commit(after, "push after")
    if not before_is_zero:
        return EventRange(before, target, ensure_commit(before, "push before"), "push-before")

    branch = event_value(event, ("repository", "default_branch"), "repository.default_branch")
    ref = event_value(event, ("ref",), "push ref")
    if not ref.startswith("refs/heads/") or try_git("check-ref-format", ref) is None:
        raise CheckError("zero-before push ref is not a valid branch ref")
    default_tip = fetch_default_branch(branch)
    if ref == f"refs/heads/{branch}":
        raise CheckError("zero-before push to repository default branch is not supported")
    return EventRange(before, target, resolve_merge_base(default_tip, target), "zero-before-merge-base")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--range", dest="revision_range", metavar="A..B")
    mode.add_argument("--event-path", metavar="PATH")
    parser.add_argument("--event-name", choices=("push", "pull_request"))
    args = parser.parse_args()
    if args.event_path and not args.event_name:
        parser.error("--event-name is required with --event-path")
    if args.event_name and not args.event_path:
        parser.error("--event-path is required with --event-name")

    try:
        event: EventRange | None = None
        revision_range = args.revision_range
        if args.event_path:
            event = event_range(args.event_path, args.event_name)
            revision_range = event.revision_range
            print(f"large-files event={args.event_name} before={event.before} after={event.after}")
            print(f"large-files base={event.base} reason={event.reason}")
        paths = added_paths(revision_range)
        violations = [
            (Path(path).as_posix(), size)
            for path in paths
            if (size := blob_size(path, revision_range)) > MAX_BYTES
        ]
    except CheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if violations:
        print(f"New files larger than {format_size(MAX_BYTES)} are not allowed:")
        for path, size in violations:
            print(f"- {path}: {format_size(size)}")
        if event:
            print(f"large-files target_count={len(paths)} result=fail")
        return 1

    print(f"No newly added files exceed {format_size(MAX_BYTES)}.")
    if event:
        print(f"large-files target_count={len(paths)} result=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
