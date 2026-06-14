#!/usr/bin/env python3
"""Shared Injector framework for inject_*.py scripts.

All boilerplate for argparse, HTML discovery, UTF-8 read/write,
idempotent marker blocks, and stats accumulation lives here.
Each inject_*.py only implements its unique build_block() logic.
"""
from __future__ import annotations

import argparse
import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

# Repo root (two levels above this file: scripts/inject/_framework.py)
ROOT: Path = Path(__file__).resolve().parents[2]

HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)


def strip_marker_block(text: str, marker: str, end_pattern: str = r"</script>") -> str:
    """Remove the first occurrence of the marker block from *text*.

    The block starts at *marker* and ends at the first match of *end_pattern*.
    Leading/trailing whitespace around the removed region is also consumed.
    """
    pat = re.compile(
        rf"{re.escape(marker)}.*?{end_pattern}\s*",
        re.DOTALL | re.IGNORECASE,
    )
    return pat.sub("", text, count=1)


def insert_before_head_close(text: str, block: str) -> str:
    """Insert *block* immediately before the first </head> tag."""
    return HEAD_CLOSE_RE.sub(block + "</head>", text, count=1)


def insert_after_body_anchor(
    text: str,
    block: str,
    anchor_re: re.Pattern,
    fallback_re: re.Pattern,
) -> str:
    """Insert *block* after the first match of *anchor_re*.

    Falls back to inserting after *fallback_re* (e.g. <body>) when the
    anchor is not found.  Returns *text* unchanged if neither matches.
    """
    m = anchor_re.search(text)
    if m:
        return text[: m.end()] + block + text[m.end():]
    fm = fallback_re.search(text)
    if fm:
        return text[: fm.end()] + block + text[fm.end():]
    return text


def iter_targets(
    paths: list[Path],
    exclusion_patterns: Sequence[re.Pattern] = (),
    recursive: bool = True,
) -> list[Path]:
    """Expand *paths* (files and/or dirs) to a deduplicated HTML file list.

    Directories are traversed with rglob (recursive=True) or glob (False).
    Files whose *name* matches any pattern in *exclusion_patterns* are skipped.
    """
    out: list[Path] = []
    for p in paths:
        if not p.exists():
            continue
        if p.is_file():
            if p.suffix.lower() == ".html" and not _excluded(p, exclusion_patterns):
                out.append(p)
        elif p.is_dir():
            globber = p.rglob("*.html") if recursive else p.glob("*.html")
            out.extend(
                sorted(x for x in globber if not _excluded(x, exclusion_patterns))
            )
    return out


def _excluded(path: Path, patterns: Sequence[re.Pattern]) -> bool:
    return any(pat.search(path.name) for pat in patterns)


class Injector(ABC):
    """Base class for all inject_*.py scripts.

    Subclasses must set MARKER and implement build_block().
    Override insertion_point() or run() for non-standard behaviour.
    """

    MARKER: str  # e.g. '<!-- ADSENSE_INJECTED v1 -->'
    DESCRIPTION: str = ""
    TAG: str = ""                          # log prefix, e.g. 'inject_analytics'
    DEFAULT_TARGETS: list[Path] = []
    EXCLUSION_PATTERNS: Sequence[re.Pattern] = ()
    RECURSIVE: bool = True
    END_PATTERN: str = r"</script>"

    @abstractmethod
    def build_block(self, path: Path, text: str) -> str | None:
        """Return the HTML block to inject, or None to skip this file."""
        ...

    def insertion_point(self, text: str, block: str) -> str:
        """Default: insert immediately before </head>."""
        return insert_before_head_close(text, block)

    def process_file(self, path: Path, force: bool, dry_run: bool) -> str:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return "skip (non-utf8)"

        if self.MARKER in text and not force:
            return "skip (already injected)"

        if not HEAD_CLOSE_RE.search(text):
            return "skip (no </head>)"

        if force and self.MARKER in text:
            text = strip_marker_block(text, self.MARKER, self.END_PATTERN)

        block = self.build_block(path, text)
        if block is None:
            return "skip (no payload)"

        new_text = self.insertion_point(text, block)
        if new_text == text:
            return "skip (no insertion point)"

        if dry_run:
            return f"would inject ({len(block)} bytes)"

        path.write_text(new_text, encoding="utf-8")
        return "injected"

    def _parse_args(self, argv: list[str] | None = None, *, extra_args: bool = False):
        """Parse standard --dry-run/--force/paths args. Returns argparse.Namespace."""
        ap = argparse.ArgumentParser(description=self.DESCRIPTION)
        if not extra_args:
            ap.add_argument("paths", nargs="*")
        ap.add_argument("--dry-run", action="store_true")
        ap.add_argument("--force", action="store_true")
        return ap.parse_args(argv)

    def run(self, argv: list[str] | None = None) -> int:
        args = self._parse_args(argv)

        raw = args.paths
        targets = (
            [Path(p) if Path(p).is_absolute() else (ROOT / p) for p in raw]
            if raw
            else self.DEFAULT_TARGETS
        )
        files = iter_targets(targets, self.EXCLUSION_PATTERNS, self.RECURSIVE)

        stats: dict[str, int] = {}
        for f in files:
            result = self.process_file(f, args.force, args.dry_run)
            key = "would inject" if result.startswith("would") else result
            stats[key] = stats.get(key, 0) + 1
        tag = self.TAG or type(self).__name__.lower().replace("injector", "")
        print(f"[{tag}] {sum(stats.values())} files: {stats}")
        return 0
