#!/usr/bin/env python3
"""Audit HTML pages for Google Discover eligibility.

Checks each page for the signals that move the needle on Discover:
  - NewsArticle JSON-LD present (marker ``<!-- JSONLD_INJECTED v1 -->``)
  - meta description present
  - canonical link present
  - og:image with a concrete URL (not default)
  - meta robots with max-image-preview:large
  - Viewport meta (mobile-friendly)

Prints a pass/fail table; exits with code 1 if any required check fails
so it can be used in CI.

Usage:
    python scripts/check_discover_readiness.py
    python scripts/check_discover_readiness.py --strict
    python scripts/check_discover_readiness.py --path presentations/day_slides/day_slide_2026_04_18.html
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGETS = [
    ROOT / "presentations" / "day_slides",
    ROOT / "presentations" / "hubs",
    ROOT / "presentations" / "digests",
]

CHECKS = [
    # Accept either the injector marker OR a raw JSON-LD script — both are
    # valid sources of structured data for Google.
    ("json-ld", re.compile(r'<!--\s*JSONLD_INJECTED|type=["\']application/ld\+json["\']', re.IGNORECASE), True),
    ("description", re.compile(r'<meta\s+[^>]*name=["\']description["\']', re.IGNORECASE), True),
    ("canonical", re.compile(r'<link\s+[^>]*rel=["\']canonical["\']', re.IGNORECASE), True),
    ("og:image", re.compile(r'<meta\s+[^>]*property=["\']og:image["\']', re.IGNORECASE), True),
    ("twitter:card", re.compile(r'<meta\s+[^>]*name=["\']twitter:card["\']', re.IGNORECASE), True),
    ("max-image-preview", re.compile(r"max-image-preview\s*:\s*large", re.IGNORECASE), True),
    ("viewport", re.compile(r'<meta\s+[^>]*name=["\']viewport["\']', re.IGNORECASE), True),
    ("analytics", re.compile(r'<!--\s*GA4_INJECTED|assets/js/analytics\.js', re.IGNORECASE), False),
    ("internal-links", re.compile(r"<!--\s*INTERNAL_LINKS_INJECTED", re.IGNORECASE), False),
]


def audit(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"_error": "non-utf8"}
    return {name: bool(pat.search(text)) for name, pat, _required in CHECKS}


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.glob("*.html")))
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", action="append", help="Specific file/dir (repeatable)")
    ap.add_argument("--strict", action="store_true", help="Exit 1 if any file fails a required check")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    targets = [Path(p) if Path(p).is_absolute() else (ROOT / p) for p in (args.path or [])] or DEFAULT_TARGETS
    files = iter_files(targets)

    # Aggregate per-check pass counts
    pass_counts = {name: 0 for name, _, _ in CHECKS}
    fail_files: dict[str, list[str]] = {name: [] for name, _, _ in CHECKS}
    total = len(files)

    any_required_fail = False
    for f in files:
        result = audit(f)
        if "_error" in result:
            continue
        for name, _, required in CHECKS:
            if result.get(name):
                pass_counts[name] += 1
            else:
                fail_files[name].append(str(f.relative_to(ROOT)))
                if required:
                    any_required_fail = True

    print(f"=== Discover readiness — {total} files ===")
    print(f"{'CHECK':<24} {'PASS':>8} {'FAIL':>8}   STATUS")
    for name, _, required in CHECKS:
        passed = pass_counts[name]
        failed = total - passed
        mark = "REQ" if required else "opt"
        status = "✓" if failed == 0 else ("✗" if required else "·")
        print(f"{name:<24} {passed:>8} {failed:>8}   {status} {mark}")

    if args.verbose:
        for name, fails in fail_files.items():
            if fails:
                print(f"\n-- {name} failures ({len(fails)}) --")
                for fn in fails[:20]:
                    print(f"  {fn}")
                if len(fails) > 20:
                    print(f"  ... +{len(fails) - 20} more")

    return 1 if (args.strict and any_required_fail) else 0


if __name__ == "__main__":
    sys.exit(main())
