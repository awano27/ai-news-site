#!/usr/bin/env python3
"""Inject the GA4 analytics loader into every HTML page.

The loader itself (/assets/js/analytics.js) reads /config/analytics.json
at runtime, so we only need to drop a single <script defer> tag before
</head>. Idempotent via the ``<!-- GA4_INJECTED v1 -->`` marker.

Usage:
    python scripts/inject_analytics.py --dry-run
    python scripts/inject_analytics.py
    python scripts/inject_analytics.py --force
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "<!-- GA4_INJECTED v1 -->"
SNIPPET = (
    MARKER
    + '\n<script src="/assets/js/analytics.js" defer></script>\n'
)

DEFAULT_TARGETS = [
    ROOT / "index.html",
    ROOT / "about.html",
    ROOT / "contact.html",
    ROOT / "privacy-policy.html",
    ROOT / "presentations",
]

HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)
EXCLUDE_PATTERNS = (
    re.compile(r"og-image-generator", re.IGNORECASE),
    re.compile(r"^test_", re.IGNORECASE),
    re.compile(r"^tmp_", re.IGNORECASE),
)


def should_skip_path(p: Path) -> bool:
    return any(pat.search(p.name) for pat in EXCLUDE_PATTERNS)


def process_file(path: Path, force: bool, dry_run: bool) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "skip (non-utf8)"

    if MARKER in text and not force:
        return "skip (already injected)"

    if not HEAD_CLOSE_RE.search(text):
        return "skip (no </head>)"

    if force and MARKER in text:
        text = re.sub(
            rf"{re.escape(MARKER)}.*?</script>\s*",
            "",
            text,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )

    new_text = HEAD_CLOSE_RE.sub(SNIPPET + "</head>", text, count=1)

    if dry_run:
        return "would inject"

    path.write_text(new_text, encoding="utf-8")
    return "injected"


def iter_targets(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if not p.exists():
            continue
        if p.is_file() and p.suffix.lower() == ".html":
            if not should_skip_path(p):
                files.append(p)
        elif p.is_dir():
            files.extend(
                sorted(x for x in p.rglob("*.html") if not should_skip_path(x))
            )
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    targets = [Path(p) if Path(p).is_absolute() else (ROOT / p) for p in args.paths] if args.paths else DEFAULT_TARGETS
    files = iter_targets(targets)

    stats: dict[str, int] = {}
    for f in files:
        result = process_file(f, args.force, args.dry_run)
        key = "would inject" if result.startswith("would") else result
        stats[key] = stats.get(key, 0) + 1
    print(f"[inject_analytics] {sum(stats.values())} files: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
