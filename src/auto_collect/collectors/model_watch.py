"""Frontier model watch: did OpenAI / Anthropic / Google / xAI ship something?

Stateless by design: every signal carries its own publication date, so the
answer for a report date is recomputed from the vendors' official pages and
OpenRouter's model catalogue without remembering yesterday's snapshot.
The result is written to presentations/model_watch/<date>.json; the report
renderer only reads that file and never touches the network.
"""
from __future__ import annotations

import argparse
import html as _html
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WATCH_DIR = PROJECT_ROOT / "presentations" / "model_watch"
WINDOW_DAYS = 2  # report date and the day before (vendor time zones differ)
_UA = {"User-Agent": "Mozilla/5.0 (compatible; visionhub-model-watch/1.0; +https://visionhub.jp/)"}

# Model-related = names a concrete model, or is an API-level model change.
# Plain "with OpenAI models" customer stories stay out.
_MODEL_CHANGE_RE = re.compile(r"deprecat|retire|rate limit|context window|fine-tun|pricing|モデル", re.I)
# A launch needs both a launch verb and a concrete model name: "fast mode is
# now available for Opus" is an update, "Introducing Grok Voice 3.0" a launch.
LAUNCH_RE = re.compile(r"introduc|launch|\bGA\b|generally available|releas|unveil|debut|発表|リリース", re.I)
NAME_RE = re.compile(
    r"GPT-?\d|GPT-[A-Z][a-z]+|\bo\d\b|Sora \d|Claude (?:Opus|Sonnet|Haiku)|(?:Opus|Sonnet|Haiku) \d"
    r"|Gemini \d|Gemma \d|Veo \d|Imagen \d|Nano Banana|Grok(?: \w+)? \d"
)



def is_model_news(title: str) -> bool:
    return bool(NAME_RE.search(title) or _MODEL_CHANGE_RE.search(title))


_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE = rf"(?:{_MONTHS}|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.? \d{{1,2}}, 20\d\d"
_DATE_RE = re.compile(rf"\b({_DATE})\b")
# Only dates that are an element's whole text (headings, <time>, card meta).
# Dates inside sentences are deadlines or references, not publication dates.
_STANDALONE_DATE_RE = re.compile(rf"<(?:h[1-6]|time|p|div|span)\b[^>]*>\s*({_DATE})\s*<", re.I)
_HEAD_RE = re.compile(r"<(h[1-6]|strong)\b[^>]*>(.*?)</\1>", re.S | re.I)
_LI_RE = re.compile(r"<li\b[^>]*>(.*?)</li>", re.S | re.I)


def _text(fragment: str) -> str:
    return " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def _parse_date(raw: str) -> Optional[date]:
    raw = raw.replace("Sept ", "Sep ").replace(".", "")
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Parsers (pure: text in, entries out)
# ---------------------------------------------------------------------------

def parse_rss(xml: str) -> List[Dict]:
    entries = []
    for item in re.findall(r"<item\b.*?</item>", xml, re.S):
        title = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item, re.S)
        pub = re.search(r"<pubDate>(.*?)</pubDate>", item, re.S)
        link = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", item, re.S)
        if not (title and pub):
            continue
        try:
            day = parsedate_to_datetime(pub.group(1).strip()).astimezone(timezone.utc).date()
        except (TypeError, ValueError):
            continue
        entries.append({"date": day.isoformat(), "title": _text(title.group(1)),
                        "url": (link.group(1).strip() if link else "")})
    return entries


def parse_dated_html(page: str, base_url: str = "") -> List[Dict]:
    """Entries from pages that print "Month D, YYYY" next to each item.

    The title is the first heading/bold text after the date (changelogs, card
    lists); if the stretch up to the next date has none, the nearest heading
    before the date (featured cards put the headline above the date).
    """
    matches = list(_STANDALONE_DATE_RE.finditer(page))
    entries, seen = [], set()
    for i, m in enumerate(matches):
        day = _parse_date(m.group(1))
        if not day:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(page)
        window = page[m.end():min(end, m.end() + 4000)]
        title = ""
        heads = [_text(h.group(2)) for h in _HEAD_RE.finditer(window)]
        heads = [h for h in heads if h and not _DATE_RE.fullmatch(h)]
        if heads:
            title = heads[0]
        else:
            items = [_text(li) for li in _LI_RE.findall(window)]
            if items and items[0]:
                title = items[0]
            else:
                before = [_text(h.group(2)) for h in _HEAD_RE.finditer(page[max(0, m.start() - 1500):m.start()])]
                before = [h for h in before if h and not _DATE_RE.fullmatch(h)]
                title = before[-1] if before else ""
        if not title:
            continue
        title = title[:160]
        key = (day, title)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"date": day.isoformat(), "title": title, "url": base_url})
    return entries


def parse_openrouter(payload: Dict, prefix: str) -> List[Dict]:
    models = []
    for m in payload.get("data", []):
        mid = m.get("id", "")
        if not mid.startswith(prefix) or ":" in mid:
            continue
        created = m.get("created")
        if not created:
            continue
        models.append({
            "id": mid,
            "name": m.get("name") or mid,
            "date": datetime.fromtimestamp(created, tz=timezone.utc).date().isoformat(),
        })
    models.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
    return models


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------

OPENROUTER_URL = "https://openrouter.ai/api/v1/models"

VENDORS = [
    {"key": "openai", "label": "OpenAI", "openrouter": "openai/", "sources": [
        ("公式ニュース", "https://openai.com/news/rss.xml", "rss"),
    ]},
    {"key": "anthropic", "label": "Anthropic", "openrouter": "anthropic/", "sources": [
        ("公式ニュース", "https://www.anthropic.com/news", "html"),
        ("API リリースノート", "https://docs.anthropic.com/en/release-notes/api", "html"),
    ]},
    {"key": "google", "label": "Google", "openrouter": "google/", "sources": [
        ("Google AI ブログ", "https://blog.google/technology/ai/rss/", "rss"),
        ("Gemini API 変更履歴", "https://ai.google.dev/gemini-api/docs/changelog", "html"),
    ]},
    {"key": "xai", "label": "xAI (Grok)", "openrouter": "x-ai/", "sources": [
        ("公式ニュース", "https://x.ai/news", "html"),
    ]},
]


def _get(url: str) -> str:
    resp = requests.get(url, headers=_UA, timeout=25)
    resp.raise_for_status()
    return resp.text


def build_watch(report_date: date, fetch: Callable[[str], str] = _get) -> Dict:
    since = report_date - timedelta(days=WINDOW_DAYS - 1)
    in_window = lambda iso: since.isoformat() <= iso <= report_date.isoformat()  # noqa: E731
    not_future = lambda e: e["date"] <= report_date.isoformat()  # noqa: E731

    try:
        catalogue = json.loads(fetch(OPENROUTER_URL))
        catalogue_error = None
    except Exception as exc:  # network / JSON
        catalogue, catalogue_error = {}, f"{type(exc).__name__}"
        logger.warning("[ModelWatch] OpenRouter failed: %s", exc)

    vendors = []
    for v in VENDORS:
        errors = []
        entries: List[Dict] = []
        for label, url, kind in v["sources"]:
            try:
                body = fetch(url)
                parsed = parse_rss(body) if kind == "rss" else parse_dated_html(body, url)
                if not parsed:
                    errors.append(f"{label}: 日付付きの項目を読み取れません")
                for e in parsed:
                    e["source"] = label
                entries.extend(e for e in parsed if not_future(e))
            except Exception as exc:
                errors.append(f"{label}: {type(exc).__name__}")
                logger.warning("[ModelWatch] %s %s failed: %s", v["key"], url, exc)
        if catalogue_error:
            errors.append(f"OpenRouter: {catalogue_error}")

        models = [m for m in parse_openrouter(catalogue, v["openrouter"]) if not_future(m)] if catalogue else []
        recent = [e for e in entries if in_window(e["date"])]
        model_news = [e for e in recent if is_model_news(e["title"])]
        launches = [e for e in model_news if LAUNCH_RE.search(e["title"]) and NAME_RE.search(e["title"])]
        for e in model_news:
            e["launch"] = e in launches
        new_models = [m for m in models if in_window(m["date"])]

        if new_models or launches:
            status = "launch"
        elif model_news:
            status = "update"
        elif errors and not entries and not models:
            status = "error"
        else:
            status = "quiet"

        latest_news = sorted((e for e in entries if is_model_news(e["title"])),
                             key=lambda e: e["date"], reverse=True)[:1]
        vendors.append({
            "key": v["key"],
            "label": v["label"],
            "status": status,
            "new_models": new_models[:6],
            "events": sorted(model_news, key=lambda e: (e["launch"], e["date"]), reverse=True)[:5],
            "other_count": len(recent) - len(model_news),
            "latest_model": models[0] if models else None,
            "last_model_news": latest_news[0] if latest_news else None,
            "errors": errors,
            "sources": [{"label": label, "url": url} for label, url, _ in v["sources"]],
        })

    return {
        "date": report_date.isoformat(),
        "window": {"from": since.isoformat(), "to": report_date.isoformat()},
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "vendors": vendors,
    }


def watch_path(report_date: str) -> Path:
    return WATCH_DIR / f"{report_date}.json"


def collect(report_date: date) -> Path:
    data = build_watch(report_date)
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    path = watch_path(report_date.isoformat())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info("[ModelWatch] %s: %s", path.name,
                ", ".join(f"{v['key']}={v['status']}" for v in data["vendors"]))
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser(description="Frontier model watch snapshot")
    ap.add_argument("--date", default=date.today().isoformat())
    print(collect(date.fromisoformat(ap.parse_args().date)))
