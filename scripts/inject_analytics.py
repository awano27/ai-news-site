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

import re
import sys
from pathlib import Path

from inject._framework import ROOT, Injector
from public_html import public_html_files, exclusion_reason

SNIPPET = (
    "<!-- GA4_INJECTED v1 -->"
    + '\n<script src="/assets/js/analytics.js" defer></script>\n'
)


class AnalyticsInjector(Injector):
    MARKER = "<!-- GA4_INJECTED v1 -->"
    DESCRIPTION = "Inject GA4 analytics loader into every HTML page."
    TAG = "inject_analytics"
    DEFAULT_TARGETS = public_html_files(ROOT)
    EXCLUSION_PATTERNS = (
        re.compile(r"og-image-generator", re.IGNORECASE),
        re.compile(r"^test_", re.IGNORECASE),
        re.compile(r"^tmp_", re.IGNORECASE),
        re.compile(r"_bak|\.bak", re.IGNORECASE),
    )

    def build_block(self, path: Path, text: str) -> str | None:
        if exclusion_reason(path, text):
            return None
        return SNIPPET


def main() -> int:
    return AnalyticsInjector().run()


if __name__ == "__main__":
    sys.exit(main())
