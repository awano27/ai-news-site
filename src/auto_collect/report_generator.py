#!/usr/bin/env python3
"""
report_generator.py — Orchestrator for weekly/monthly AI news reports.

Heavy lifting is delegated to:
  report_data_loader.py  — load_date_range, parse_day_txt
  report_llm_builder.py  — build_weekly_report, build_monthly_report

Public symbols kept in this file (run_daily.sh calls them as module functions):
  ReportGenerator, generate_weekly_report, generate_monthly_report
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from .config import PROJECT_ROOT
from .report_data_loader import load_date_range
from .report_llm_builder import build_weekly_report, build_monthly_report

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate weekly and monthly summary reports from daily news."""

    def __init__(self):
        self.news_dir = PROJECT_ROOT / "public-pages" / "news"
        self.report_dir = PROJECT_ROOT / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_weekly(self, end_date: Optional[date] = None) -> Optional[Path]:
        """Generate weekly report (last 7 days)."""
        if end_date is None:
            end_date = date.today()
        start_date = end_date - timedelta(days=6)

        logger.info(f"[Weekly] Generating report: {start_date} ~ {end_date}")

        all_items = load_date_range(self.news_dir, start_date, end_date)

        if not all_items:
            logger.warning("[Weekly] No data found for the period")
            return None

        report = build_weekly_report(all_items, start_date, end_date)

        filename = f"weekly_{end_date.strftime('%Y%m%d')}.txt"
        output_path = self.report_dir / filename
        output_path.write_text(report, encoding="utf-8")

        logger.info(f"[Weekly] Report saved: {output_path}")
        return output_path

    def generate_monthly(self, year: int = None, month: int = None) -> Optional[Path]:
        """Generate monthly report."""
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        if end_date > today:
            end_date = today

        logger.info(f"[Monthly] Generating report: {start_date} ~ {end_date}")

        all_items = load_date_range(self.news_dir, start_date, end_date)

        if not all_items:
            logger.warning("[Monthly] No data found")
            return None

        report = build_monthly_report(all_items, start_date, end_date, year, month)

        filename = f"monthly_{year}{month:02d}.txt"
        output_path = self.report_dir / filename
        output_path.write_text(report, encoding="utf-8")

        logger.info(f"[Monthly] Report saved: {output_path}")
        return output_path

    # Backward-compat private-name aliases (callers outside this module)
    _load_date_range = staticmethod(lambda self_unused, s, e: load_date_range(None, s, e))
    _build_weekly_report = staticmethod(build_weekly_report)
    _build_monthly_report = staticmethod(build_monthly_report)


def generate_weekly_report():
    """CLI entry point for weekly report (called by run_daily.sh)."""
    logging.basicConfig(level=logging.INFO)
    gen = ReportGenerator()
    path = gen.generate_weekly()
    if path:
        print(f"Weekly report: {path}")
        print(path.read_text(encoding="utf-8"))


def generate_monthly_report():
    """CLI entry point for monthly report (called by run_daily.sh)."""
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
