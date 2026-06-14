"""
report_llm_builder.py — Build weekly/monthly report text (pure text aggregation).

Extracted from report_generator.py. No LLM/Ollama calls exist in the current
codebase; the module name reflects future intent per the goal spec.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import List, Dict


def build_weekly_report(items: List[Dict], start: date, end: date) -> str:
    """Build weekly summary report."""
    lines = []
    start_str = start.strftime("%Y年%m月%d日")
    end_str = end.strftime("%Y年%m月%d日")

    lines.append(f"📊 週次AIニュースレポート（{start_str} 〜 {end_str}）")
    lines.append("=" * 60)
    lines.append("")

    # Stats
    dates_covered = set(item["_date"] for item in items)
    categories = Counter(item.get("category", "Other") for item in items)
    high_score = [i for i in items if i.get("score", 0) >= 80]

    lines.append("📈 概要統計")
    lines.append(f"  記事総数: {len(items)}件（{len(dates_covered)}日分）")
    lines.append(f"  高スコア記事（80+）: {len(high_score)}件")
    lines.append("  カテゴリ分布:")
    for cat, count in categories.most_common():
        lines.append(f"    {cat}: {count}件")
    lines.append("")

    # Top 10 articles of the week
    top_items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)[:10]
    lines.append("🏆 今週のTOP 10")
    lines.append("-" * 40)
    for i, item in enumerate(top_items, 1):
        score = item.get("score", 0)
        cat = item.get("category", "")
        title = item.get("title", "")
        d = item.get("_date", "")
        lines.append(f"  {i}. [{score}] {title}")
        lines.append(f"     {cat} | {d}")
    lines.append("")

    # Category breakdown
    lines.append("📂 カテゴリ別ハイライト")
    lines.append("-" * 40)
    by_category: Dict[str, List] = defaultdict(list)
    for item in items:
        by_category[item.get("category", "Other")].append(item)

    for cat in ["AI Model", "Business", "Product", "Research", "Hardware"]:
        cat_items = by_category.get(cat, [])
        if cat_items:
            top = sorted(cat_items, key=lambda x: x.get("score", 0), reverse=True)[:3]
            lines.append(f"  [{cat}] ({len(cat_items)}件)")
            for item in top:
                lines.append(f"    ・{item['title']} (スコア: {item.get('score', 0)})")
            lines.append("")

    # Trend keywords
    all_titles = " ".join(item.get("title", "") for item in items).lower()
    keyword_counts: Counter = Counter()
    for kw in [
        "ai", "gpt", "llm", "agent", "model", "openai", "google",
        "nvidia", "meta", "anthropic", "claude", "gemini",
        "open source", "funding", "acquisition",
    ]:
        count = all_titles.count(kw)
        if count > 0:
            keyword_counts[kw] = count

    if keyword_counts:
        lines.append("🔑 トレンドキーワード")
        lines.append("-" * 40)
        for kw, count in keyword_counts.most_common(10):
            bar = "█" * min(count, 20)
            lines.append(f"  {kw:20s} {bar} ({count})")
        lines.append("")

    return "\n".join(lines)


def build_monthly_report(
    items: List[Dict], start: date, end: date, year: int, month: int
) -> str:
    """Build monthly summary report."""
    lines = []

    lines.append(f"📊 月次AIニュースレポート（{year}年{month}月）")
    lines.append("=" * 60)
    lines.append("")

    # Overview stats
    dates = set(item["_date"] for item in items)
    categories = Counter(item.get("category", "Other") for item in items)
    scores = [item.get("score", 0) for item in items]
    avg_score = sum(scores) / len(scores) if scores else 0

    lines.append("📈 月次概要")
    lines.append(f"  総記事数: {len(items)}件（{len(dates)}日分）")
    lines.append(f"  平均スコア: {avg_score:.1f}")
    lines.append(f"  最高スコア: {max(scores) if scores else 0}")
    lines.append("")

    # Category distribution
    lines.append("📂 カテゴリ分布")
    total = len(items) or 1
    for cat, count in categories.most_common():
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        lines.append(f"  {cat:20s} {bar} {pct:.0f}% ({count}件)")
    lines.append("")

    # Top 20 of the month
    top_items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)[:20]
    lines.append("🏆 今月のTOP 20")
    lines.append("-" * 40)
    for i, item in enumerate(top_items, 1):
        score = item.get("score", 0)
        title = item.get("title", "")
        d = item.get("_date", "")
        lines.append(f"  {i:2d}. [{score}] {title} ({d})")
    lines.append("")

    # Weekly breakdown
    lines.append("📅 週別推移")
    lines.append("-" * 40)
    by_week: Dict[int, List] = defaultdict(list)
    for item in items:
        try:
            d = date.fromisoformat(item["_date"])
            week_num = d.isocalendar()[1]
            by_week[week_num].append(item)
        except Exception:
            pass

    for week_num in sorted(by_week.keys()):
        week_items = by_week[week_num]
        week_scores = [i.get("score", 0) for i in week_items]
        avg = sum(week_scores) / len(week_scores) if week_scores else 0
        high = len([s for s in week_scores if s >= 80])
        lines.append(f"  W{week_num}: {len(week_items)}件 / 平均{avg:.0f}点 / 高スコア{high}件")
    lines.append("")

    # AI model mentions trend
    lines.append("🔑 月間トレンドキーワード")
    lines.append("-" * 40)
    all_text = " ".join(
        (item.get("title", "") + " " + item.get("summary", "")).lower() for item in items
    )
    keyword_counts: Counter = Counter()
    for kw in [
        "openai", "google", "anthropic", "meta", "nvidia", "microsoft",
        "claude", "gemini", "gpt", "llama", "mistral", "deepseek",
        "agent", "open source", "benchmark", "funding", "acquisition",
        "regulation", "safety", "gpu",
    ]:
        count = all_text.count(kw)
        if count > 0:
            keyword_counts[kw] = count

    for kw, count in keyword_counts.most_common(15):
        bar = "█" * min(count, 30)
        lines.append(f"  {kw:20s} {bar} ({count})")
    lines.append("")

    return "\n".join(lines)
