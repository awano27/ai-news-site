"""Claim/source records shared by static pages and the existing news pipeline.

This validates recorded structure and consistency, not truth or source meaning.
Fingerprints are recorded by an author after review, never refreshed by a build.
Old articles without this optional extension retain their existing behavior.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import date
from typing import Any
from urllib.parse import urlsplit


BASIS_LABELS = {
    "official_spec": "公式仕様・公式発表",
    "vendor_claim": "ベンダー公称値",
    "independent_measurement": "第三者の測定",
    "reporting": "報道",
    "operator_measurement": "運営者による実測",
    "editorial": "編集者の見解・推奨",
}
STATUS_LABELS = {
    "matched": "資料との照合済み",
    "partial": "一部のみ裏付けあり",
    "unverified": "未確認・根拠未登録",
    "conflict": "資料間に不一致あり",
}
METHOD_LABELS = {
    "ai_document_review": "AIによる資料照合",
    "human_document_review": "人による資料照合",
    "operator_test": "運営者の実測記録",
}
INFORMATION_LABELS = {
    "", "Fact", "Fact-A", "Fact-B", "Fact-C", "Claim", "Opinion",
    "Forecast", "Opinion / Forecast", "Opinion/Forecast", "Rumor", "Curated",
}
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,99}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")


def normalized_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_http_url(value: Any) -> str:
    """Accept direct HTTP(S) URLs only; never create an executable link."""
    if not isinstance(value, str) or not value or any(ord(c) <= 32 or ord(c) == 127 for c in value):
        return ""
    if "\\" in value:
        return ""
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"https", "http"} or not parts.hostname:
            return ""
        if parts.username is not None or parts.password is not None:
            return ""
        _ = parts.port  # Reject invalid ports, including malformed authority text.
    except ValueError:
        return ""
    return value


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def article_fingerprint(item: dict) -> str:
    return _digest({field: normalized_text(item.get(field)) for field in ("title", "tldr", "summary")})


def claim_fingerprint(claim: dict, sources: list[dict]) -> str:
    """Bind a review to wording, conditions and the exact support references."""
    source_map = {s["id"]: s for s in sources if isinstance(s, dict) and isinstance(s.get("id"), str)}
    references = claim.get("source_refs") if isinstance(claim.get("source_refs"), list) else []
    payload = {field: claim.get(field) for field in (
        "statement", "evidence_label", "basis", "conditions", "as_of", "uncertainty", "measurement"
    )}
    payload["statement"] = normalized_text(payload["statement"])
    payload["source_refs"] = [
        {"reference": ref, "source": source_map.get(str(ref.get("source_id")))}
        for ref in references if isinstance(ref, dict)
    ]
    return _digest(payload)


def validate_bundle(bundle: Any, subject: dict | None = None) -> list[str]:
    """Validate explicit records. Missing legacy metadata is not an error."""
    if bundle is None or bundle == {}:
        return []
    if not isinstance(bundle, dict):
        return ["claim_evidence: object required"]
    errors: list[str] = []
    if bundle.get("version") != 1:
        errors.append("claim_evidence: unsupported version")
    sources, claims = bundle.get("sources"), bundle.get("claims")
    if not isinstance(sources, list) or not isinstance(claims, list) or not claims:
        return errors + ["claim_evidence: sources list and nonempty claims list required"]
    source_map: dict[str, dict] = {}
    for source in sources:
        if not isinstance(source, dict):
            errors.append("source: object required")
            continue
        sid = source.get("id")
        if not isinstance(sid, str) or not _ID.fullmatch(sid) or sid in source_map:
            errors.append(f"source: invalid or duplicate id {sid!r}")
            continue
        source_map[sid] = source
        for key in ("publisher", "title"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                errors.append(f"source {sid}: {key} required")
        if not safe_http_url(source.get("url")):
            errors.append(f"source {sid}: safe HTTP(S) URL required")
        if source.get("published_at") is not None and not _valid_date(source["published_at"]):
            errors.append(f"source {sid}: invalid published_at")

    ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("claim: object required")
            continue
        cid = claim.get("id")
        if not isinstance(cid, str) or not _ID.fullmatch(cid) or cid in ids:
            errors.append(f"claim: invalid or duplicate id {cid!r}")
            continue
        ids.add(cid)
        prefix = f"claim {cid}"
        if not isinstance(claim.get("statement"), str) or not claim["statement"].strip():
            errors.append(f"{prefix}: statement required")
        if not isinstance(claim.get("basis"), str) or claim["basis"] not in BASIS_LABELS:
            errors.append(f"{prefix}: unknown basis")
        if not isinstance(claim.get("evidence_label", ""), str) or claim.get("evidence_label", "") not in INFORMATION_LABELS:
            errors.append(f"{prefix}: unknown evidence_label")
        status = claim.get("status")
        if not isinstance(status, str) or status not in STATUS_LABELS:
            errors.append(f"{prefix}: unknown status")
        conditions = claim.get("conditions")
        if not isinstance(conditions, list) or any(not isinstance(c, str) or not c.strip() for c in conditions):
            errors.append(f"{prefix}: conditions must be a list of nonempty strings")
        if claim.get("as_of") is not None and not _valid_date(claim["as_of"]):
            errors.append(f"{prefix}: invalid as_of")
        refs = claim.get("source_refs")
        if not isinstance(refs, list):
            errors.append(f"{prefix}: source_refs list required")
            refs = []
        for ref in refs:
            if not isinstance(ref, dict) or not isinstance(ref.get("source_id"), str) or ref["source_id"] not in source_map:
                errors.append(f"{prefix}: missing referenced source")
                continue
            if not all(isinstance(ref.get(k), str) and ref[k].strip() for k in ("section", "supports")):
                errors.append(f"{prefix}: each source needs section and supports")
        verified_state = isinstance(status, str) and status in {"matched", "partial", "conflict"}
        verification = claim.get("verification")
        if verified_state and (not refs or not isinstance(verification, dict)):
            errors.append(f"{prefix}: stated verification requires sources and a review record")
        if verification is not None:
            if not isinstance(verification, dict):
                errors.append(f"{prefix}: invalid verification record")
            else:
                checked_at = verification.get("checked_at")
                if (checked_at is not None or verified_state) and not _valid_date(checked_at):
                    errors.append(f"{prefix}: valid checked_at required")
                if not isinstance(verification.get("method"), str) or verification["method"] not in METHOD_LABELS:
                    errors.append(f"{prefix}: documented review method required")
                if verification.get("fingerprint") != claim_fingerprint(claim, sources):
                    errors.append(f"{prefix}: review fingerprint does not match current statement/conditions/sources")
        if claim.get("basis") == "operator_measurement":
            measurement = claim.get("measurement")
            if not isinstance(measurement, dict) or not all(
                isinstance(measurement.get(k), str) and measurement[k].strip() for k in ("environment", "method")
            ) or not safe_http_url(measurement.get("results_url")):
                errors.append(f"{prefix}: operator measurement requires environment, method and results URL")
    subject_digest = bundle.get("subject_fingerprint")
    if subject is not None and subject_digest is None:
        errors.append("claim_evidence: article metadata requires a reviewed subject fingerprint")
    if subject_digest is not None:
        if not isinstance(subject_digest, str) or not _HASH.fullmatch(subject_digest):
            errors.append("claim_evidence: invalid subject fingerprint")
        elif subject is not None and subject_digest != article_fingerprint(subject):
            errors.append("claim_evidence: article text differs from the reviewed subject")
    return errors


def require_valid_evidence(bundle: Any, subject: dict | None = None) -> None:
    errors = validate_bundle(bundle, subject)
    if errors:
        raise ValueError("; ".join(errors))


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def render_evidence(bundle: Any, claim_ids: list[str] | None = None, subject: dict | None = None) -> str:
    """Native, keyboard-operable details; limits and status remain visible."""
    if bundle is None or bundle == {}:
        return ""
    errors = validate_bundle(bundle, subject)
    if not isinstance(bundle, dict) or not isinstance(bundle.get("claims"), list):
        return '<p class="claim-evidence-warning">根拠情報の形式を再確認してください（未確認）。</p>'
    source_list = bundle.get("sources") if isinstance(bundle.get("sources"), list) else []
    sources = {s["id"]: s for s in source_list if isinstance(s, dict) and isinstance(s.get("id"), str)}
    blocks = []
    for claim in bundle["claims"]:
        if not isinstance(claim, dict) or (claim_ids is not None and claim.get("id") not in claim_ids):
            continue
        cid = claim.get("id", "")
        invalid = bool(errors)  # A malformed bundle must never show a false verified record.
        status = "unverified" if invalid else claim.get("status", "unverified")
        verification = claim.get("verification") if not invalid else None
        checked_at = verification.get("checked_at") if isinstance(verification, dict) else None
        method = verification.get("method") if isinstance(verification, dict) else None
        date_html = f'照合 <time datetime="{_esc(checked_at)}">{_esc(checked_at)}</time>' if _valid_date(checked_at) else "照合日未記録"
        method_text = METHOD_LABELS.get(str(method), "確認方法未記録")
        conditions = claim.get("conditions") if isinstance(claim.get("conditions"), list) else []
        limits = " / ".join(str(v) for v in conditions)
        if claim.get("uncertainty"):
            limits += (" / " if limits else "") + str(claim["uncertainty"])
        refs_html = []
        refs = claim.get("source_refs") if isinstance(claim.get("source_refs"), list) else []
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            source = sources.get(str(ref.get("source_id")))
            if not source:
                continue
            url = safe_http_url(source.get("url"))
            title = _esc(source.get("title"))
            link = f'<a href="{_esc(url)}" target="_blank" rel="noopener noreferrer">{title}</a>' if url else title + "（URL要確認）"
            published_at = source.get("published_at")
            publication = f' / 出典公開日 {_esc(published_at)}' if _valid_date(published_at) else " / 出典公開日未記録"
            refs_html.append(
                f'<li><span>{_esc(source.get("publisher"))} — {link}</span>'
                f'<span class="claim-evidence-support">該当箇所: {_esc(ref.get("section"))}。裏付ける内容: {_esc(ref.get("supports"))}{publication}</span></li>'
            )
        refs_block = '<ul class="claim-evidence-sources">' + "".join(refs_html) + "</ul>" if refs_html else '<p>対応する出典情報は未登録です。未登録は虚偽の判定ではありません。</p>'
        as_of = f'<p>対象時点: {_esc(claim["as_of"])}</p>' if _valid_date(claim.get("as_of")) else '<p>対象時点: 未記録</p>'
        note = f'<p>照合範囲: {_esc(verification.get("note"))}</p>' if isinstance(verification, dict) and verification.get("note") else ""
        warning = '<p class="claim-evidence-warning">本文・条件または根拠記録に不整合があるため、照合状態を再確認してください。</p>' if invalid else ""
        anchor = f' id="evidence-{_esc(cid)}"' if isinstance(cid, str) and _ID.fullmatch(cid) else ""
        blocks.append(
            f'<aside class="claim-evidence"{anchor} data-evidence-id="{_esc(cid)}">'
            f'<p class="claim-evidence-line"><strong>{_esc(claim.get("label") or "この主張")}</strong> '
            f'<span>{_esc(BASIS_LABELS.get(str(claim.get("basis")), "根拠の種類未登録"))}</span> · '
            f'<span class="claim-evidence-status">{_esc(STATUS_LABELS.get(status, STATUS_LABELS["unverified"]))}</span> · '
            f'<span>{date_html}（{_esc(method_text)}）</span></p>'
            f'{warning}'
            + (f'<p class="claim-evidence-limits">適用・制限: {_esc(limits)}</p>' if limits else "")
            + f'<details><summary>{_esc(claim.get("label") or "この主張")}の出典と照合範囲</summary>'
            f'<p class="claim-evidence-statement">照合対象: {_esc(claim.get("statement"))}</p>'
            f'<p>情報区分: {_esc(claim.get("evidence_label") or "未登録")}</p>{refs_block}{as_of}{note}'
            '<p class="claim-evidence-caveat">この表示は資料と主張の対応状況を示します。全環境での動作や独立した実証を保証しません。</p>'
            '</details></aside>'
        )
    return "\n".join(blocks)
