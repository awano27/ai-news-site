#!/usr/bin/env python3
"""Validate config/analytics.json measurement_id.

Exit 0 when the ID matches ^G-[A-Z0-9]{6,}$ and is not a placeholder
(REPLACE / XXXX). Otherwise print one line and exit 1.

    py -3 scripts/check_analytics_config.py
    py -3 scripts/check_analytics_config.py --allow-placeholder
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "analytics.json"
ID_RE = re.compile(r"^G-[A-Z0-9]{6,}$")
PLACEHOLDER_RE = re.compile(r"REPLACE|XXXX", re.I)


def classify_measurement_id(value: object) -> tuple[bool, str]:
    if not isinstance(value, str) or not value.strip():
        return False, "measurement_id missing"
    mid = value.strip()
    if not ID_RE.fullmatch(mid):
        return False, f"measurement_id {mid!r} does not match ^G-[A-Z0-9]{{6,}}$"
    if PLACEHOLDER_RE.search(mid):
        return False, f"measurement_id {mid!r} is a placeholder"
    return True, mid


def load_measurement_id(path: Path = CONFIG) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"{path.as_posix()} not found"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read analytics config: {exc}"
    if not isinstance(data, dict):
        return False, "analytics config is not an object"
    return classify_measurement_id(data.get("measurement_id"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--allow-placeholder",
        action="store_true",
        help="warn on placeholder / invalid ID but exit 0",
    )
    args = ap.parse_args(argv)
    ok, detail = load_measurement_id()
    if ok:
        print(f"[check_analytics_config] ok {detail}")
        return 0
    prefix = "warning" if args.allow_placeholder else "error"
    print(f"[check_analytics_config] {prefix}: {detail}", file=sys.stderr)
    return 0 if args.allow_placeholder else 1


if __name__ == "__main__":
    raise SystemExit(main())
