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


def generate_html(data: Dict) -> str:
    """Generate full HTML report page."""
    title = data["title"]
    report_date = data["date"] or date.today().isoformat()
    headlines = data["headlines"]
    funding = data["funding"]
    github = data["github"]
    models = data["models"]

    total = len(headlines) + len(funding) + len(github) + len(models)
    high_score = len([h for h in headlines if h.get("score", 0) >= 80])
    categories = {}
    for h in headlines:
        cat = h.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    # Build nav items
    nav_html = f'''
        <a href="#headlines" class="nav-item active">📰 ヘッドライン ({len(headlines)})</a>
    '''
    if funding:
        nav_html += f'<a href="#funding" class="nav-item">💰 資金動向 ({len(funding)})</a>\n'
    if github:
        nav_html += f'<a href="#github" class="nav-item">🔥 GitHub Trending ({len(github)})</a>\n'
    if models:
        nav_html += f'<a href="#models" class="nav-item">🤗 注目モデル ({len(models)})</a>\n'

    nav_html += '''
        <div style="margin-top:24px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.1);">
            <a href="index.html" class="nav-item">🏠 ホーム</a>
            <a href="day_slides_list.html" class="nav-item">📊 日次スライド</a>
            <a href="ai_external_resources.html" class="nav-item">🔗 外部リソース</a>
        </div>
    '''

    # Build stats cards
    cat_html = "".join(
        f'<span style="background:#e2e8f0;padding:4px 10px;border-radius:12px;margin:2px;display:inline-block;font-size:0.85rem">{cat}: {cnt}</span>'
        for cat, cnt in sorted(categories.items(), key=lambda x: -x[1])
    )

    # Build headlines
    headlines_html = ""
    for i, item in enumerate(headlines, 1):
        headlines_html += _render_news_item(i, item)

    # Build funding section
    funding_html = ""
    for i, item in enumerate(funding, 1):
        funding_html += _render_news_item(i, item)

    # Build github section
    github_html = ""
    for i, item in enumerate(github, 1):
        github_html += _render_github_item(i, item)

    # Build models section
    models_html = ""
    for i, item in enumerate(models, 1):
        models_html += _render_model_item(i, item)

    now = datetime.now().strftime("%Y-%m-%d %H:%M JST")

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | AI Intelligence</title>
    <style>
        :root {{
            --primary: #0f172a;
            --accent: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --research: #8b5cf6;
            --dark: #020617;
            --light: #f8fafc;
            --border: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px; line-height: 1.6; color: var(--text-primary); background: var(--light);
        }}
        .sidebar {{
            position: fixed; left: 0; top: 0; width: 260px; height: 100vh;
            background: var(--primary); padding: 24px 16px; overflow-y: auto;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1); z-index: 1000;
        }}
        .sidebar h1 {{ color: white; font-size: 1.1rem; margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 16px; }}
        .nav-item {{
            color: #94a3b8; display: block; padding: 8px 12px; border-radius: 6px;
            text-decoration: none; margin-bottom: 4px; transition: all 0.2s;
        }}
        .nav-item:hover {{ background: rgba(255,255,255,0.08); color: white; }}
        .nav-item.active {{ background: var(--accent); color: white; }}
        .main-content {{ margin-left: 260px; padding: 32px 48px; max-width: 1400px; background: white; min-height: 100vh; }}
        h1 {{ font-size: 2rem; color: var(--primary); margin-bottom: 8px; }}
        h2 {{ font-size: 1.4rem; margin: 32px 0 16px; color: var(--primary); padding-bottom: 8px; border-bottom: 2px solid var(--accent); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 24px 0; }}
        .stat-card {{
            background: var(--primary); color: white; text-align: center;
            padding: 20px; border-radius: 8px;
        }}
        .stat-value {{ font-size: 2rem; font-weight: bold; }}
        .stat-label {{ font-size: 0.85rem; color: #94a3b8; margin-top: 4px; }}
        .news-item {{
            background: white; border: 1px solid var(--border); border-radius: 8px;
            padding: 20px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            transition: all 0.2s;
        }}
        .news-item:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.12); transform: translateY(-2px); }}
        .news-rank {{
            background: var(--primary); color: white; width: 32px; height: 32px;
            border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 0.9rem; margin-right: 10px; flex-shrink: 0;
        }}
        .news-title {{ font-size: 1.15rem; font-weight: bold; color: var(--primary); }}
        .news-score {{
            padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;
            float: right; color: white;
        }}
        .score-high {{ background: var(--danger); }}
        .score-mid {{ background: var(--warning); }}
        .score-low {{ background: var(--success); }}
        .news-meta {{ color: var(--text-secondary); font-size: 0.85rem; margin: 6px 0; }}
        .news-summary {{ color: var(--text-secondary); margin: 10px 0; line-height: 1.7; }}
        .news-points {{ margin: 8px 0; padding-left: 8px; }}
        .news-points li {{ list-style: none; padding: 3px 0; color: var(--text-secondary); }}
        .news-points li::before {{ content: "•"; color: var(--accent); font-weight: bold; margin-right: 8px; }}
        .evidence {{
            background: #f0f9ff; border-radius: 8px; padding: 12px 16px; margin: 12px 0;
            border-left: 3px solid var(--accent); font-size: 0.9rem;
        }}
        .evidence-row {{ display: flex; align-items: baseline; margin: 4px 0; gap: 8px; }}
        .evidence-label {{ font-weight: 600; color: var(--primary); min-width: 60px; flex-shrink: 0; }}
        .evidence-value {{ color: var(--text-secondary); }}
        .tag {{
            display: inline-block; padding: 2px 10px; border-radius: 12px;
            font-size: 0.8rem; margin: 2px;
        }}
        .tag-category {{ background: #e0e7ff; color: #4338ca; }}
        .tag-source {{ background: #fef3c7; color: #92400e; }}
        .github-item {{
            background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 8px;
            padding: 16px; margin: 12px 0;
        }}
        .github-stars {{ color: #e3b341; font-weight: bold; }}
        .model-item {{
            background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px;
            padding: 16px; margin: 12px 0;
        }}
        .news-url {{ margin-top: 8px; }}
        .news-url a {{ color: var(--accent); text-decoration: none; font-size: 0.85rem; }}
        .news-url a:hover {{ text-decoration: underline; }}
        .footer {{ text-align: center; padding: 32px; color: var(--text-muted); font-size: 0.85rem; border-top: 1px solid var(--border); margin-top: 48px; }}
        @media (max-width: 768px) {{
            .sidebar {{ display: none; }}
            .main-content {{ margin-left: 0; padding: 16px; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h1>🤖 AI Daily Report</h1>
        <div style="color:#64748b; font-size:0.85rem; margin-bottom:16px;">{report_date}</div>
        {nav_html}
    </div>

    <div class="main-content">
        <h1>{title}</h1>
        <p style="color:var(--text-muted); margin-bottom:24px;">自動生成: {now} | Powered by Ollama + gemma3:4b</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total}</div>
                <div class="stat-label">総記事数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{high_score}</div>
                <div class="stat-label">高スコア (80+)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(github)}</div>
                <div class="stat-label">GitHub Trending</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(models)}</div>
                <div class="stat-label">注目モデル</div>
            </div>
        </div>

        <div style="margin: 16px 0;">{cat_html}</div>

        <h2 id="headlines">📰 ヘッドライン速報</h2>
        {headlines_html}

        {"<h2 id='funding'>💰 市場・資金動向</h2>" + funding_html if funding else ""}

        {"<h2 id='github'>🔥 GitHub Trending AI/ML</h2>" + github_html if github else ""}

        {"<h2 id='models'>🤗 HuggingFace 注目モデル</h2>" + models_html if models else ""}

        <div class="footer">
            <p>AI Daily News Report — 自動生成 by auto_collect system</p>
            <p>ソース: RSS (OpenAI, TechCrunch, The Verge, ITmedia等) / Hacker News / GitHub / HuggingFace</p>
        </div>
    </div>
</body>
</html>'''


def _score_class(score: int) -> str:
    if score >= 80:
        return "score-high"
    elif score >= 60:
        return "score-mid"
    return "score-low"


def _render_news_item(rank: int, item: Dict) -> str:
    score = item.get("score", 0)
    evidence_html = ""

    has_evidence = any([
        item.get("metrics"),
        item.get("competitors"),
        item.get("impact"),
        item.get("actionable"),
    ])

    if has_evidence:
        rows = ""
        if item.get("metrics"):
            metrics = "; ".join(item["metrics"])
            rows += f'<div class="evidence-row"><span class="evidence-label">📊 数値</span><span class="evidence-value">{_esc(metrics)}</span></div>'
        if item.get("competitors"):
            comp = ", ".join(item["competitors"])
            rows += f'<div class="evidence-row"><span class="evidence-label">🔄 競合</span><span class="evidence-value">{_esc(comp)}</span></div>'
        if item.get("impact"):
            rows += f'<div class="evidence-row"><span class="evidence-label">🇯🇵 影響</span><span class="evidence-value">{_esc(item["impact"])}</span></div>'
        if item.get("actionable"):
            rows += f'<div class="evidence-row"><span class="evidence-label">⚡ 実装</span><span class="evidence-value"><code>{_esc(item["actionable"])}</code></span></div>'
        evidence_html = f'<div class="evidence">{rows}</div>'

    points_html = ""
    if item.get("points"):
        lis = "".join(f"<li>{_esc(p.lstrip('・- '))}</li>" for p in item["points"][:5])
        points_html = f'<ul class="news-points">{lis}</ul>'

    url_html = ""
    if item.get("url"):
        url_html = f'<div class="news-url"><a href="{_esc(item["url"])}" target="_blank">🔗 {_esc(item["url"][:80])}</a></div>'

    return f'''
    <div class="news-item">
        <div style="display:flex;align-items:center;">
            <span class="news-rank">{rank}</span>
            <span class="news-title" style="flex:1;">{_esc(item.get("title", ""))}</span>
            <span class="news-score {_score_class(score)}">{score}</span>
        </div>
        <div class="news-meta">
            <span class="tag tag-category">{_esc(item.get("category", ""))}</span>
            <span class="tag tag-source">{_esc(item.get("source", ""))}</span>
            {f'<span class="tag" style="background:#fee2e2;color:#991b1b;">HN: {item["hn_score"]}</span>' if item.get("hn_score") else ""}
        </div>
        <div class="news-summary">{_esc(item.get("summary", ""))}</div>
        {points_html}
        {evidence_html}
        {url_html}
    </div>
    '''


def _render_github_item(rank: int, item: Dict) -> str:
    metrics = "; ".join(item.get("metrics", []))
    return f'''
    <div class="github-item">
        <div style="display:flex;align-items:center;gap:8px;">
            <span class="news-rank" style="background:#24292f;">{rank}</span>
            <span class="news-title" style="flex:1;">{_esc(item.get("title", ""))}</span>
            <span class="github-stars">{_esc(metrics)}</span>
        </div>
        <div class="news-summary">{_esc(item.get("summary", ""))}</div>
        {f'<div style="margin-top:8px;"><code style="background:#f0f0f0;padding:4px 8px;border-radius:4px;font-size:0.85rem;">{_esc(item.get("actionable", ""))}</code></div>' if item.get("actionable") else ""}
        {f'<div class="news-url"><a href="{_esc(item.get("url", ""))}" target="_blank">🔗 GitHub</a></div>' if item.get("url") else ""}
    </div>
    '''


def _render_model_item(rank: int, item: Dict) -> str:
    metrics = "; ".join(item.get("metrics", []))
    return f'''
    <div class="model-item">
        <div style="display:flex;align-items:center;gap:8px;">
            <span class="news-rank" style="background:#ea580c;">{rank}</span>
            <span class="news-title" style="flex:1;">{_esc(item.get("title", ""))}</span>
        </div>
        {f'<div style="margin:8px 0;color:var(--text-secondary);">{_esc(metrics)}</div>' if metrics else ""}
        {f'<div style="margin:8px 0;"><code style="background:#fff7ed;padding:4px 8px;border-radius:4px;font-size:0.85rem;">{_esc(item.get("actionable", ""))}</code></div>' if item.get("actionable") else ""}
        {f'<div class="news-url"><a href="{_esc(item.get("url", ""))}" target="_blank">🤗 HuggingFace</a></div>' if item.get("url") else ""}
    </div>
    '''


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
