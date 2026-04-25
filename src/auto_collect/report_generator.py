#!/usr/bin/env python3
"""
Weekly and Monthly AI News Report Generator.
Aggregates daily input/day/MMDD.txt files into summary reports.
"""

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import requests

from .config import PROJECT_ROOT, INPUT_DAY_DIR, OLLAMA_CHAT_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate weekly and monthly summary reports from daily news."""

    def __init__(self):
        self.news_dir = PROJECT_ROOT / "public-pages" / "news"
        self.report_dir = PROJECT_ROOT / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_weekly(self, end_date: Optional[date] = None) -> Path:
        """Generate weekly report (last 7 days)."""
        if end_date is None:
            end_date = date.today()
        start_date = end_date - timedelta(days=6)

        logger.info(f"[Weekly] Generating report: {start_date} ~ {end_date}")

        # Collect all daily data
        all_items = self._load_date_range(start_date, end_date)

        if not all_items:
            logger.warning("[Weekly] No data found for the period")
            return None

        report = self._build_weekly_report(all_items, start_date, end_date)

        # Write report
        filename = f"weekly_{end_date.strftime('%Y%m%d')}.txt"
        output_path = self.report_dir / filename
        output_path.write_text(report, encoding="utf-8")

        logger.info(f"[Weekly] Report saved: {output_path}")
        return output_path

    def generate_monthly(self, year: int = None, month: int = None) -> Path:
        """Generate monthly report."""
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        # Calculate date range
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # Don't go past today
        if end_date > today:
            end_date = today

        logger.info(f"[Monthly] Generating report: {start_date} ~ {end_date}")

        all_items = self._load_date_range(start_date, end_date)

        if not all_items:
            logger.warning("[Monthly] No data found")
            return None

        report = self._build_monthly_report(all_items, start_date, end_date, year, month)

        filename = f"monthly_{year}{month:02d}.txt"
        output_path = self.report_dir / filename
        output_path.write_text(report, encoding="utf-8")

        logger.info(f"[Monthly] Report saved: {output_path}")
        return output_path

    def _load_date_range(self, start: date, end: date) -> List[Dict]:
        """Load news items from JSON archives for a date range."""
        all_items = []
        current = start

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")

            # Try JSON archive first
            json_path = self.news_dir / f"{date_str}.json"
            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text(encoding="utf-8"))
                    items = data.get("items", [])
                    for item in items:
                        item["_date"] = date_str
                    all_items.extend(items)
                except Exception as e:
                    logger.warning(f"[Report] Failed to load {json_path}: {e}")

            # Also try input/day/MMDD.txt for sections
            mmdd = current.strftime("%m%d")
            txt_path = INPUT_DAY_DIR / f"{mmdd}.txt"
            if txt_path.exists() and not json_path.exists():
                try:
                    content = txt_path.read_text(encoding="utf-8")
                    parsed = self._parse_day_txt(content, date_str)
                    all_items.extend(parsed)
                except Exception as e:
                    logger.warning(f"[Report] Failed to parse {txt_path}: {e}")

            current += timedelta(days=1)

        return all_items

    def _parse_day_txt(self, content: str, date_str: str) -> List[Dict]:
        """Parse a day txt file into items."""
        items = []
        current_title = ""
        current_score = 0
        current_category = ""
        current_lines = []

        for line in content.split("\n"):
            if line.startswith("■ "):
                # Save previous item
                if current_title:
                    items.append({
                        "title": current_title,
                        "score": current_score,
                        "category": current_category,
                        "summary": " ".join(current_lines),
                        "_date": date_str,
                    })

                # Parse new item
                match = re.match(r'■ (.+?)（(.+?) / スコア: (\d+)）', line)
                if match:
                    current_title = match.group(1)
                    current_category = match.group(2)
                    current_score = int(match.group(3))
                else:
                    current_title = line[2:].strip()
                    current_score = 50
                    current_category = "AI Technology"
                current_lines = []
            elif line.strip() and not line.startswith("=") and not line.startswith("📰") \
                    and not line.startswith("💰") and not line.startswith("🔥") \
                    and not line.startswith("🤗"):
                current_lines.append(line.strip())

        # Save last item
        if current_title:
            items.append({
                "title": current_title,
                "score": current_score,
                "category": current_category,
                "summary": " ".join(current_lines),
                "_date": date_str,
            })

        return items

    def _build_weekly_report(self, items: List[Dict], start: date, end: date) -> str:
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

        lines.append(f"📈 概要統計")
        lines.append(f"  記事総数: {len(items)}件（{len(dates_covered)}日分）")
        lines.append(f"  高スコア記事（80+）: {len(high_score)}件")
        lines.append(f"  カテゴリ分布:")
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
        by_category = defaultdict(list)
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
        keyword_counts = Counter()
        for kw in ["ai", "gpt", "llm", "agent", "model", "openai", "google",
                    "nvidia", "meta", "anthropic", "claude", "gemini",
                    "open source", "funding", "acquisition"]:
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

    def _build_monthly_report(self, items: List[Dict], start: date, end: date,
                               year: int, month: int) -> str:
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
        by_week = defaultdict(list)
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
            (item.get("title", "") + " " + item.get("summary", "")).lower()
            for item in items
        )
        keyword_counts = Counter()
        for kw in ["openai", "google", "anthropic", "meta", "nvidia", "microsoft",
                    "claude", "gemini", "gpt", "llama", "mistral", "deepseek",
                    "agent", "open source", "benchmark", "funding", "acquisition",
                    "regulation", "safety", "gpu"]:
            count = all_text.count(kw)
            if count > 0:
                keyword_counts[kw] = count

        for kw, count in keyword_counts.most_common(15):
            bar = "█" * min(count, 30)
            lines.append(f"  {kw:20s} {bar} ({count})")
        lines.append("")

        return "\n".join(lines)


def generate_weekly_report():
    """CLI entry point for weekly report."""
    logging.basicConfig(level=logging.INFO)
    gen = ReportGenerator()
    path = gen.generate_weekly()
    if path:
        print(f"Weekly report: {path}")
        print(path.read_text(encoding="utf-8"))


def generate_monthly_report():
    """CLI entry point for monthly report."""
    logging.basicConfig(level=logging.INFO)
    gen = ReportGenerator()
    path = gen.generate_monthly()
    if path:
        print(f"Monthly report: {path}")
        print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "monthly":
        generate_monthly_report()
    else:
        generate_weekly_report()
