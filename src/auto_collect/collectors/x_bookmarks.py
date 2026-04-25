"""X (Twitter) bookmarks collector — reads pre-curated posts from the
Obsidian vault.

The vault is synced by a Playwright script that lives outside this repo
(C:/develop/obsidian/2026/scripts/x-sync). It scrapes x.com/i/bookmarks
hourly and drops one .md file per bookmark into 00 Inbox/X-Bookmarks/.

Each file is YAML-frontmatter + body. We parse them into the same article
shape the rest of the pipeline uses, but we mark them as user-curated so
downstream code can skip the LLM summarization step (the body is already
in Japanese, already concise, and re-summarizing degrades it).
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from ..config import X_BOOKMARKS_DIR, X_LOOKBACK_HOURS

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Anchor section headers to start-of-line so that empty sections don't make the
# capture group spill into the next section's header.
_BODY_SECTION_RE = re.compile(r"^##\s*本文\s*\n(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
_NOTE_SECTION_RE = re.compile(r"^##\s*メモ\s*\n(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)


def _parse_bookmark(path: Path) -> Optional[Dict]:
    """Return a normalized article dict, or None if the file is unparseable."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"[X] read failed: {path.name} ({e})")
        return None

    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        return None
    try:
        meta = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError as e:
        logger.warning(f"[X] yaml parse failed: {path.name} ({e})")
        return None

    rest = text[fm_match.end():]
    body_match = _BODY_SECTION_RE.search(rest)
    body = body_match.group(1).strip() if body_match else ""
    note_match = _NOTE_SECTION_RE.search(rest)
    note = note_match.group(1).strip() if note_match else ""

    if not body:
        return None

    url = meta.get("url", "")
    author = meta.get("author", "@unknown").lstrip("@")
    tweet_id = str(meta.get("tweet_id", "") or "")
    bookmark_date = meta.get("date")
    images = meta.get("images") or []

    title = _make_title(body)

    return {
        "name": title,
        "tagline": _truncate(body, 140),
        "description": body,
        "summary": _truncate(body, 280),
        "tldr": _truncate(body, 80),
        "rss_source": f"X (@{author})",
        "source": "X",
        "category": "X ポスト",
        "links": {"official": url} if url else {},
        "url": url,
        "source_rank": 1,
        "authors": f"@{author}",
        "x_curated": True,
        "x_tweet_id": tweet_id,
        "x_images": [img for img in images if isinstance(img, str)],
        "x_note": note,
        "bookmark_date": str(bookmark_date) if bookmark_date else "",
        "score": 75,
        "evidence_label": "Curated",
    }


def _make_title(body: str) -> str:
    first = body.strip().split("\n", 1)[0].strip()
    first = re.sub(r"https?://\S+", "", first).strip()
    if len(first) > 80:
        first = first[:78] + "…"
    return first or "(本文なし)"


def _truncate(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


class XBookmarksCollector:
    """Read ~/vault/00 Inbox/X-Bookmarks/*.md modified within `lookback_hours`."""

    def __init__(self, bookmarks_dir: Path = X_BOOKMARKS_DIR, lookback_hours: int = X_LOOKBACK_HOURS):
        self.bookmarks_dir = Path(bookmarks_dir)
        self.lookback_hours = lookback_hours

    def collect(self, target_date: date) -> List[Dict]:
        if not self.bookmarks_dir.exists():
            logger.info(f"[X] vault not found at {self.bookmarks_dir} — skipping (cloud run?)")
            return []

        cutoff = datetime.now() - timedelta(hours=self.lookback_hours)
        out: List[Dict] = []
        seen_ids = set()
        for path in sorted(self.bookmarks_dir.glob("*.md")):
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
            except OSError:
                continue
            if mtime < cutoff:
                continue
            article = _parse_bookmark(path)
            if not article:
                continue
            tid = article.get("x_tweet_id")
            if tid and tid in seen_ids:
                continue
            if tid:
                seen_ids.add(tid)
            out.append(article)

        logger.info(f"[X] collected {len(out)} bookmarks (lookback {self.lookback_hours}h)")
        return out
