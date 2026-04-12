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

logger = logging.getLogger(__name__)

OUTPUT_PATH = PROJECT_ROOT / "presentations" / "auto_daily_report.html"


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

            # Parse title and metadata
            match = re.match(r'■ (.+?)（(.+?) / スコア: (\d+)）', line)
            if match:
                current_item = {
                    "title": match.group(1),
                    "category": match.group(2),
                    "score": int(match.group(3)),
                    "source": "",
                    "summary": "",
                    "points": [],
                    "metrics": [],
                    "competitors": [],
                    "impact": "",
                    "actionable": "",
                    "url": "",
                    "hn_score": "",
                }
            else:
                current_item = {
                    "title": line[2:].strip(),
                    "category": "",
                    "score": 0,
                    "source": "",
                    "summary": "",
                    "points": [],
                    "metrics": [],
                    "competitors": [],
                    "impact": "",
                    "actionable": "",
                    "url": "",
                    "hn_score": "",
                }
            continue

        if current_item is None:
            continue

        line_s = line.strip()
        if line_s.startswith("ソース:"):
            current_item["source"] = line_s[4:].strip()
        elif line_s.startswith("📊"):
            current_item["metrics"].append(line_s[2:].strip().lstrip("数値:").strip())
        elif line_s.startswith("🔄"):
            current_item["competitors"].append(line_s[2:].strip().lstrip("競合:").strip())
        elif line_s.startswith("🇯🇵"):
            current_item["impact"] = line_s[4:].strip().lstrip("影響:").strip()
        elif line_s.startswith("⚡"):
            current_item["actionable"] = line_s[1:].strip().lstrip("今すぐ:").strip()
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


def generate_html(data: Dict) -> str:
    """Generate HTML from template + data."""
    report_date = data["date"] or date.today().isoformat()
    headlines = data["headlines"]
    funding = data["funding"]
    # Filter GitHub section to only include github.com URLs
    github = [g for g in data["github"] if "github.com" in g.get("url", "")]
    models = data["models"]

    total = len(headlines) + len(funding) + len(github) + len(models)
    high_score = len([h for h in headlines if h.get("score", 0) >= 80])
    categories = {}
    for h in headlines:
        cat = h.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    # Read template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    now = datetime.now().strftime("%Y-%m-%d %H:%M JST")

    cat_tags = "".join(
        f'<span class="tag">{_esc(cat)} <b>{cnt}</b></span>'
        for cat, cnt in sorted(categories.items(), key=lambda x: -x[1])
    )

    headlines_html = "\n".join(_render_news_row(i, item) for i, item in enumerate(headlines, 1))
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

    return html


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


def _render_news_row(rank: int, item: Dict) -> str:
    score = item.get("score", 0)
    cat = item.get("category", "")

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
    <span class="row-cat {_cat_class(cat)}">{_esc(cat)}</span>
    <span class="row-src">{_esc(item.get("source",""))}</span>
    <span class="row-score {_score_class(score)}">{score}</span>
    <span class="row-arr">&#9660;</span>
  </div>
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


def generate_html_report(txt_path: Path = None):
    """Main entry: parse txt and generate HTML."""
    if txt_path is None:
        mmdd = date.today().strftime("%m%d")
        txt_path = INPUT_DAY_DIR / f"{mmdd}.txt"

    if not txt_path.exists():
        logger.warning(f"[HTML] {txt_path} not found")
        return None

    logger.info(f"[HTML] Generating report from {txt_path}")
    data = parse_daily_txt(txt_path)
    html = generate_html(data)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    logger.info(f"[HTML] Report saved: {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    generate_html_report(path)
