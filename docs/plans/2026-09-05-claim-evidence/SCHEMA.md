# Shared claim evidence contract

One optional `claim_evidence` object extends existing article records; static HTML embeds this exact object in `<script type="application/json" id="claim-evidence-data">`. Existing `evidence_label`, `source_attribution`, correction text, numerical data and all old JSON fields retain their meaning. This is not a second confidence rating.

```json
{
  "version": 1,
  "sources": [{"id":"source-id","publisher":"Publisher","title":"Document title","url":"https://example.com/direct-document","published_at":null}],
  "claims": [{
    "id":"stable-claim-id",
    "label":"Short reader-facing subject",
    "statement":"The exact text under review",
    "evidence_label":"Claim",
    "basis":"reporting",
    "status":"matched",
    "source_refs":[{"source_id":"source-id","section":"Lead paragraph","supports":"What this passage supports"}],
    "conditions":["Environment, scope and limits"],
    "as_of":"2026-09-03",
    "uncertainty":"Secondary attribution or other limits, shown without opening details",
    "verification":{"checked_at":"2026-09-05","method":"ai_document_review","fingerprint":"literal reviewed fingerprint","note":"What was actually read; human review record not supplied"}
  }],
  "subject_fingerprint":"optional literal fingerprint of the article title/tldr/summary"
}
```

`basis`: `official_spec` (official specification/announcement), `vendor_claim`, `independent_measurement`, `reporting`, `operator_measurement`, `editorial`.
`status`: `matched`, `partial`, `unverified`, `conflict`.
`evidence_label`: existing Fact/Fact-A/Fact-B/Fact-C/Claim/Opinion/Forecast/Opinion / Forecast/Rumor/Curated or empty. No mapping from an official URL to verified status or to independent measurement.

`verification` may be null. Its `checked_at` is an actual strict YYYY-MM-DD date or null; never filled from a build clock. `method`: `ai_document_review`, `human_document_review`, `operator_test` (requires actual evidence). No human identity inferred. `matched`, `partial`, and `conflict` require source references, supports/section, valid date/method/fingerprint. Unverified without sources is valid and rendered honestly. Missing metadata on legacy records is valid.

Fingerprint `claim_fingerprint(claim, sources)` covers statement, evidence_label, basis, conditions, as_of, uncertainty, measurement, source references and corresponding source records. Do not recompute it during normal rendering/builds. An author records it only after the stated review. `article_fingerprint(item)` covers normalized title/tldr/summary. For curated article metadata, store a literal subject fingerprint too. Edited subjects/claims are validation errors; rendering downgrades invalid records to unverified with a visible warning.

Operator measurement requires a `measurement` object with nonempty `environment`, `method`, `results_url` (safe HTTP(S)); its content is also covered by the fingerprint.

Python API in `src/auto_collect/claim_evidence.py` (primary owner):

- `claim_fingerprint(claim, sources)` -> hex digest; sources is the source list.
- `article_fingerprint(item)` -> hex digest.
- `validate_bundle(bundle, subject=None)` -> list[str]; None/{} legacy -> no errors.
- `render_evidence(bundle, claim_ids=None, subject=None)` -> safe HTML; missing -> empty; invalid -> unverified (never a false match).
- `require_valid_evidence(bundle, subject=None)` -> raises ValueError on errors; absent -> no-op.

Static helper `scripts/render_claim_evidence.py` verifies and renders only evidence slots in existing pages (not a whole-page generator). Each claim's statement appears in exactly one existing HTML element with `data-claim-id="..."`. A nearby `<div data-evidence-for="...">...</div>` is replaced with shared rendered metadata. The helper checks normalized visible text against `statement` and its fingerprint before writing. Include `/assets/claim-evidence.css`. Embedded JSON must escape `<` as `\u003c` to prevent script end-tag injection. No new runtime fetch, tracking or JS dependency.

News integrations (worker owner) preserve the bundle through existing correction/formatter/parser/renderer/data paths, validate explicit metadata, put a compact shared block beside the target claim, and include the same stylesheet. Registered Crusoe metadata lives with the existing URL-specific correction rather than a parallel external source catalog. Unrelated legacy items remain untouched.

Explicit article metadata passed with a subject must include subject_fingerprint. Missing legacy bundles remain valid. Static pages instead bind each actual body element to the statement. Validation never refreshes a seal.

Homepage JSON keeps the canonical article bundle and a dated evidence_url. Its preflight also compares the homepage title/blurb against the reviewed article projection, so changing displayed wording cannot silently reuse the old review. No homepage ranking or layout changes were made.
