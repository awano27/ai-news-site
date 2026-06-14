"""
html_report_renderer.py — Render structured report data to HTML.

Extracted from html_report.py; the orchestrator imports from here.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict

from .ogp_generator import render as _ogp_render
from . import trend_tracker
from . import dedup as _dedup

TEMPLATE_PATH = Path(__file__).parent / "report_template.html"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """HTML escape."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _cat_class(cat: str) -> str:
    c = cat.lower()
    if "model" in c:
        return "c-model"
    if "business" in c or "biz" in c:
        return "c-biz"
    if "product" in c:
        return "c-product"
    if "research" in c:
        return "c-research"
    if "hardware" in c or "hw" in c:
        return "c-hw"
    return "c-other"


def _score_class(score: int) -> str:
    if score >= 85:
        return "s-s"
    if score >= 70:
        return "s-a"
    if score >= 50:
        return "s-b"
    return "s-c"


def _label_class(label: str) -> str:
    l = (label or "").strip().lower()
    if l.startswith("fact"):
        return "lbl-fact"
    if l.startswith("claim"):
        return "lbl-claim"
    if l.startswith("rumor") or l.startswith("rumour"):
        return "lbl-rumor"
    return ""


def _render_top3(headlines: List[Dict]) -> str:
    if not headlines:
        return ""
    top = sorted(headlines, key=lambda h: h.get("score", 0), reverse=True)[:3]
    cards = []
    for i, h in enumerate(top, 1):
        title = _esc(h.get("title", ""))
        tldr = h.get("tldr") or h.get("summary", "")
        tldr_short = tldr[:90] + ("…" if len(tldr) > 90 else "")
        score = h.get("score", 0)
        source = _esc(h.get("source", ""))
        cat = _esc(h.get("category", ""))
        cards.append(
            f"""<a class="top3-card" href="#headlines">
  <div class="top3-rank">{i:02d}</div>
  <div class="top3-title">{title}</div>
  <div class="top3-tldr">{_esc(tldr_short)}</div>
  <div class="top3-foot">
    <span class="top3-score">{score}</span>
    <span>·</span><span>{cat}</span>
    <span>·</span><span>{source}</span>
  </div>
</a>"""
        )
    return f"""<section class="top3" id="top3">
  <div class="top3-h">Top 3 of the day</div>
  <div class="top3-grid">
    {"".join(cards)}
  </div>
</section>"""


def _render_news_row(rank: int, item: Dict, trend: str = None) -> str:
    score = item.get("score", 0)
    cat = item.get("category", "")
    label = item.get("evidence_label") or (item.get("evidence", {}) or {}).get("evidence_label", "")
    label_html = ""
    if label:
        cls = _label_class(label)
        if cls:
            label_html = f'<span class="row-label {cls}">{_esc(label[:6])}</span>'

    trend_html = ""
    if trend == "new":
        trend_html = '<span class="row-trend trend-new">🆕 NEW</span>'
    elif trend == "continuing":
        trend_html = '<span class="row-trend trend-cont">🔁 継続</span>'

    tldr = item.get("tldr") or ""
    if not tldr and item.get("summary"):
        s = item["summary"]
        m = re.split(r"[。！？.!?]\s*", s, maxsplit=1)
        tldr = (m[0] if m else s).strip()[:90]
    tldr_html = f'<div class="row-tldr">{_esc(tldr)}</div>' if tldr else ""

    ev_rows = ""
    has_ev = any(
        [item.get("metrics"), item.get("competitors"), item.get("impact"), item.get("actionable")]
    )
    if has_ev:
        if item.get("metrics"):
            ev_rows += f'<div class="d-ev-r"><span class="d-ev-k">DATA</span><span class="d-ev-v">{_esc("; ".join(item["metrics"]))}</span></div>'
        if item.get("competitors"):
            ev_rows += f'<div class="d-ev-r"><span class="d-ev-k">VS</span><span class="d-ev-v">{_esc(", ".join(item["competitors"]))}</span></div>'
        if item.get("impact"):
            ev_rows += f'<div class="d-ev-r"><span class="d-ev-k">IMPACT</span><span class="d-ev-v">{_esc(item["impact"])}</span></div>'
        if item.get("actionable"):
            ev_rows += f'<div class="d-ev-r"><span class="d-ev-k">ACTION</span><span class="d-ev-v"><code>{_esc(item["actionable"])}</code></span></div>'

    points_html = ""
    if item.get("points"):
        lis = "".join(f"<li>{_esc(p.lstrip('・- '))}</li>" for p in item["points"][:5])
        points_html = f'<ul class="d-points">{lis}</ul>'

    url_html = ""
    if item.get("url"):
        short = item["url"].replace("https://", "").replace("http://", "")[:70]
        url_html = f'<div class="d-url"><a href="{_esc(item["url"])}" target="_blank">{_esc(short)}</a></div>'

    return f"""<div class="row">
  <div class="row-head">
    <span class="row-n">{rank:02d}</span>
    <span class="row-title">{_esc(item.get("title",""))}</span>
    {trend_html}
    {label_html}
    <span class="row-cat {_cat_class(cat)}">{_esc(cat)}</span>
    <span class="row-src">{_esc(item.get("source",""))}</span>
    <span class="row-score {_score_class(score)}">{score}</span>
    <span class="row-arr">&#9660;</span>
  </div>
  {tldr_html}
  <div class="row-detail">
    <div class="d-summary">{_esc(item.get("summary",""))}</div>
    {points_html}
    {f'<div class="d-ev">{ev_rows}</div>' if ev_rows else ""}
    {url_html}
  </div>
</div>"""


def _render_github_row(rank: int, item: Dict) -> str:
    stats = " / ".join(item.get("metrics", []))
    return f"""<div class="gh">
  <span class="gh-n">{rank:02d}</span>
  <div class="gh-info">
    <div class="gh-name"><a href="{_esc(item.get('url',''))}" target="_blank">{_esc(item.get("title",""))}</a></div>
    <div class="gh-desc">{_esc(item.get("summary",""))}</div>
    {f'<span class="gh-cmd">{_esc(item.get("actionable",""))}</span>' if item.get("actionable") else ""}
  </div>
  <span class="gh-stars">{_esc(stats)}</span>
</div>"""


def _render_model_row(rank: int, item: Dict) -> str:
    metrics = " / ".join(item.get("metrics", []))
    return f"""<div class="mdl">
  <span class="gh-n">{rank:02d}</span>
  <div class="gh-info">
    <div class="gh-name"><a href="{_esc(item.get('url',''))}" target="_blank">{_esc(item.get("title",""))}</a></div>
    {f'<div class="gh-desc">{_esc(metrics)}</div>' if metrics else ""}
    {f'<span class="gh-cmd">{_esc(item.get("actionable",""))}</span>' if item.get("actionable") else ""}
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_html(data: Dict, archive_dir: Path, default_og_image: str) -> tuple:
    """Generate HTML from template + data.  Returns (html_str, report_data_dict)."""
    from .html_report_parser import build_report_data

    report_date = data["date"] or date.today().isoformat()
    headlines = data["headlines"]
    funding = data["funding"]
    # Filter GitHub section to only include github.com URLs
    github = [g for g in data["github"] if "github.com" in g.get("url", "")]
    models = data["models"]

    # Defensive cross-section dedup
    headlines, funding, models, github = _dedup.dedup_across_sections(
        headlines=headlines, funding=funding, models=models, github=github,
    )

    total = len(headlines) + len(funding) + len(github) + len(models)
    high_score = len([h for h in headlines if h.get("score", 0) >= 80])
    categories: Dict[str, int] = {}
    for h in headlines:
        cat = h.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    # Trend tag classification (new vs continuing)
    trend_map = trend_tracker.classify(
        [h.get("title", "") for h in headlines],
        today_iso=report_date,
    )

    # Read template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    now = datetime.now().strftime("%Y-%m-%d %H:%M JST")

    cat_tags = "".join(
        f'<span class="tag">{_esc(cat)} <b>{cnt}</b></span>'
        for cat, cnt in sorted(categories.items(), key=lambda x: -x[1])
    )

    headlines_html = "\n".join(
        _render_news_row(i, item, trend=trend_map.get(item.get("title", "")))
        for i, item in enumerate(headlines, 1)
    )
    funding_html = "\n".join(_render_news_row(i, item) for i, item in enumerate(funding, 1))
    github_html = "\n".join(_render_github_row(i, item) for i, item in enumerate(github, 1))
    models_html = "\n".join(_render_model_row(i, item) for i, item in enumerate(models, 1))

    funding_section = (
        f"""<section class="sec" id="funding">
    <div class="sec-actions">
      <div class="sec-h"><em>&#9650;</em> マーケット・資金動向</div>
      <button class="expand-btn" data-target="funding">すべて開く</button>
    </div>
    {funding_html}
  </section>"""
        if funding
        else ""
    )

    github_section = (
        f"""<section class="sec" id="github">
    <div class="sec-h"><em>&#9679;</em> GitHub トレンド</div>
    {github_html}
  </section>"""
        if github
        else ""
    )

    models_section = (
        f"""<section class="sec" id="models">
    <div class="sec-h"><em>&#9670;</em> 注目モデル</div>
    {models_html}
  </section>"""
        if models
        else ""
    )

    top3_html = _render_top3(headlines)
    report_data = build_report_data(
        report_date, headlines, funding, github, models, categories, total
    )
    # Strip heavy content from the in-page script — only chart-relevant fields.
    chart_payload = {
        "date": report_data["date"],
        "total": report_data["total"],
        "categories": report_data["categories"],
        "score_buckets": report_data["score_buckets"],
        "trend": report_data["trend"],
    }

    # Replace placeholders in template
    html = template
    html = html.replace("{{REPORT_DATE}}", _esc(report_date))
    html = html.replace("{{TOTAL}}", str(total))
    html = html.replace("{{HIGH}}", str(high_score))
    html = html.replace("{{GH_COUNT}}", str(len(github)))
    html = html.replace("{{MDL_COUNT}}", str(len(models)))
    html = html.replace("{{CAT_TAGS}}", cat_tags)
    html = html.replace("{{HEADLINES}}", headlines_html)
    html = html.replace("{{NOW}}", now)
    html = html.replace("{{NAV_FUNDING}}", '<a href="#funding">マーケット</a>' if funding else "")
    html = html.replace("{{NAV_GITHUB}}", '<a href="#github">GitHub</a>' if github else "")
    html = html.replace("{{NAV_MODELS}}", '<a href="#models">モデル</a>' if models else "")
    html = html.replace("{{FUNDING_SECTION}}", funding_section)
    html = html.replace("{{GITHUB_SECTION}}", github_section)
    html = html.replace("{{MODELS_SECTION}}", models_section)
    html = html.replace("{{TOP3_SECTION}}", top3_html)
    html = html.replace(
        "{{REPORT_DATA_JSON}}",
        json.dumps(chart_payload, ensure_ascii=False).replace("</", "<\\/"),
    )
    # OGP image: per-day file if present, else default.
    og_filename = f"og/{report_date.replace('-', '_')}.png"
    og_path = archive_dir / og_filename
    if og_path.exists():
        html = html.replace(
            "{{OG_IMAGE}}",
            f"https://visionhub.jp/presentations/daily_reports/{og_filename}",
        )
    else:
        html = html.replace("{{OG_IMAGE}}", default_og_image)

    return html, report_data
