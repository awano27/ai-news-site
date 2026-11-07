"""X Scout collector — verified topic JSON from the Grok bot.

The bot publishes one file per day on the data/x-scout branch. This collector
reads it over unauthenticated HTTP. A failed fetch, 404, invalid JSON, or a
generated_at older than 24 hours yields no posts and does not stop the daily
report. Accepted posts still go through process_x_posts and the shared quality
gate; summary_ja is only the text the model reads.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

import requests

from ..config import (
    X_SCOUT_BRANCH,
    X_SCOUT_MAX_AGE_HOURS,
    X_SCOUT_MAX_ITEMS,
    X_SCOUT_TIMEOUT,
    X_SCOUT_URL_TEMPLATE,
    x_scout_enabled,
)
from ..quality import valid_article_url

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
JST = timezone(timedelta(hours=9))
REQUIRED_ITEM_FIELDS = (
    "id",
    "title_ja",
    "summary_ja",
    "url_primary",
    "primary_date",
    "primary_verified",
    "x_url",
    "x_author",
    "x_posted_at",
    "evidence_label",
)


class XScoutFetchError(Exception):
    """The daily file could not be downloaded or was not JSON text."""


def _http_get(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=X_SCOUT_TIMEOUT,
            headers={"User-Agent": "visionhub-daily/1.0"},
        )
    except requests.RequestException as exc:
        raise XScoutFetchError(str(exc)) from exc
    if response.status_code == 404:
        raise XScoutFetchError("404")
    if response.status_code != 200:
        raise XScoutFetchError(f"HTTP {response.status_code}")
    return response.text


def scout_url(target_date: date) -> str:
    return X_SCOUT_URL_TEMPLATE.format(branch=X_SCOUT_BRANCH, date=target_date.isoformat())


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_generated_at(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return _as_utc(parsed)


def _calendar_day(value: object) -> Optional[date]:
    if not isinstance(value, str) or not value.strip():
        return None
    stamp = value.strip()
    try:
        if len(stamp) > 10:
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(JST)
            return parsed.date()
        return date.fromisoformat(stamp)
    except ValueError:
        return None


def _in_publication_window(day: date, today: date) -> bool:
    return today - timedelta(days=1) <= day <= today


def _required_text(item: Dict, key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        return ""
    return value.strip()


def _item_id(item: Dict) -> str:
    value = item.get("id")
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return ""
    return str(value).strip()


def _author_handle(value: str) -> str:
    return value.strip().lstrip("@")


class XScoutCollector:
    """Fetch one day's X Scout file and return at most five accepted posts."""

    def __init__(self, fetch: Optional[Callable[[str], str]] = None, now: Optional[Callable[[], datetime]] = None):
        self._fetch = fetch or _http_get
        self._now = now or (lambda: datetime.now(timezone.utc))

    def collect(self, target_date: date) -> List[Dict]:
        if not x_scout_enabled():
            return []
        url = scout_url(target_date)
        try:
            raw = self._fetch(url)
        except XScoutFetchError as exc:
            logger.warning("[X Scout] fetch failed for %s (%s); continuing without X Scout", url, exc)
            return []
        except Exception as exc:
            logger.warning("[X Scout] fetch failed for %s (%s); continuing without X Scout", url, exc)
            return []
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("[X Scout] invalid JSON from %s (%s); continuing without X Scout", url, exc)
            return []
        posts, problem = self._accept(payload, target_date)
        if problem:
            logger.warning("[X Scout] %s; continuing without X Scout", problem)
            return []
        return posts

    def _accept(self, payload: object, today: date) -> tuple[List[Dict], str]:
        if not isinstance(payload, dict):
            return [], "file is not a JSON object"
        if payload.get("schema_version") != SCHEMA_VERSION:
            return [], f"schema_version {payload.get('schema_version')!r} is not {SCHEMA_VERSION}"
        for key in ("date", "generated_at", "generated_by", "items"):
            if key not in payload:
                return [], f"missing {key}"
        if not isinstance(payload.get("generated_by"), str) or not payload["generated_by"].strip():
            return [], "generated_by is empty"
        generated = _parse_generated_at(payload.get("generated_at"))
        if generated is None:
            return [], "generated_at is missing or invalid"
        now = _as_utc(self._now())
        age = now - generated
        if age > timedelta(hours=X_SCOUT_MAX_AGE_HOURS):
            return [], f"generated_at {payload.get('generated_at')} is older than {X_SCOUT_MAX_AGE_HOURS} hours"
        items = payload.get("items")
        if not isinstance(items, list):
            return [], "items is not a list"

        accepted: List[Dict] = []
        seen: set[str] = set()
        rejected: Dict[str, int] = {}
        for item in items:
            reason = self._reject_reason(item, today, seen)
            if reason:
                rejected[reason] = rejected.get(reason, 0) + 1
                continue
            if len(accepted) >= X_SCOUT_MAX_ITEMS:
                rejected["over_cap"] = rejected.get("over_cap", 0) + 1
                continue
            seen.add(_item_id(item))
            accepted.append(_to_article(item))
        if rejected:
            detail = ", ".join(f"{reason}={count}" for reason, count in sorted(rejected.items()))
            logger.info("[X Scout] accepted %d, rejected %d (%s)", len(accepted), sum(rejected.values()), detail)
        else:
            logger.info("[X Scout] accepted %d posts", len(accepted))
        return accepted, ""

    def _reject_reason(self, item: object, today: date, seen: set[str]) -> str:
        if not isinstance(item, dict):
            return "missing_field"
        text_fields = tuple(key for key in REQUIRED_ITEM_FIELDS if key not in ("id", "primary_verified"))
        if not _item_id(item) or any(not _required_text(item, key) for key in text_fields):
            return "missing_field"
        if item.get("primary_verified") is not True:
            return "unverified"
        if not valid_article_url(item.get("url_primary")):
            return "bad_url"
        primary_day = _calendar_day(item.get("primary_date"))
        if primary_day is None or not _in_publication_window(primary_day, today):
            return "outside_window"
        if _item_id(item) in seen:
            return "duplicate_id"
        return ""


def _to_article(item: Dict) -> Dict:
    handle = _author_handle(_required_text(item, "x_author"))
    primary_day = _calendar_day(item.get("primary_date"))
    posted_day = _calendar_day(item.get("x_posted_at"))
    days = [day for day in (primary_day, posted_day) if day is not None]
    bookmark = max(days).isoformat() if days else ""
    summary = _required_text(item, "summary_ja")
    source = f"X Scout (@{handle})" if handle else "X Scout"
    url = _required_text(item, "url_primary")
    caveat = item.get("caveat")
    article = {
        "name": _required_text(item, "title_ja"),
        "tagline": summary[:140],
        "description": summary,
        "summary": "",
        "rss_source": source,
        "source": source,
        "category": "X ポスト",
        "links": {"official": url},
        "url": url,
        "authors": f"@{handle}" if handle else "",
        "x_curated": True,
        "x_scout": True,
        "x_tweet_id": str(item.get("x_tweet_id") or "").strip(),
        "x_url": _required_text(item, "x_url"),
        "x_images": [],
        "x_note": "",
        "bookmark_date": bookmark,
        "score": 75,
        "evidence_label": _required_text(item, "evidence_label"),
    }
    if isinstance(caveat, str) and caveat.strip():
        article["caveat"] = caveat.strip()
    return article
