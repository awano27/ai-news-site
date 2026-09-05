from copy import deepcopy
import json

from scripts.render_claim_evidence import EvidencePage, render_static_page
from src.auto_collect.claim_evidence import claim_fingerprint


def page_fixture():
    sources = [{"id": "docs", "publisher": "Provider", "title": "Specification", "url": "https://example.com/spec", "published_at": None}]
    claim = {"id": "sandbox", "statement": "Bash と子プロセスを隔離。", "evidence_label": "Fact-A", "basis": "official_spec", "status": "matched", "conditions": ["対象OSで設定時のみ"], "as_of": None, "source_refs": [{"source_id": "docs", "section": "Scope", "supports": "Bash process scope"}]}
    claim["verification"] = {"checked_at": "2026-09-05", "method": "ai_document_review", "fingerprint": claim_fingerprint(claim, sources)}
    bundle = {"version": 1, "sources": sources, "claims": [claim]}
    return '<html><head><link rel="stylesheet" href="/assets/claim-evidence.css"></head><body><p data-claim-id="sandbox"><b>Bash</b> と子プロセスを隔離。</p><div data-evidence-for="sandbox"></div><script type="application/json" id="claim-evidence-data">' + json.dumps(bundle, ensure_ascii=False) + '</script></body></html>'


def test_static_slot_render_is_idempotent_and_does_not_create_reviews():
    before = page_fixture()
    rendered, errors = render_static_page(before)
    assert not errors
    assert rendered != before
    assert render_static_page(rendered) == (rendered, [])
    assert EvidencePage(before).bundle() == EvidencePage(rendered).bundle()


def test_body_edits_fail_even_when_embedded_json_looks_verified():
    before = page_fixture()
    changed = before.replace('<b>Bash</b> と子プロセスを隔離。', '<b>製品全体</b>を完全隔離。')
    rendered, errors = render_static_page(changed)
    assert rendered == changed
    assert any("body text differs" in e for e in errors)


def test_unregistered_references_and_missing_slots_fail():
    text = page_fixture().replace('data-evidence-for="sandbox"', 'data-evidence-for="wrong"')
    assert any("unregistered claim" in e for e in render_static_page(text)[1])


def test_duplicate_claim_ids_cannot_misassociate_a_review():
    text = page_fixture().replace('</body>', '<p data-claim-id="sandbox">別の説明。</p></body>')
    assert any("exactly one bound body" in e for e in render_static_page(text)[1])


def test_changed_conditions_fail_without_automatic_reseal():
    text = page_fixture().replace('対象OSで設定時のみ', '全OSで常に')
    assert any("fingerprint" in e for e in render_static_page(text)[1])


def test_correction_history_is_not_treated_as_a_current_assertion():
    text = page_fixture().replace('</body>', '<p>訂正履歴: 過去の「Claude Codeはサンドボックスなし」を訂正しました。</p></body>')
    assert not render_static_page(text)[1]
