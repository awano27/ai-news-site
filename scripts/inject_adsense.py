#!/usr/bin/env python3
"""Inject the Google AdSense snippet site-wide.

Reads the publisher ID from ``config/adsense.json`` (created by the
operator after AdSense approval) and emits a single ``<script async>``
tag before ``</head>`` on every HTML page. Idempotent via
``<!-- ADSENSE_INJECTED v1 -->`` marker.

Do not run this until AdSense has approved the site — inserting the
snippet on an unapproved site causes console errors.

Usage:
    python scripts/inject_adsense.py --dry-run
    python scripts/inject_adsense.py
    python scripts/inject_adsense.py --force
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "adsense.json"
MARKER = "<!-- ADSENSE_INJECTED v1 -->"

HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)
DEFAULT_TARGETS = [
    ROOT / "index.html",
    ROOT / "about.html",
    ROOT / "contact.html",
    ROOT / "privacy-policy.html",
    ROOT / "presentations",
]


def load_publisher_id() -> str | None:
    if not CONFIG.exists():
        print(f"[adsense] {CONFIG.relative_to(ROOT)} missing — create it after AdSense approval", file=sys.stderr)
        return None
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("[adsense] config is not valid JSON", file=sys.stderr)
        return None
    pub = cfg.get("publisher_id") or ""
    if not re.fullmatch(r"ca-pub-\d{16}", pub):
        print(f"[adsense] publisher_id looks invalid: {pub!r}", file=sys.stderr)
        return None
    return pub


def snippet(pub: str) -> str:
    return (
        f"{MARKER}\n"
        f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={pub}"'
        f' crossorigin="anonymous"></script>\n'
    )


def process_file(path: Path, block: str, force: bool, dry_run: bool) -> str:
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

    new = HEAD_CLOSE_RE.sub(block + "</head>", text, count=1)
    if dry_run:
        return "would inject"
    path.write_text(new, encoding="utf-8")
    return "injected"


def iter_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_file() and p.suffix.lower() == ".html":
            out.append(p)
        elif p.is_dir():
            out.extend(sorted(x for x in p.rglob("*.html") if "test_" not in x.name and "tmp_" not in x.name))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    pub = load_publisher_id()
    if not pub:
        return 1

    block = snippet(pub)
    targets = [Path(p) if Path(p).is_absolute() else (ROOT / p) for p in args.paths] if args.paths else DEFAULT_TARGETS
    files = iter_files(targets)

    stats: dict[str, int] = {}
    for f in files:
        r = process_file(f, block, args.force, args.dry_run)
        k = "would inject" if r.startswith("would") else r
        stats[k] = stats.get(k, 0) + 1
    print(f"[adsense] {sum(stats.values())} files: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
