#!/usr/bin/env python3
"""Offline checks for the explicitly migrated claim-evidence surfaces only.

Missing metadata in unrelated legacy articles is allowed. This checks structure,
body/review bindings and derivative consistency, never source truth or freshness.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.render_claim_evidence import DEFAULT_PAGES, check_static_page
from src.auto_collect.claim_evidence import normalized_text, render_evidence, validate_bundle
from src.auto_collect.content_integrity import CRUSOE_2026_09_05_URL, apply_article_correction, canonical_url


NEWS_JSON = (
    "daily-news/data.json",
    "presentations/auto_daily_report.json",
    "public-pages/api/auto_daily_report/latest.json",
)
NEWS_HTML = (
    "daily-news/index.html",
    "daily-news/archive/2026-09-05.html",
    "presentations/auto_daily_report.html",
    "presentations/daily_reports/auto_daily_report_2026_09_05.html",
)
FIXED_HTML = {"daily-news/archive/2026-09-05.html", "presentations/daily_reports/auto_daily_report_2026_09_05.html"}


def article_records(value):
    if isinstance(value, dict):
        if (canonical_url(value.get("url", "")) == CRUSOE_2026_09_05_URL
                and any(field in value for field in ("summary", "tldr", "type", "evidence_label"))):
            yield value
        else:
            for child in value.values():
                yield from article_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from article_records(child)


def compare_article_evidence(record: dict, expected: dict) -> list[str]:
    actual = record.get("claim_evidence")
    if not actual:
        return ["migrated article is missing claim_evidence"]
    errors = validate_bundle(actual, record)
    if actual != expected:
        errors.append("claim classification, sources or review data differ from the canonical article")
    return errors


def compare_homepage_evidence(record: dict, expected: dict, subject: dict | None = None) -> list[str]:
    """Homepage blurb is a projection; preserve the reviewed full article bundle."""
    errors = validate_bundle(record.get("claim_evidence"))
    if record.get("claim_evidence") != expected:
        errors.append("homepage projection differs from the canonical article evidence")
    expected_link = "presentations/daily_reports/auto_daily_report_2026_09_05.html#evidence-" + expected["claims"][0]["id"]
    if record.get("evidence_url") != expected_link:
        errors.append("homepage projection must link to the dated claim detail")
    if subject is not None:
        if record.get("title") != subject.get("title") or record.get("blurb") != normalized_text(subject.get("tldr") or subject.get("summary"))[:200]:
            errors.append("homepage wording differs from the reviewed article projection")
    return errors


def check_news(root: Path) -> list[str]:
    canonical = apply_article_correction({"url": CRUSOE_2026_09_05_URL})
    expected = canonical.get("claim_evidence")
    if not expected:
        return ["canonical Crusoe correction has no migrated evidence records"]
    errors = [f"canonical Crusoe: {error}" for error in validate_bundle(expected, canonical)]
    for relative in NEWS_JSON:
        path = root / relative
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        for record in article_records(data):
            errors.extend(f"{relative}: {error}" for error in compare_article_evidence(record, expected))
    try:
        homepage = json.loads((root / "news/latest.json").read_text(encoding="utf-8"))
        for records in homepage.get("sections", {}).values():
            for record in records:
                if canonical_url(record.get("source", {}).get("url", "")) == CRUSOE_2026_09_05_URL:
                    errors.extend(f"news/latest.json: {error}" for error in compare_homepage_evidence(record, expected, canonical))
    except (OSError, ValueError) as exc:
        errors.append(f"news/latest.json: {exc}")
    for relative in NEWS_HTML:
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        # Rolling lists may no longer include this historical article. Fixed
        # archives are always checked and cannot pass by silently dropping it.
        if CRUSOE_2026_09_05_URL not in text:
            if relative in FIXED_HTML:
                errors.append(f"{relative}: fixed historical article missing")
            continue
        for claim in expected["claims"]:
            rendered = render_evidence(expected, [claim["id"]], canonical)
            if rendered not in text:
                errors.append(f"{relative}: stale/missing evidence display for {claim['id']}")
        if '/assets/claim-evidence.css' not in text:
            errors.append(f"{relative}: missing shared evidence stylesheet")
        match = re.search(r'<script\b[^>]*id="report-data"[^>]*>(.*?)</script>', text, re.S)
        if match:
            try:
                data = json.loads(match.group(1))
                for record in article_records(data):
                    errors.extend(f"{relative} embedded JSON: {error}" for error in compare_article_evidence(record, expected))
            except ValueError as exc:
                errors.append(f"{relative}: invalid report-data JSON: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = []
    for relative in DEFAULT_PAGES:
        try:
            errors.extend(f"{relative}: {e}" for e in check_static_page(args.root / relative))
        except (OSError, ValueError) as exc:
            errors.append(f"{relative}: {exc}")
    errors.extend(check_news(args.root))
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("PASS: migrated claim bindings, source records, review dates and derivatives are consistent.")
    print(f"Scope: {len(DEFAULT_PAGES)} registered static pages and the fixed Crusoe article; no source fetch or site-wide truth guarantee.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
