"""Deterministic guards for sourced numerical claims in Daily News.

The collector normally treats summaries as presentation text.  A small set of
articles needs a durable, source-specific correction when a report contains
several financial metrics.  This module keeps those corrections structured so
the renderer can use the same values on every regeneration.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import re
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urlsplit, urlunsplit

from .claim_evidence import require_valid_evidence


class FinancialClaimError(ValueError):
    """Raised when one metric/event/currency is assigned two amounts."""


_UNIT_TO_MILLIONS = {
    "m": Decimal("1"),
    "million": Decimal("1"),
    "millions": Decimal("1"),
    "b": Decimal("1000"),
    "billion": Decimal("1000"),
    "billions": Decimal("1000"),
    "万": Decimal("0.01"),
    "億": Decimal("100"),
}


def canonical_url(url: str) -> str:
    """Drop tracking data without changing the article's identity."""
    parts = urlsplit(str(url or "").strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def normalize_financial_claim(claim: Dict[str, Any]) -> Dict[str, Any]:
    """Return a claim with a comparable ``amount_millions`` value.

    The input explicitly identifies the metric.  We intentionally do not infer
    a metric from nearby prose: a valuation, a round size, and a contract can
    legitimately have different values in the same article.
    """
    metric = str(claim.get("metric") or "").strip()
    currency = str(claim.get("currency") or "").strip().upper()
    event_date = str(claim.get("event_date") or "").strip()
    unit = str(claim.get("unit") or "").strip().lower()
    if not metric or not currency or not event_date or unit not in _UNIT_TO_MILLIONS:
        raise FinancialClaimError("financial claims need metric, currency, event_date, and a supported unit")
    try:
        amount = Decimal(str(claim["amount"]))
    except Exception as error:  # KeyError, InvalidOperation, or TypeError
        raise FinancialClaimError("financial claim amount must be numeric") from error
    if not amount.is_finite() or amount < 0:
        raise FinancialClaimError("financial claim amount must be finite and non-negative")

    normalized = dict(claim)
    normalized.update(
        {
            "metric": metric,
            "currency": currency,
            "event_date": event_date,
            "unit": unit,
            "amount": str(amount),
            "amount_millions": str(amount * _UNIT_TO_MILLIONS[unit]),
        }
    )
    return normalized


def validate_financial_claims(claims: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize claims and reject only conflicts within one article.

    ``event_date`` records the source-stated event date and is ``"unknown"``
    when the report does not state it; ``reported_at`` may separately preserve
    the report's publication date. Callers invoke this per article, so its key deliberately does not include
    an organization identifier.  ``metric``, ``currency``, and ``event_date``
    distinguish several facts reported by that one article; two separate
    articles never share this comparison scope.
    """
    normalized = [normalize_financial_claim(claim) for claim in claims]
    amounts: Dict[Tuple[str, str, str], Decimal] = {}
    for claim in normalized:
        key = (claim["metric"], claim["currency"], claim["event_date"])
        amount_millions = Decimal(claim["amount_millions"])
        previous = amounts.get(key)
        if previous is not None and previous != amount_millions:
            raise FinancialClaimError(
                "inconsistent financial claim for "
                f"metric={key[0]!r}, currency={key[1]!r}, event_date={key[2]!r}: "
                f"{previous}M versus {amount_millions}M"
            )
        amounts[key] = amount_millions
    return normalized


# This is an editorial correction, not an assertion that Crusoe itself issued a
# press release.  The wording preserves TechCrunch's attribution to Bloomberg.
CRUSOE_2026_09_05_URL = (
    "https://techcrunch.com/2026/09/03/"
    "crusoe-reportedly-raises-3b-at-a-30b-valuation"
)

# The source was reviewed as a TechCrunch article that attributes the report to
# Bloomberg.  These are not claims of a direct Crusoe announcement.  The
# literal seals below are filled once from this reviewed record and are never
# regenerated during rendering.
_CRUSOE_CLAIM_EVIDENCE: Dict[str, Any] = {
    "version": 1,
    "sources": [{
        "id": "techcrunch-crusoe-20260903",
        "publisher": "TechCrunch",
        "title": "Crusoe reportedly raises $3B at a $30B valuation",
        "url": CRUSOE_2026_09_05_URL,
        "published_at": "2026-09-03",
    }],
    "claims": [
        {
            "id": "crusoe-valuation",
            "label": "企業価値",
            "statement": "Crusoeの企業価値は約300億米ドルと報じられた。",
            "evidence_label": "Claim",
            "basis": "reporting",
            "status": "matched",
            "source_refs": [{
                "source_id": "techcrunch-crusoe-20260903",
                "section": "リード段落",
                "supports": "Bloomberg報道として、Crusoeの企業価値が約300億米ドルと記載されている。",
            }],
            "conditions": ["金額はTechCrunchがBloomberg報道として記した内容である。"],
            "as_of": "2026-09-03",
            "uncertainty": "Bloomberg原報を直接確認していない。Crusoe自身の公式発表もこの照合では確認していない。",
            "verification": {
                "checked_at": "2026-09-05",
                "method": "ai_document_review",
                "fingerprint": "b9ca46694a5ccf612f137f2b40a7f86f6287813b9c2a7329974a06c4cbe17677",
                "note": "TechCrunch本文をAIで確認。Bloomberg報道への帰属を維持し、Crusoeの直接発表とは扱わない。",
            },
        },
        {
            "id": "crusoe-funding",
            "label": "調達額",
            "statement": "Crusoeが約30億米ドルを調達したと報じられた。",
            "evidence_label": "Claim",
            "basis": "reporting",
            "status": "matched",
            "source_refs": [{
                "source_id": "techcrunch-crusoe-20260903",
                "section": "リード段落",
                "supports": "Bloomberg報道として、Crusoeが約30億米ドルを調達したと記載されている。",
            }],
            "conditions": ["金額はTechCrunchがBloomberg報道として記した内容である。"],
            "as_of": "2026-09-03",
            "uncertainty": "Bloomberg原報を直接確認していない。Crusoe自身の公式発表もこの照合では確認していない。",
            "verification": {
                "checked_at": "2026-09-05",
                "method": "ai_document_review",
                "fingerprint": "10f5a4f57489989cc5f4dc340f867315d1d1f8f33fc77204815750a440b3c017",
                "note": "TechCrunch本文をAIで確認。Bloomberg報道への帰属を維持し、Crusoeの直接発表とは扱わない。",
            },
        },
        {
            "id": "crusoe-contract",
            "label": "Jane Street契約",
            "statement": "Jane StreetへのGPU・AIインフラ提供の5年契約は約130億米ドルと報じられた。",
            "evidence_label": "Claim",
            "basis": "reporting",
            "status": "matched",
            "source_refs": [{
                "source_id": "techcrunch-crusoe-20260903",
                "section": "Jane Street契約段落",
                "supports": "Jane StreetへのGPU・AIインフラ提供の5年契約が約130億米ドルと記載されている。",
            }],
            "conditions": ["契約額と期間は資金調達・企業価値とは別の指標である。", "金額はTechCrunchがBloomberg報道として記した内容である。"],
            "as_of": "2026-09-03",
            "uncertainty": "Bloomberg原報を直接確認していない。Crusoe自身の公式発表もこの照合では確認していない。",
            "verification": {
                "checked_at": "2026-09-05",
                "method": "ai_document_review",
                "fingerprint": "c6292dee5d5206e48c4f8a943a2c853c97e54f709dd7e9a7754490b42a5ed90b",
                "note": "TechCrunch本文をAIで確認。Bloomberg報道への帰属を維持し、Crusoeの直接発表とは扱わない。",
            },
        },
    ],
    "subject_fingerprint": "001df1d0715df1c5075aa744f7694896348297cff4bac7223895f7f8956bbe12",
}

ARTICLE_CORRECTIONS: Dict[str, Dict[str, Any]] = {
    CRUSOE_2026_09_05_URL: {
        "tldr": "TechCrunchはBloomberg報道として、Crusoeが約30億米ドルを調達し、企業価値が約300億米ドルになったと報じた。",
        "title": "クルーソ、約300億米ドル評価で約30億米ドル調達",
        "summary": (
            "TechCrunchはBloomberg報道として、Crusoeが新ラウンドで約30億米ドルを調達し、"
            "企業価値が約300億米ドルになったと報じた。別件として、Jane StreetへのGPU・AIインフラ提供の"
            "5年契約は約130億米ドルと報じられている。"
        ),
        "source_attribution": "TechCrunch（Bloomberg報道）",
        "correction_note": "2026-09-05: 企業価値・調達額・契約額を別の指標として訂正。",
        "claim_evidence": _CRUSOE_CLAIM_EVIDENCE,
        "financial_claims": [
            {"metric": "valuation", "currency": "USD", "amount": "30", "unit": "billion", "event_date": "unknown", "reported_at": "2026-09-03"},
            {"metric": "funding", "currency": "USD", "amount": "3", "unit": "billion", "event_date": "unknown", "reported_at": "2026-09-03"},
            {"metric": "contract", "currency": "USD", "amount": "13", "unit": "billion", "event_date": "unknown", "reported_at": "2026-09-03", "term": "5 years"},
        ],
    }
}


def apply_article_correction(article: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a known source-specific correction exactly once, if applicable."""
    corrected = deepcopy(article)
    correction = ARTICLE_CORRECTIONS.get(canonical_url(corrected.get("url", "")))
    if not correction:
        return corrected

    # Do not retain generated evidence from the pre-correction summary.  Its
    # wording and any implied causal claims were not independently reviewed.
    evidence = {
        "metrics": [
            "企業価値: 約300億米ドル（TechCrunchのBloomberg報道）",
            "調達額: 約30億米ドル（TechCrunchのBloomberg報道）",
            "契約額: 約130億米ドル・5年（TechCrunchのBloomberg報道）",
        ],
        "competitors": [],
        "impact_ja": "",
        "actionable": "",
        "evidence_label": "Claim",
    }
    corrected.update(
        {
            "title": correction["title"],
            "tldr": correction["tldr"],
            "summary": correction["summary"],
            "source_attribution": correction["source_attribution"],
            "correction_note": correction["correction_note"],
            "financial_claims": validate_financial_claims(correction["financial_claims"]),
            "points": [],
            "metrics": list(evidence["metrics"]),
            "evidence": evidence,
            "evidence_label": "Claim",
            "impact": "",
            "actionable": "",
            "competitors": [],
            "claim_evidence": deepcopy(correction["claim_evidence"]),
        }
    )
    require_valid_evidence(corrected["claim_evidence"], corrected)
    return corrected


_METRIC_PATTERNS = {
    "valuation": r"企業価値|評価額|valuation",
    "funding": r"資金調達|調達額|調達|funding|raised?|raise",
    "contract": r"契約|contract",
}
_AMOUNT_PATTERN = re.compile(
    r"(?:"
    r"\$\s*(?P<dollar_amount>\d+(?:\.\d+)?)\s*(?P<dollar_unit>billion|billions|million|millions|[BM]|億|万)"
    r"|(?P<suffix_amount>\d+(?:\.\d+)?)\s*(?P<suffix_unit>billion|billions|million|millions|[BM]|億|万)\s*(?P<suffix_currency>米ドル|ドル|USD|円)"
    r")",
    re.IGNORECASE,
)


def _claims_found_in_text(text: str, event_date: str) -> List[Dict[str, Any]]:
    """Associate every amount with its nearest labelled metric in one sentence."""
    claims: List[Dict[str, Any]] = []
    for sentence in re.split(r"[。！？\n]+", text):
        # Japanese financial prose normally separates distinct facts with 、.
        # Keep each clause isolated so one amount is never assigned to every
        # metric that happens to occur in the same sentence.
        for clause in re.split(r"[、;；]", sentence):
            metric_matches = [
                (metric, match.start())
                for metric, pattern in _METRIC_PATTERNS.items()
                for match in re.finditer(pattern, clause, re.IGNORECASE)
            ]
            for match in _AMOUNT_PATTERN.finditer(clause):
                if not metric_matches:
                    continue
                ranked_metrics = sorted(metric_matches, key=lambda item: abs(item[1] - match.start()))
                metric, distance = ranked_metrics[0]
                nearest_distance = abs(distance - match.start())
                second_distance = (
                    abs(ranked_metrics[1][1] - match.start()) if len(ranked_metrics) > 1 else None
                )
                # Do not guess where two labels are equally close to one amount.
                if nearest_distance > 24 or (
                    second_distance is not None and second_distance - nearest_distance <= 8
                ):
                    continue
                amount = match.group("dollar_amount") or match.group("suffix_amount")
                unit = match.group("dollar_unit") or match.group("suffix_unit")
                currency = "USD" if match.group("dollar_amount") else (
                    "JPY" if match.group("suffix_currency") == "円" else "USD"
                )
                claims.append(
                    {
                        "metric": metric,
                        "currency": currency,
                        "amount": amount,
                        "unit": unit,
                        "event_date": event_date,
                    }
                )
    return claims


def apply_financial_integrity(article: Dict[str, Any]) -> Dict[str, Any]:
    """Correct known records or hold only a numerically conflicting article.

    Numbers without a nearby metric are warnings, not blockers.  A detected
    conflict is scoped to this article; the rest of the daily report remains
    publishable.  No network check occurs in this guard.
    """
    correction = ARTICLE_CORRECTIONS.get(canonical_url(article.get("url", "")))
    checked = apply_article_correction(article)
    if correction:
        return checked

    # A publication date is not proof of the date a deal occurred. The
    # processor also emits articles without dates; keep that fact unknown.
    event_date = str(checked.get("event_date") or "unknown")
    text_fields = [
        str(checked.get("title") or ""),
        str(checked.get("tldr") or ""),
        str(checked.get("summary") or ""),
        *[str(point) for point in checked.get("points") or []],
        *[str(metric) for metric in checked.get("metrics") or []],
    ]
    evidence = checked.get("evidence") or {}
    text_fields.extend(str(metric) for metric in evidence.get("metrics") or [])
    combined = "\n".join(text_fields)
    explicit_claims = list(checked.get("financial_claims") or [])
    candidate_claims = explicit_claims or _claims_found_in_text(combined, event_date)

    historical_comparison = bool(
        re.search(r"前年|昨年|前回|過去|previous|prior|earlier", combined, re.IGNORECASE)
    )
    try:
        if historical_comparison and candidate_claims and not explicit_claims:
            checked["integrity_warning"] = (
                "financial values span a prior-period comparison; manual source review recommended"
            )
            return checked
        if candidate_claims:
            checked["financial_claims"] = validate_financial_claims(candidate_claims)
    except FinancialClaimError as error:
        checked.update(
            {
                "title": "数値整合性を確認中",
                "integrity_status": "pending_fact_check",
                "integrity_warning": str(error),
                "tldr": "同じ指標に複数の数値を検出したため、原典を確認中です。",
                "summary": "数値の整合性を確認中のため、金額を含む要約の掲載を保留しています。",
                "points": [],
                "financial_claims": [],
                "metrics": [],
                "evidence_label": "",
                "impact": "",
                "actionable": "",
                "competitors": [],
                "evidence": {
                    "metrics": [],
                    "competitors": [],
                    "impact_ja": "",
                    "actionable": "",
                    "evidence_label": "",
                },
            }
        )
    else:
        if _AMOUNT_PATTERN.search(combined) and not candidate_claims:
            checked["integrity_warning"] = "financial amount found without a labelled metric; manual source review recommended"
    return checked
