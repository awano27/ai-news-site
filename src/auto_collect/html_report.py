#!/usr/bin/env python3
"""
Generate HTML report page from daily auto-collected news.
Outputs to presentations/daily_ai_news_report_latest.html
Matches existing site design patterns.
"""

import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict

from .config import PROJECT_ROOT, INPUT_DAY_DIR
from . import trend_tracker
from . import ogp_generator

logger = logging.getLogger(__name__)

OUTPUT_PATH = PROJECT_ROOT / "presentations" / "auto_daily_report.html"
JSON_OUTPUT_PATH = PROJECT_ROOT / "presentations" / "auto_daily_report.json"
PUBLIC_API_DIR = PROJECT_ROOT / "public-pages" / "api" / "auto_daily_report"
DEFAULT_OG_IMAGE = "https://visionhub.jp/presentations/daily_reports/og/default.png"


def parse_daily_txt(txt_path: Path) -> Dict:
    """Parse enhanced MMDD.txt into structured sections."""
    content = txt_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    result = {
        "title": lines[0] if lines else "",
        "date": "",
        "headlines": [],
        "funding": [],
        "github": [],
        "models": [],
    }

    # Extract date from title
    m = re.match(r'(\d{4})年(\d{2})月(\d{2})日', result["title"])
    if m:
        result["date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    current_section = "headlines"
    current_item = None

    for line in lines:
        # Section headers
        if "ヘッドライン速報" in line:
            current_section = "headlines"
            continue
        elif "市場・資金動向" in line:
            current_section = "funding"
            continue
        elif "GitHub Trending" in line:
            current_section = "github"
            continue
        elif "HuggingFace注目モデル" in line:
            current_section = "models"
            continue
        elif line.startswith("="):
            continue

        # Article start
        if line.startswith("■ "):
            if current_item:
                result[current_section].append(current_item)

            base_item = {
                "title": "",
                "category": "",
                "score": 0,
                "source": "",
                "tldr": "",
                "summary": "",
                "points": [],
                "metrics": [],
                "competitors": [],
                "impact": "",
                "actionable": "",
                "evidence_label": "",
                "url": "",
                "hn_score": "",
            }

            match = re.match(r'■ (.+?)（(.+?) / スコア: (\d+)）', line)
            if match:
                base_item.update({
                    "title": match.group(1),
                    "category": match.group(2),
                    "score": int(match.group(3)),
                })
            else:
                base_item["title"] = line[2:].strip()
            current_item = base_item
            continue

        if current_item is None:
            continue

        line_s = line.strip()
        if line_s.startswith("ソース:"):
            current_item["source"] = line_s[4:].strip()
        elif line_s.startswith("🎯"):
            tldr_text = line_s.replace("🎯", "").strip()
            tldr_text = re.sub(r'^TL;DR\s*:\s*', '', tldr_text, flags=re.IGNORECASE).strip()
            current_item["tldr"] = tldr_text
        elif line_s.startswith("📊"):
            current_item["metrics"].append(line_s[2:].strip().lstrip("数値:").strip())
        elif line_s.startswith("🔄"):
            current_item["competitors"].append(line_s[2:].strip().lstrip("競合:").strip())
        elif line_s.startswith("🇯🇵"):
            current_item["impact"] = line_s[4:].strip().lstrip("影響:").strip()
        elif line_s.startswith("⚡"):
            current_item["actionable"] = line_s[1:].strip().lstrip("今すぐ:").strip()
        elif line_s.startswith("🏷️ Label:") or line_s.startswith("🏷 Label:"):
            current_item["evidence_label"] = line_s.split("Label:", 1)[-1].strip()
        elif line_s.startswith("URL:"):
            current_item["url"] = line_s[4:].strip()
        elif line_s.startswith("HN Score:"):
            current_item["hn_score"] = line_s[9:].strip()
        elif line_s.startswith("📄"):
            current_item["license"] = line_s[2:].strip()
        elif line_s.startswith("🏷"):
            current_item["topics"] = line_s[2:].strip()
        elif line_s.startswith("📥") or line_s.startswith("❤"):
            current_item["metrics"].append(line_s)
        elif line_s.startswith("・") or line_s.startswith("- "):
            current_item["points"].append(line_s)
        elif line_s and not line_s.startswith("本日の"):
            if not current_item["summary"]:
                current_item["summary"] = line_s
            else:
                current_item["summary"] += " " + line_s

    # Save last item
    if current_item:
        result[current_section].append(current_item)

    return result


TEMPLATE_PATH = Path(__file__).parent / "report_template.html"


def _build_report_data(report_date: str, headlines: List[Dict], funding: List[Dict],
                        github: List[Dict], models: List[Dict],
                        categories: Dict[str, int], total: int) -> Dict:
    """Compute everything needed for the in-page chart script and the JSON API."""
    # Score buckets
    s = a = b = c = 0
    for h in headlines:
        sc = h.get("score", 0)
        if sc >= 85:
            s += 1
        elif sc >= 70:
            a += 1
        elif sc >= 50:
            b += 1
        else:
            c += 1

    # 7-day trend: pull archived counts and append today.
    trend = trend_tracker.recent_counts(report_date, days=7)
    trend = [t for t in trend if t["date"] != report_date]
    trend.append({"date": report_date, "count": total})
    trend = trend[-7:]

    return {
        "date": report_date,
        "total": total,
        "categories": categories,
        "score_buckets": {"s": s, "a": a, "b": b, "c": c},
        "trend": trend,
        "headlines": headlines,
        "funding": funding,
        "github": github,
        "models": models,
    }


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
        cards.append(f'''<a class="top3-card" href="#headlines">
  <div class="top3-rank">{i:02d}</div>
  <div class="top3-title">{title}</div>
  <div class="top3-tldr">{_esc(tldr_short)}</div>
  <div class="top3-foot">
    <span class="top3-score">{score}</span>
    <span>·</span><span>{cat}</span>
    <span>·</span><span>{source}</span>
  </div>
</a>''')
    return f'''<section class="top3" id="top3">
  <div class="top3-h">Top 3 of the day</div>
  <div class="top3-grid">
    {''.join(cards)}
  </div>
</section>'''


def generate_html(data: Dict) -> str:
    """Generate HTML from template + data."""
    report_date = data["date"] or date.today().isoformat()
    headlines = data["headlines"]
    funding = data["funding"]
    # Filter GitHub section to only include github.com URLs
    github = [g for g in data["github"] if "github.com" in g.get("url", "")]
    models = data["models"]

    # Defensive cross-section dedup. The same pass runs in main.py before
    # the txt is written, but applying it here too lets us heal an existing
    # day file (with duplicates from a prior pipeline version) by simply
    # re-running generate_html_report.
    from . import dedup as _dedup
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

    funding_section = f'''<section class="sec" id="funding">
    <div class="sec-actions">
      <div class="sec-h"><em>&#9650;</em> マーケット・資金動向</div>
      <button class="expand-btn" data-target="funding">すべて開く</button>
    </div>
    {funding_html}
  </section>''' if funding else ""

    github_section = f'''<section class="sec" id="github">
    <div class="sec-h"><em>&#9679;</em> GitHub トレンド</div>
    {github_html}
  </section>''' if github else ""

    models_section = f'''<section class="sec" id="models">
    <div class="sec-h"><em>&#9670;</em> 注目モデル</div>
    {models_html}
  </section>''' if models else ""

    top3_html = _render_top3(headlines)
    report_data = _build_report_data(report_date, headlines, funding, github, models, categories, total)
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
    og_path = ARCHIVE_DIR / og_filename
    if og_path.exists():
        html = html.replace("{{OG_IMAGE}}", f"https://visionhub.jp/presentations/daily_reports/{og_filename}")
    else:
        html = html.replace("{{OG_IMAGE}}", DEFAULT_OG_IMAGE)

    return html, report_data


def _cat_class(cat: str) -> str:
    c = cat.lower()
    if "model" in c: return "c-model"
    if "business" in c or "biz" in c: return "c-biz"
    if "product" in c: return "c-product"
    if "research" in c: return "c-research"
    if "hardware" in c or "hw" in c: return "c-hw"
    return "c-other"


def _score_class(score: int) -> str:
    if score >= 85: return "s-s"
    if score >= 70: return "s-a"
    if score >= 50: return "s-b"
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
        # Fallback: first sentence of the summary, capped.
        s = item["summary"]
        m = re.split(r'[。！？.!?]\s*', s, maxsplit=1)
        tldr = (m[0] if m else s).strip()[:90]
    tldr_html = f'<div class="row-tldr">{_esc(tldr)}</div>' if tldr else ""

    ev_rows = ""
    has_ev = any([item.get("metrics"), item.get("competitors"), item.get("impact"), item.get("actionable")])
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

    return f'''<div class="row">
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
</div>'''


def _render_github_row(rank: int, item: Dict) -> str:
    stats = " / ".join(item.get("metrics", []))
    return f'''<div class="gh">
  <span class="gh-n">{rank:02d}</span>
  <div class="gh-info">
    <div class="gh-name"><a href="{_esc(item.get('url',''))}" target="_blank">{_esc(item.get("title",""))}</a></div>
    <div class="gh-desc">{_esc(item.get("summary",""))}</div>
    {f'<span class="gh-cmd">{_esc(item.get("actionable",""))}</span>' if item.get("actionable") else ""}
  </div>
  <span class="gh-stars">{_esc(stats)}</span>
</div>'''


def _render_model_row(rank: int, item: Dict) -> str:
    metrics = " / ".join(item.get("metrics", []))
    return f'''<div class="mdl">
  <span class="gh-n">{rank:02d}</span>
  <div class="gh-info">
    <div class="gh-name"><a href="{_esc(item.get('url',''))}" target="_blank">{_esc(item.get("title",""))}</a></div>
    {f'<div class="gh-desc">{_esc(metrics)}</div>' if metrics else ""}
    {f'<span class="gh-cmd">{_esc(item.get("actionable",""))}</span>' if item.get("actionable") else ""}
  </div>
</div>'''


def _esc(text: str) -> str:
    """HTML escape."""
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


ARCHIVE_DIR = PROJECT_ROOT / "presentations" / "daily_reports"
ARCHIVE_INDEX_PATH = ARCHIVE_DIR / "index.json"
SEARCHABLE_INDEX_PATH = ARCHIVE_DIR / "searchable.json"
_ARCHIVE_FILE_RE = re.compile(r"^auto_daily_report_(\d{4})_(\d{2})_(\d{2})\.html$")
_TOTAL_META_RE = re.compile(r'<meta name="report:total" content="(\d+)"')
_HIGH_META_RE = re.compile(r'<meta name="report:high" content="(\d+)"')
_ROW_TITLE_RE = re.compile(r'<span class="row-title">([^<]+)</span>')


def rebuild_archive_index() -> int:
    """Rescan ARCHIVE_DIR and rewrite both index.json and searchable.json.

    `index.json` keeps the existing tiny shape (date+file+count) consumed by
    `daily_reports_archive.html`. `searchable.json` is the richer payload
    used by the in-browser full-text search added in Phase 4 — it carries
    per-report totals and the list of headline titles.
    """
    index_reports = []
    search_reports = []
    for p in sorted(ARCHIVE_DIR.glob("auto_daily_report_*.html")):
        m = _ARCHIVE_FILE_RE.match(p.name)
        if not m:
            continue
        iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        index_reports.append({"date": iso, "file": p.name})

        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        total_m = _TOTAL_META_RE.search(text)
        high_m = _HIGH_META_RE.search(text)
        titles = [t.strip() for t in _ROW_TITLE_RE.findall(text) if t.strip()]
        search_reports.append({
            "date": iso,
            "file": p.name,
            "total": int(total_m.group(1)) if total_m else len(titles),
            "high": int(high_m.group(1)) if high_m else 0,
            "titles": titles[:50],
        })

    index_reports.sort(key=lambda r: r["date"], reverse=True)
    search_reports.sort(key=lambda r: r["date"], reverse=True)

    ARCHIVE_INDEX_PATH.write_text(
        json.dumps(
            {
                "generated": date.today().isoformat(),
                "source": "presentations/daily_reports/",
                "count": len(index_reports),
                "reports": index_reports,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    SEARCHABLE_INDEX_PATH.write_text(
        json.dumps(
            {
                "generated": date.today().isoformat(),
                "count": len(search_reports),
                "reports": search_reports,
            },
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    return len(index_reports)


def generate_html_report(txt_path: Path = None):
    """Main entry: parse txt and generate HTML + JSON outputs.

    Saves:
      - presentations/auto_daily_report.html      (latest, always overwritten)
      - presentations/auto_daily_report.json      (machine-readable mirror)
      - presentations/daily_reports/auto_daily_report_YYYY_MM_DD.html  (archive)
      - presentations/daily_reports/index.json    (rebuilt from directory)
      - public-pages/api/auto_daily_report/latest.json (CDN-friendly API)
    """
    if txt_path is None:
        mmdd = date.today().strftime("%m%d")
        txt_path = INPUT_DAY_DIR / f"{mmdd}.txt"

    if not txt_path.exists():
        logger.warning(f"[HTML] {txt_path} not found")
        return None

    logger.info(f"[HTML] Generating report from {txt_path}")
    data = parse_daily_txt(txt_path)
    html, report_data = generate_html(data)

    # Save latest HTML
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    logger.info(f"[HTML] Report saved: {OUTPUT_PATH}")

    # Save JSON mirror (full data, including headlines)
    json_payload = json.dumps(report_data, ensure_ascii=False, indent=2) + "\n"
    JSON_OUTPUT_PATH.write_text(json_payload, encoding="utf-8")
    logger.info(f"[HTML] JSON saved: {JSON_OUTPUT_PATH}")

    # Public API copy (served by GitHub Pages)
    PUBLIC_API_DIR.mkdir(parents=True, exist_ok=True)
    (PUBLIC_API_DIR / "latest.json").write_text(json_payload, encoding="utf-8")

    # Save dated archive
    report_date = data.get("date") or date.today().isoformat()
    archive_filename = f"auto_daily_report_{report_date.replace('-', '_')}.html"
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / archive_filename
    archive_path.write_text(html, encoding="utf-8")
    logger.info(f"[HTML] Archive saved: {archive_path}")

    # OGP image (best-effort — silently skipped if Pillow unavailable)
    try:
        top_titles = [
            h.get("title", "")
            for h in sorted(report_data.get("headlines", []),
                            key=lambda h: h.get("score", 0), reverse=True)[:3]
        ]
        ogp_generator.render(
            report_date=report_date,
            total=report_data.get("total", 0),
            high=len([h for h in report_data.get("headlines", []) if h.get("score", 0) >= 80]),
            top_titles=top_titles,
        )
    except Exception as e:
        logger.warning(f"[HTML] OGP generation failed (continuing): {e}")

    # Rebuild the archive index.json consumed by daily_reports_archive.html
    count = rebuild_archive_index()
    logger.info(f"[HTML] Archive index rebuilt: {ARCHIVE_INDEX_PATH} ({count} reports)")

    return OUTPUT_PATH


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    generate_html_report(path)
