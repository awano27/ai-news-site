#!/usr/bin/env python3
"""Detect day-slides stranded on unmerged remote branches.

Why this exists
---------------
Claude Code cloud/web sessions push their work to ``claude/*`` branches, not to
``main``. If such a session creates a day-slide and the branch is never merged,
the slide silently never reaches visionhub.jp (2026-06-30 and 2026-07-02 were
lost this way and only noticed on 2026-07-12).

This script lists every ``origin/claude/*`` branch that contains a
``presentations/day_slides/day_slide_YYYY_MM_DD.html`` file absent from
``origin/main``. Exit 1 when any orphan is found so CI turns red.

Files with extra suffixes (e.g. ``day_slide_2025_10_26_backup.html``) are
ignored — only the strict daily-slide pattern counts.

Usage:
    git fetch origin '+refs/heads/claude/*:refs/remotes/origin/claude/*'
    python scripts/check_orphaned_slide_branches.py
"""
from __future__ import annotations

import re
import subprocess
import sys

SLIDE_RE = re.compile(r"presentations/day_slides/day_slide_\d{4}_\d{2}_\d{2}\.html$")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def _slides(ref: str) -> set[str]:
    try:
        out = _git("ls-tree", "-r", "--name-only", ref, "--", "presentations/day_slides")
    except subprocess.CalledProcessError:
        return set()
    return {line for line in out.splitlines() if SLIDE_RE.search(line)}


def main() -> int:
    main_slides = _slides("origin/main")
    if not main_slides:
        print("[orphan-check] could not read origin/main slide list — is origin fetched?")
        return 1

    branches = [
        b.strip()
        for b in _git("branch", "-r", "--format=%(refname:short)").splitlines()
        if b.strip().startswith("origin/claude/")
    ]
    orphans: dict[str, list[str]] = {}
    for branch in branches:
        extra = sorted(_slides(branch) - main_slides)
        if extra:
            orphans[branch] = extra

    if not orphans:
        print(f"[orphan-check] OK — {len(branches)} claude/* branches, "
              "no day-slide missing from origin/main.")
        return 0

    print("[orphan-check] FAIL — day-slides exist on unmerged branches but NOT on origin/main:")
    for branch, files in sorted(orphans.items()):
        for f in files:
            print(f"  {branch} : {f}")
    print("\nRecovery: git checkout <branch> -- <file>, add the entry to "
          "presentations/day_slides_index.html, re-run scripts/inject_slide_nav.py, "
          "scripts/update_home_fallback.py and scripts/build_sitemap.py, then push to main. "
          "Delete the branch once merged.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
