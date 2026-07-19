#!/usr/bin/env python3
"""Reject newly added Git blobs larger than 5 MiB."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


MAX_BYTES = 5 * 1024 * 1024


def run_git(*args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except FileNotFoundError:
        raise SystemExit("error: git is not installed or not on PATH") from None
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"error: git {' '.join(args)} failed: {detail}") from None


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
            raise SystemExit("error: --range must use A..B Git revision syntax")
        target_revision = revision_range.rsplit("..", 1)[1]
        if not target_revision:
            raise SystemExit("error: --range must include the target revision B")
        object_name = f"{target_revision}:{path}"
    return int(run_git("cat-file", "-s", object_name).strip())


def format_size(size: int) -> str:
    return f"{size / (1024 * 1024):.2f} MiB"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--range", dest="revision_range", metavar="A..B")
    args = parser.parse_args()

    violations = [
        (Path(path).as_posix(), size)
        for path in added_paths(args.revision_range)
        if (size := blob_size(path, args.revision_range)) > MAX_BYTES
    ]
    if violations:
        print(f"New files larger than {format_size(MAX_BYTES)} are not allowed:")
        for path, size in violations:
            print(f"- {path}: {format_size(size)}")
        return 1

    print(f"No newly added files exceed {format_size(MAX_BYTES)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
