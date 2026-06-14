"""
ranking_data_parser.py — Pure data-parsing helpers for ranking reports.

Extracted from ranking_report_generator.py; the generator imports from here.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Dict, Any, List


def parse_ranking_data(file_path: str) -> Dict[str, Any]:
    """ランキングデータファイルを解析"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        ranking_items: List[Dict] = []

        pattern = (
            r"(\d+)\.\s\*\*([^*]+)\*\*:\s([^.\n]+\.)\sEng Tool:\s(\d+),"
            r"\sBiz Eff:\s(\d+),\s合計:\s(\d+)\.\s([^\n]+)"
        )
        matches = re.findall(pattern, content)

        for match in matches:
            rank, name, description, eng_tool, biz_eff, total, benefits = match
            ranking_items.append(
                {
                    "rank": int(rank),
                    "name": name.strip(),
                    "description": description.strip(),
                    "eng_tool": int(eng_tool),
                    "biz_eff": int(biz_eff),
                    "total_score": int(total),
                    "benefits": benefits.strip(),
                }
            )

        period_match = re.search(r"直近1ヶ月（(.+?)から(.+?)）", content)
        period_start = period_match.group(1) if period_match else "2025年7月27日"
        period_end = period_match.group(2) if period_match else "2025年8月27日"

        key_points: List[str] = []
        if "**キー points:**" in content:
            key_section = content.split("**キー points:**")[1].split("**ランキング概要**")[0]
            for line in key_section.split("\n"):
                if line.strip().startswith("- "):
                    key_points.append(line.strip()[2:])

        sectors: List[Dict] = []
        if "| セクター |" in content:
            lines = content.split("| セクター |")[1].split("\n")
            for line in lines[1:]:
                if line.startswith("|") and line.count("|") >= 6:
                    parts = [p.strip() for p in line.split("|")[1:-1]]
                    if len(parts) >= 5:
                        sectors.append(
                            {
                                "name": parts[0],
                                "representative": parts[1],
                                "count": int(parts[2]) if parts[2].isdigit() else 0,
                                "avg_score": float(parts[3]) if parts[3].replace(".", "").isdigit() else 0.0,
                                "use_case": parts[4],
                            }
                        )

        return {
            "period_start": period_start,
            "period_end": period_end,
            "ranking_items": ranking_items,
            "key_points": key_points,
            "sectors": sectors,
            "total_items": len(ranking_items),
        }

    except Exception as e:
        print(f"Error parsing ranking data: {e}")
        return {}


def analyze_ranking_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """ランキングデータの詳細分析"""
    items = data.get("ranking_items", [])

    if not items:
        return {}

    eng_scores = [item["eng_tool"] for item in items]
    biz_scores = [item["biz_eff"] for item in items]
    total_scores = [item["total_score"] for item in items]

    categories: Dict[str, List] = defaultdict(list)
    for item in items:
        name = item["name"].lower()
        if any(keyword in name for keyword in ["gpt", "claude", "llm", "model"]):
            categories["LLMモデル"].append(item)
        elif any(keyword in name for keyword in ["video", "image", "visual", "genie"]):
            categories["ビジュアル・メディア"].append(item)
        elif any(keyword in name for keyword in ["copilot", "excel", "pdf", "productivity"]):
            categories["生産性ツール"].append(item)
        else:
            categories["その他・特殊"].append(item)

    top_eng = sorted(items, key=lambda x: x["eng_tool"], reverse=True)[:5]
    top_biz = sorted(items, key=lambda x: x["biz_eff"], reverse=True)[:5]
    top_overall = sorted(items, key=lambda x: x["total_score"], reverse=True)[:10]

    high_impact = [item for item in items if item["total_score"] >= 8]
    medium_impact = [item for item in items if 6 <= item["total_score"] < 8]
    low_impact = [item for item in items if item["total_score"] < 6]

    return {
        "score_stats": {
            "avg_eng_score": round(sum(eng_scores) / len(eng_scores), 1),
            "avg_biz_score": round(sum(biz_scores) / len(biz_scores), 1),
            "avg_total_score": round(sum(total_scores) / len(total_scores), 1),
            "max_total_score": max(total_scores),
            "min_total_score": min(total_scores),
        },
        "categories": dict(categories),
        "top_performers": {
            "engineering": top_eng,
            "business": top_biz,
            "overall": top_overall,
        },
        "impact_distribution": {
            "high": high_impact,
            "medium": medium_impact,
            "low": low_impact,
        },
    }


def prepare_ranking_chart_data(data: Dict, analysis: Dict) -> Dict:
    """ランキング用チャートデータの準備"""
    items = data.get("ranking_items", [])

    score_ranges = {"8-9点": 0, "7点": 0, "6点": 0, "5点以下": 0}
    for item in items:
        score = item["total_score"]
        if score >= 8:
            score_ranges["8-9点"] += 1
        elif score == 7:
            score_ranges["7点"] += 1
        elif score == 6:
            score_ranges["6点"] += 1
        else:
            score_ranges["5点以下"] += 1

    categories = analysis.get("categories", {})
    category_data = {name: len(cat_items) for name, cat_items in categories.items()}

    top_10 = items[:10]
    eng_scores = [item["eng_tool"] for item in top_10]
    biz_scores = [item["biz_eff"] for item in top_10]
    item_names = [
        item["name"][:20] + "..." if len(item["name"]) > 20 else item["name"]
        for item in top_10
    ]

    return {
        "score_labels": json.dumps(list(score_ranges.keys())),
        "score_values": json.dumps(list(score_ranges.values())),
        "category_labels": json.dumps(list(category_data.keys())),
        "category_values": json.dumps(list(category_data.values())),
        "comparison_labels": json.dumps(item_names),
        "eng_scores": json.dumps(eng_scores),
        "biz_scores": json.dumps(biz_scores),
        "avg_total_score": analysis.get("score_stats", {}).get("avg_total_score", 0),
    }
