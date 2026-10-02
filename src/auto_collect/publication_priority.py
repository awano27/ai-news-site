"""Priority for the public daily timeline, independent of collector credentials."""
from datetime import date


def prefer_existing(existing: dict, candidate: dict) -> bool:
    """Never roll back a date or discard same-day curated X posts."""
    existing_date = date.fromisoformat(existing["date"])
    candidate_date = date.fromisoformat(candidate["date"])
    if existing_date != candidate_date:
        return existing_date > candidate_date
    existing_x = sum(item.get("type") == "x" for item in existing["items"])
    candidate_x = sum(item.get("type") == "x" for item in candidate["items"])
    return existing_x > candidate_x
