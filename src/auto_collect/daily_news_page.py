"""daily-news/index.html generator.

Builds the network-wide timeline page consumed by https://visionhub.jp/daily-news/.

Distinct from auto_daily_report (curated Top 15) — this page is the full feed:
RSS / arXiv / GitHub / HuggingFace / Hacker News articles plus the user's own
X bookmarks (read from the Obsidian vault by XBookmarksCollector).

Output:
    daily-news/index.html               (always overwritten)
    daily-news/data.json                (machine-readable mirror)
    daily-news/archive/YYYY-MM-DD.html  (dated snapshot)
"""

from __future__ import annotations

import html
import json
import logging
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

DAILY_NEWS_DIR = PROJECT_ROOT / "daily-news"
ARCHIVE_DIR = DAILY_NEWS_DIR / "archive"
TEMPLATE_PATH = Path(__file__).parent / "daily_news_template.html"


CATEGORY_ALIASES = {
    "AI Research": "研究",
    "AI News": "ビジネス",
    "Tech News": "ビジネス",
    "Open Source": "ツール",
    "GitHub": "ツール",
    "Benchmark": "研究",
    "Funding": "ビジネス",
    "arXiv": "研究",
    "HuggingFace": "ツール",
    "X ポスト": "X",
}

TAB_ORDER = ["記事", "X", "ツール", "研究", "ビジネス"]


def _normalize_category(raw: str) -> str:
    if not raw:
        return "その他"
    return CATEGORY_ALIASES.get(raw, raw)


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _truncate(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _label_class(label: str) -> str:
    return {
        "Fact": "label-fact",
        "Claim": "label-claim",
        "Rumor": "label-rumor",
        "Curated": "label-curated",
    }.get(label or "", "")


def _flatten_news(articles: List[Dict], tag: str = "記事") -> List[Dict]:
    """Map a processor-output article into the timeline item shape."""
    out = []
    for a in articles or []:
        title = a.get("title") or a.get("name") or ""
        if not title:
            continue
        url = (a.get("url")
               or (a.get("links") or {}).get("official")
               or (a.get("links") or {}).get("github") or "")
        cat_raw = a.get("category") or a.get("rss_source") or tag
        cat = _normalize_category(cat_raw)
        score = int(a.get("score", 0) or 0)
        out.append({
            "type": "news",
            "title": title,
            "url": url,
            "summary": a.get("summary") or a.get("description") or a.get("tagline") or "",
            "tldr": a.get("tldr") or "",
            "evidence_label": a.get("evidence_label") or "",
            "score": score,
            "category": cat,
            "category_raw": cat_raw,
            "source": a.get("rss_source") or a.get("source") or "",
            "tag_group": tag,
        })
    return out


def _flatten_x(x_articles: List[Dict]) -> List[Dict]:
    out = []
    for a in x_articles or []:
        out.append({
            "type": "x",
            "title": a.get("name") or "",
            "url": a.get("url") or (a.get("links") or {}).get("official") or "",
            "body": a.get("description") or a.get("summary") or "",
            "tldr": a.get("tldr") or "",
            "evidence_label": a.get("evidence_label") or "Curated",
            "category": "X",
            "category_raw": "X ポスト",
            "source": a.get("rss_source") or "X",
            "author": a.get("authors") or "",
            "images": a.get("x_images") or [],
            "note": a.get("x_note") or "",
            "tweet_id": a.get("x_tweet_id") or "",
            "bookmark_date": a.get("bookmark_date") or "",
            "tag_group": "X",
            "score": int(a.get("score", 75) or 75),
        })
    return out


def _render_news_card(item: Dict) -> str:
    title = _esc(item["title"])
    url = _esc(item["url"])
    cat = _esc(item["category"])
    source = _esc(item["source"])
    score = item["score"]
    summary = _esc(_truncate(item.get("summary", ""), 240))
    tldr = _esc(_truncate(item.get("tldr", ""), 100))
    label = item.get("evidence_label", "")
    label_html = (
        f'<span class="label-pill {_label_class(label)}">{_esc(label)}</span>'
        if label else ""
    )
    high_class = " high" if score >= 80 else ""
    score_class = " s" if score >= 80 else ""
    title_html = f'<a href="{url}" target="_blank" rel="noopener">{title}</a>' if url else title
    open_link = f'<a class="open" href="{url}" target="_blank" rel="noopener">開く ↗</a>' if url else ""
    search_text = (item["title"] + " " + (item.get("summary") or "") + " " + source).lower()

    return f'''<article class="card{high_class}" data-cat="{cat}" data-search="{_esc(search_text)}">
  <div class="card-meta">
    <span class="cat-pill">{cat}</span>
    <span class="source">{source}</span>
    <span class="score{score_class}">score {score}</span>
  </div>
  <h2 class="card-title">{title_html}</h2>
  {f'<div class="card-tldr">{tldr}</div>' if tldr else ''}
  {f'<div class="card-body">{summary}</div>' if summary else ''}
  <div class="card-foot">
    {label_html}
    {open_link}
  </div>
</article>'''


def _render_x_card(item: Dict) -> str:
    title = _esc(item["title"])
    body = _esc(_truncate(item.get("body", ""), 600))
    author = _esc(item.get("author", ""))
    url = _esc(item["url"])
    note = item.get("note", "")
    images = item.get("images") or []
    images_html = ""
    if images:
        imgs = "".join(
            f'<img src="{_esc(u)}" alt="" loading="lazy">'
            for u in images[:4] if u
        )
        images_html = f'<div class="x-images">{imgs}</div>'
    note_html = f'<div class="x-note">{_esc(note)}</div>' if note.strip() else ""
    title_html = f'<a href="{url}" target="_blank" rel="noopener">{title}</a>' if url else title
    open_link = f'<a class="open" href="{url}" target="_blank" rel="noopener">X で開く ↗</a>' if url else ""
    search_text = (item["title"] + " " + (item.get("body") or "") + " " + author).lower()

    return f'''<article class="card x-post" data-cat="X" data-search="{_esc(search_text)}">
  <div class="card-meta">
    <span class="x-pill">X</span>
    <span class="source">{author}</span>
  </div>
  <h2 class="card-title">{title_html}</h2>
  <div class="card-body">{body}</div>
  {images_html}
  {note_html}
  <div class="card-foot">
    <span class="label-pill label-curated">Curated</span>
    {open_link}
  </div>
</article>'''


def _build_tab_buttons(category_counts: Dict[str, int]) -> str:
    """Render category tab buttons in TAB_ORDER, then any leftover."""
    seen = set()
    btns = []
    for cat in TAB_ORDER:
        if cat in category_counts:
            btns.append(
                f'<button class="tab" data-cat="{_esc(cat)}">{_esc(cat)} '
                f'<span class="tab-count">{category_counts[cat]}</span></button>'
            )
            seen.add(cat)
    for cat, n in sorted(category_counts.items(), key=lambda e: -e[1]):
        if cat in seen:
            continue
        btns.append(
            f'<button class="tab" data-cat="{_esc(cat)}">{_esc(cat)} '
            f'<span class="tab-count">{n}</span></button>'
        )
    return "\n      ".join(btns)


def _render_timeline(items: List[Dict]) -> str:
    cards = []
    for it in items:
        cards.append(_render_x_card(it) if it["type"] == "x" else _render_news_card(it))
    return "\n".join(cards)


def generate_daily_news(
    today: date,
    articles: List[Dict],
    github_articles: Optional[List[Dict]] = None,
    benchmark_articles: Optional[List[Dict]] = None,
    funding_articles: Optional[List[Dict]] = None,
    x_articles: Optional[List[Dict]] = None,
) -> Optional[Path]:
    """Build daily-news/index.html from collector output."""
    DAILY_NEWS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    timeline: List[Dict] = []
    timeline.extend(_flatten_news(articles, tag="記事"))
    timeline.extend(_flatten_news(github_articles or [], tag="ツール"))
    timeline.extend(_flatten_news(benchmark_articles or [], tag="研究"))
    timeline.extend(_flatten_news(funding_articles or [], tag="ビジネス"))
    timeline.extend(_flatten_x(x_articles or []))

    # Sort by date desc first (stable), then by score desc — Python sort is
    # stable, so within each score bucket items remain in date-desc order.
    # That matters most for X bookmarks, which all share score=75.
    timeline.sort(key=lambda i: i.get("bookmark_date", ""), reverse=True)
    timeline.sort(key=lambda i: -int(i.get("score", 0) or 0))

    total = len(timeline)
    x_count = sum(1 for i in timeline if i["type"] == "x")
    news_count = total - x_count
    high_count = sum(1 for i in timeline if i.get("score", 0) >= 80)

    category_counts = Counter(i["category"] for i in timeline)
    source_counts = Counter(i["source"] for i in timeline if i.get("source"))

    report_date = today.isoformat()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    generated_iso = datetime.now().isoformat()

    # Trim source chart to top-8 for legibility
    top_sources = dict(source_counts.most_common(8))

    report_data = {
        "date": report_date,
        "generated_iso": generated_iso,
        "total": total,
        "news_count": news_count,
        "x_count": x_count,
        "high_count": high_count,
        "categories": dict(category_counts),
        "sources": top_sources,
        "items": timeline,
    }

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    timeline_html = _render_timeline(timeline) or '<div class="empty">本日の項目はまだありません</div>'

    html_out = (template
                .replace("{{REPORT_DATE}}", report_date)
                .replace("{{TOTAL}}", str(total))
                .replace("{{NEWS_COUNT}}", str(news_count))
                .replace("{{X_COUNT}}", str(x_count))
                .replace("{{HIGH_COUNT}}", str(high_count))
                .replace("{{TAB_BUTTONS}}", _build_tab_buttons(category_counts))
                .replace("{{TIMELINE_HTML}}", timeline_html)
                .replace("{{GENERATED_AT}}", generated_at)
                .replace("{{REPORT_DATA_JSON}}", json.dumps(report_data, ensure_ascii=False)))

    out_path = DAILY_NEWS_DIR / "index.html"
    out_path.write_text(html_out, encoding="utf-8")
    logger.info(f"[daily-news] written: {out_path}")

    json_path = DAILY_NEWS_DIR / "data.json"
    json_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")

    archive_path = ARCHIVE_DIR / f"{report_date}.html"
    archive_path.write_text(html_out, encoding="utf-8")
    logger.info(f"[daily-news] archive: {archive_path}")

    return out_path
