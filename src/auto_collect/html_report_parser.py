"""
html_report_parser.py — Parse daily MMDD.txt into structured section data.

Extracted from html_report.py; the orchestrator imports from here.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict

from . import trend_tracker


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
    m = re.match(r"(\d{4})年(\d{2})月(\d{2})日", result["title"])
    if m:
        result["date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    current_section = "headlines"
    current_item = None

    for line in lines:
        # Section headers
        if "ヘッドライン速報" in line:
            if current_item:
                result[current_section].append(current_item)
                current_item = None
            current_section = "headlines"
            continue
        elif "市場・資金動向" in line:
            if current_item:
                result[current_section].append(current_item)
                current_item = None
            current_section = "funding"
            continue
        elif "GitHub Trending" in line:
            if current_item:
                result[current_section].append(current_item)
                current_item = None
            current_section = "github"
            continue
        elif "HuggingFace注目モデル" in line:
            if current_item:
                result[current_section].append(current_item)
                current_item = None
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

            match = re.match(r"■ (.+?)（(.+?) / スコア: (\d+)）", line)
            if match:
                base_item.update(
                    {
                        "title": match.group(1),
                        "category": match.group(2),
                        "score": int(match.group(3)),
                    }
                )
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
            tldr_text = re.sub(r"^TL;DR\s*:\s*", "", tldr_text, flags=re.IGNORECASE).strip()
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


def build_report_data(
    report_date: str,
    headlines: List[Dict],
    funding: List[Dict],
    github: List[Dict],
    models: List[Dict],
    categories: Dict[str, int],
    total: int,
) -> Dict:
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
