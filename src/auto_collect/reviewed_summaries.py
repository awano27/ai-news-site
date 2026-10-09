"""Apply fixed, source-reviewed Japanese copy to explicitly listed article URLs.

This is editorial text, not a claim-evidence verification badge. Existing claim
bundles retain their wording and author-recorded fingerprints; builds must not
refresh or discard those records. No translation is invented for unlisted URLs.
The JSON registry is also consumed by the homepage builder.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .claim_evidence import safe_http_url
from .config import PROJECT_ROOT

REGISTRY_PATH = PROJECT_ROOT / "config" / "reviewed_news_summaries.json"
COPY_FIELDS = ("title", "tldr", "summary", "impact")
REVIEW_FIELDS = ("source_url", "source_date", "reviewed_at", "review_method")


def normalize_source_url(value: str) -> str:
    """Ignore scheme/host case and one final slash; retain path/query/fragment."""
    if not isinstance(value, str) or not safe_http_url(value.strip()):
        return ""
    parts = urlsplit(value.strip())
    return urlunsplit((
        parts.scheme.lower(), parts.netloc.lower(), parts.path.removesuffix("/"),
        parts.query, parts.fragment,
    ))


def load_reviewed_summaries(path: Path = REGISTRY_PATH) -> dict:
    """Read the shared, versioned editorial registry once per report."""
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("reviewed summaries: unsupported registry version")
    if not isinstance(payload.get("articles"), dict):
        raise ValueError("reviewed summaries: articles object required")
    summaries = {}
    for url, record in payload["articles"].items():
        canonical = normalize_source_url(url)
        if not canonical or canonical in summaries:
            raise ValueError("reviewed summaries: unsafe or duplicate source URL")
        fields = COPY_FIELDS + REVIEW_FIELDS + ("publisher",)
        if not isinstance(record, dict) or any(
            not isinstance(record.get(field), str) or not record[field].strip()
            for field in fields
        ):
            raise ValueError("reviewed summaries: nonempty copy and source metadata required")
        if canonical != normalize_source_url(record["source_url"]):
            raise ValueError("reviewed summaries: source URL must match its registry key")
        try:
            source_date = date.fromisoformat(record["source_date"])
            reviewed_at = date.fromisoformat(record["reviewed_at"])
            if (
                source_date.isoformat() != record["source_date"]
                or reviewed_at.isoformat() != record["reviewed_at"]
                or reviewed_at < source_date
            ):
                raise ValueError
        except ValueError as error:
            raise ValueError("reviewed summaries: valid source/review dates required") from error
        summaries[canonical] = record
    return summaries


def apply_reviewed_summary(item: dict, summaries: dict | None = None) -> dict:
    """Return enriched copy while leaving source data and evidence untouched."""
    result = dict(item)
    if item.get("claim_evidence") is not None:
        return result
    if summaries is None:
        summaries = load_reviewed_summaries()
    record = summaries.get(normalize_source_url(item.get("url", "")))
    if record is not None:
        result.update({field: record[field] for field in COPY_FIELDS})
        result["reviewed_summary"] = {field: record[field] for field in REVIEW_FIELDS}
    return result
