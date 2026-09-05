"""Contract checks for the audited evidence embedded in the 2026-09-04 slide."""

from __future__ import annotations

import json
from pathlib import Path
import re

from scripts.render_claim_evidence import render_static_page


ROOT = Path(__file__).resolve().parents[1]
SLIDE = ROOT / "presentations" / "day_slides" / "day_slide_2026_09_04.html"
AUDIT_IDS = {
    *(f"S06-{number:02d}" for number in range(1, 20)),
    *(f"S07-{number:02d}" for number in range(1, 17)),
    *(f"S08-{number:02d}" for number in range(1, 13)),
}


def load_slide() -> tuple[str, dict]:
    html = SLIDE.read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="claim-evidence-data">\s*(.*?)\s*</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return html, json.loads(match.group(1))


def test_slide_embeds_the_full_audited_claim_bundle_and_slots() -> None:
    html, bundle = load_slide()

    assert 'href="/assets/claim-evidence.css"' in html
    assert '<details class="claim-ledger"' not in html
    assert "手元朝稿" not in html
    assert "一次URLは4本とも取得できた" not in html
    assert 'href="#evidence-S07-01"' in html
    assert 'href="#evidence-S08-09"' in html
    assert "Help Centerは提供元の公式資料" in html
    assert bundle["version"] == 1
    claims = {claim["id"]: claim for claim in bundle["claims"]}
    assert set(claims) == AUDIT_IDS

    for claim_id in claims:
        assert f'data-claim-id="{claim_id}"' in html, claim_id
        assert f'data-evidence-for="{claim_id}"' in html, claim_id


def test_historical_pricing_and_help_center_claims_are_not_marked_matched() -> None:
    _, bundle = load_slide()
    claims = {claim["id"]: claim for claim in bundle["claims"]}
    source_dates = {source["id"]: source["published_at"] for source in bundle["sources"]}

    for claim_id in {"S07-01", "S07-02", "S07-06", "S07-07", "S08-08"}:
        assert claims[claim_id]["status"] in {"partial", "unverified"}
        assert (
            "2026-09-05" in " ".join(claims[claim_id]["conditions"])
            or "2026-09-05" in {
                source_dates[ref["source_id"]] for ref in claims[claim_id]["source_refs"]
            }
        )


def test_editorial_routes_do_not_claim_measurement_status() -> None:
    _, bundle = load_slide()
    claims = {claim["id"]: claim for claim in bundle["claims"]}

    for claim_id in {"S06-03", "S06-18", "S07-08", "S07-13", "S08-01", "S08-02", "S08-03", "S08-04", "S08-05", "S08-07", "S08-10", "S08-12"}:
        assert claims[claim_id]["basis"] == "editorial"
        assert claims[claim_id]["status"] in {"partial", "unverified"}


def test_visible_pricing_cost_and_model_values_are_bound_to_reviewed_claims() -> None:
    """Changing a reader-facing value must fail the static evidence checker."""
    html, _ = load_slide()
    mutations = {
        "S07-02": ("2×", "3×"),
        "S07-04": ("75%高", "76%高"),
        "S08-09": ("1.05M", "1.06M"),
    }

    for claim_id, (old, new) in mutations.items():
        pattern = rf'(<span data-claim-id="{claim_id}">)(.*?)(</span>)'
        match = re.search(pattern, html, re.DOTALL)
        assert match is not None
        assert old in match.group(2)
        mutated = html[: match.start(2)] + match.group(2).replace(old, new, 1) + html[match.end(2) :]
        _, errors = render_static_page(mutated)
        assert f"{claim_id}: body text differs from reviewed statement" in errors
