"""Priority for the public daily timeline, independent of collector credentials."""
from datetime import date


def prefer_existing(existing: dict, candidate: dict) -> bool:
    """Never roll back a date.

    On the same day, keep a bundle with more X posts only when the candidate
    did not judge X itself. A missing vault yields no posts and must not erase
    curated ones. A candidate marked x_authoritative read bookmarks and ran
    the quality gate, so its smaller set replaces the previous bundle.
    """
    existing_date = date.fromisoformat(existing["date"])
    candidate_date = date.fromisoformat(candidate["date"])
    if existing_date != candidate_date:
        return existing_date > candidate_date
    if candidate.get("x_authoritative") is True:
        return False
    existing_x = sum(item.get("type") == "x" for item in existing["items"])
    candidate_x = sum(item.get("type") == "x" for item in candidate["items"])
    return existing_x > candidate_x
