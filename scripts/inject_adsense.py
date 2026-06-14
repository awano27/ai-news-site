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

import json
import re
import sys
from pathlib import Path

from inject._framework import ROOT, Injector

CONFIG = ROOT / "config" / "adsense.json"

DEFAULT_TARGETS = [
    ROOT / "index.html",
    ROOT / "about.html",
    ROOT / "contact.html",
    ROOT / "privacy-policy.html",
    ROOT / "presentations",
]


def load_publisher_id() -> str | None:
    if not CONFIG.exists():
        print(
            f"[adsense] {CONFIG.relative_to(ROOT)} missing — create it after AdSense approval",
            file=sys.stderr,
        )
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


class AdsenseInjector(Injector):
    MARKER = "<!-- ADSENSE_INJECTED v1 -->"
    DESCRIPTION = "Inject Google AdSense snippet site-wide."
    TAG = "adsense"
    DEFAULT_TARGETS = DEFAULT_TARGETS
    END_PATTERN = r"</script>"

    def __init__(self, pub: str) -> None:
        self._pub = pub

    def build_block(self, path: Path, text: str) -> str | None:
        return (
            f"{self.MARKER}\n"
            f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={self._pub}"'
            f' crossorigin="anonymous"></script>\n'
        )


def main() -> int:
    pub = load_publisher_id()
    if not pub:
        return 1
    return AdsenseInjector(pub).run()


if __name__ == "__main__":
    sys.exit(main())
