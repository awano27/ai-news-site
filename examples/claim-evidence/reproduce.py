#!/usr/bin/env python3
"""Run offline claim-evidence reproduction checks against the pinned source tree.

This runner deliberately imports the production validator, renderer, and static
HTML checker. It never fetches example.com and never recalculates a review seal.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable


SAMPLE_DIR = Path(__file__).resolve().parent
ROOT = SAMPLE_DIR.parents[1]
FIXTURE_PATH = SAMPLE_DIR / "fixtures.json"


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def fresh_bundle(fixture: dict[str, Any], key: str = "bundle") -> dict[str, Any]:
    """Return an isolated copy; mutation checks must not leak into another case."""
    return deepcopy(fixture[key])


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_rejected(bundle: dict[str, Any], expected: str) -> None:
    errors = validate_bundle(bundle)
    require(any(expected in error for error in errors), f"expected {expected!r}, got {errors!r}")
    require("資料との照合済み" not in render_evidence(bundle), "invalid record was displayed as matched")


def static_document(fixture: dict[str, Any], bundle: dict[str, Any]) -> str:
    # The literal bundle is embedded for the existing static-page checker. Escaping
    # '<' matches the contract for JSON inside a script element; it does not seal data.
    embedded = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return fixture["static_html_template"].replace("__BUNDLE_JSON__", embedded)


def check_pinned_core(fixture: dict[str, Any]) -> None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True
    )
    require(completed.stdout.strip() == fixture["pinned_sha"], "checkout HEAD is not the documented pinned SHA")
    for relative, expected in fixture["core_file_sha256_lf"].items():
        content = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha256(content).hexdigest()
        require(actual == expected, f"pinned LF-normalized core checksum differs: {relative}")


def load_production_modules() -> None:
    """Import production code only after its pinned source has passed the gate."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    global check_static_page, render_static_page, render_evidence, validate_bundle
    import scripts.render_claim_evidence as static_module
    import src.auto_collect.claim_evidence as evidence_module
    require(Path(static_module.__file__).resolve() == (ROOT / "scripts/render_claim_evidence.py").resolve(), "unexpected static module import path")
    require(Path(evidence_module.__file__).resolve() == (ROOT / "src/auto_collect/claim_evidence.py").resolve(), "unexpected evidence module import path")
    check_static_page, render_static_page = static_module.check_static_page, static_module.render_static_page
    render_evidence, validate_bundle = evidence_module.render_evidence, evidence_module.validate_bundle


def check_valid_record(fixture: dict[str, Any]) -> None:
    bundle = fresh_bundle(fixture)
    require(validate_bundle(bundle, fixture["subject"]) == [], "valid fixture was rejected")
    rendered = render_evidence(bundle, subject=fixture["subject"])
    require("ベンダー公称値" in rendered and "資料との照合済み" in rendered, "expected display labels are absent")


def check_statement_change_rejected(fixture: dict[str, Any]) -> None:
    bundle = fresh_bundle(fixture)
    bundle["claims"][0]["statement"] = "架空ベンダーは達成率99.9%と公表した。"
    require_rejected(bundle, "fingerprint")


def check_conditions_change_rejected(fixture: dict[str, Any]) -> None:
    bundle = fresh_bundle(fixture)
    bundle["claims"][0]["conditions"] = ["全環境で常に有効"]
    require_rejected(bundle, "fingerprint")


def check_missing_source_rejected(fixture: dict[str, Any]) -> None:
    bundle = fresh_bundle(fixture)
    bundle["claims"][0]["source_refs"][0]["source_id"] = "missing-source"
    require_rejected(bundle, "missing referenced source")


def check_source_record_change_rejected(fixture: dict[str, Any]) -> None:
    bundle = fresh_bundle(fixture)
    bundle["sources"][0]["title"] = "別の架空資料"
    require_rejected(bundle, "fingerprint")


def check_legacy_records_have_no_badge(_: dict[str, Any]) -> None:
    for legacy in (None, {}):
        require(validate_bundle(legacy) == [], "legacy metadata should remain optional")
        require(render_evidence(legacy) == "", "legacy metadata unexpectedly rendered a badge")


def check_provenance_is_not_upgraded(fixture: dict[str, Any]) -> None:
    rendered = render_evidence(fresh_bundle(fixture), subject=fixture["subject"])
    require("ベンダー公称値" in rendered and "AIによる資料照合" in rendered, "recorded provenance is absent")
    require("第三者の測定" not in rendered and "人による資料照合" not in rendered, "provenance was upgraded")


def check_review_metadata_is_not_authenticated(fixture: dict[str, Any]) -> None:
    """A valid review label is recorded metadata, not reviewer authentication."""
    bundle = fresh_bundle(fixture)
    verification = bundle["claims"][0]["verification"]
    verification["checked_at"] = "2026-09-06"
    verification["method"] = "human_document_review"
    require(validate_bundle(bundle, fixture["subject"]) == [], "valid changed review metadata was rejected")
    rendered = render_evidence(bundle, subject=fixture["subject"])
    require("照合 <time datetime=\"2026-09-06\">2026-09-06</time>" in rendered, "changed date was not rendered")
    require("人による資料照合" in rendered and "AIによる資料照合" not in rendered, "changed method was not rendered")


def check_static_regeneration_is_identical(fixture: dict[str, Any]) -> None:
    bundle = fresh_bundle(fixture)
    before = json.dumps(bundle, ensure_ascii=False, sort_keys=True)
    rendered_once, errors_once = render_static_page(static_document(fixture, bundle))
    require(errors_once == [], f"initial static render failed: {errors_once!r}")
    rendered_twice, errors_twice = render_static_page(rendered_once)
    require(errors_twice == [], f"second static render failed: {errors_twice!r}")
    require(rendered_once == rendered_twice, "identical inputs produced different static output")
    require(before == json.dumps(bundle, ensure_ascii=False, sort_keys=True), "render changed recorded dates or sources")
    with tempfile.TemporaryDirectory() as directory:
        page = Path(directory) / "reproduced.html"
        page.write_text(rendered_once, encoding="utf-8")
        require(check_static_page(page) == [], "existing static checker considers regenerated page stale")


def check_implausible_claim_is_not_truth_checked(fixture: dict[str, Any]) -> None:
    bundle = fresh_bundle(fixture, "implausible_bundle")
    require(validate_bundle(bundle) == [], "structurally valid fictional claim was rejected")
    require("月面の全利用者" in render_evidence(bundle), "fictional assertion was not rendered")


def check_subject_and_body_changes_rejected(fixture: dict[str, Any]) -> None:
    bundle = fresh_bundle(fixture)
    changed_subject = deepcopy(fixture["subject"])
    changed_subject["summary"] = "別の架空本文です。"
    errors = validate_bundle(bundle, changed_subject)
    require(any("article text differs" in error for error in errors), f"expected subject mismatch, got {errors!r}")
    require("資料との照合済み" not in render_evidence(bundle, subject=changed_subject), "changed subject kept matched display")
    changed_body = static_document(fixture, fresh_bundle(fixture)).replace(
        "架空ベンダーは固定条件で達成率72.6%と公表した。", "架空ベンダーは全環境で達成率100%と公表した。", 1
    )
    _, body_errors = render_static_page(changed_body)
    require(any("body text differs" in error for error in body_errors), f"expected body mismatch, got {body_errors!r}")


CHECKS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("02 valid_record", check_valid_record),
    ("03 statement_change_rejected", check_statement_change_rejected),
    ("04 conditions_change_rejected", check_conditions_change_rejected),
    ("05 missing_source_rejected", check_missing_source_rejected),
    ("06 source_record_change_rejected", check_source_record_change_rejected),
    ("07 legacy_without_badge", check_legacy_records_have_no_badge),
    ("08 provenance_not_upgraded", check_provenance_is_not_upgraded),
    ("09 review_metadata_not_authenticated", check_review_metadata_is_not_authenticated),
    ("10 static_regeneration_identical", check_static_regeneration_is_identical),
    ("11 implausible_claim_not_truth_checked", check_implausible_claim_is_not_truth_checked),
    ("12 subject_and_body_changes_rejected", check_subject_and_body_changes_rejected),
)


def main() -> int:
    fixture = load_fixture()
    total = len(CHECKS) + 1
    try:
        check_pinned_core(fixture)
    except (AssertionError, OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL 01 pinned_core: {exc}")
        print(f"RESULT unexpected failures: 1/{total}")
        return 1
    print("PASS 01 pinned_core")
    try:
        load_production_modules()
    except (AssertionError, ImportError, OSError) as exc:
        print(f"FAIL production_import: {exc}")
        print(f"RESULT unexpected failures: 1/{total}")
        return 1
    failures = 0
    for name, check in CHECKS:
        try:
            check(fixture)
        except (AssertionError, OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
            failures += 1
            print(f"FAIL {name}: {exc}")
        else:
            print(f"PASS {name}")
    if failures:
        print(f"RESULT unexpected failures: {failures}/{total}")
        return 1
    print(f"RESULT {total}/{total} checks passed; expected rejections were observed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
