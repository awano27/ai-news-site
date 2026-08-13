#!/usr/bin/env python3
"""
Build a formal ranking HTML report from the preview input text
presentations/ai_ranking_input_latest.txt using RankingReportGenerator.

Outputs:
  - presentations/ai_ranking_report_YYYYMMDD.html
  - presentations/ai_ranking_report_latest.html (alias)
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add repo root to path so `src.*` imports resolve as a package.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.generators.ranking_report_generator import RankingReportGenerator  # type: ignore

REPORT_TITLE = "AIニューステクノロジーランキング・レポート"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build ranking HTML from preview input")
    parser.add_argument(
        "--output-date",
        default=None,
        help="Pin dated output as YYYYMMDD (default: local clock)",
    )
    args = parser.parse_args(argv)

    input_file = ROOT / "presentations" / "ai_ranking_input_latest.txt"
    if not input_file.exists():
        print("Input not found:", input_file)
        return 1

    gen = RankingReportGenerator(
        templates_dir=str(ROOT / "templates"),
        output_dir=str(ROOT / "presentations"),
    )
    title = REPORT_TITLE
    out = gen.generate_ranking_report(str(input_file), title)
    if not out:
        print("Failed to generate report")
        return 2

    out_path = Path(out)
    wanted_date = args.output_date or datetime.now().strftime("%Y%m%d")
    wanted = ROOT / "presentations" / f"ai_ranking_report_{wanted_date}.html"
    html = out_path.read_text(encoding="utf-8")
    if out_path.resolve() != wanted.resolve():
        html = html.replace(out_path.name, wanted.name)
        wanted.write_text(html, encoding="utf-8")
        print("Renamed dated report to:", wanted)
    else:
        wanted.write_text(html, encoding="utf-8")

    # Copy to latest alias with self-canonical (never keep dated canonical/og:url)
    latest = ROOT / "presentations" / "ai_ranking_report_latest.html"
    dated_url = f"https://visionhub.jp/presentations/{wanted.name}"
    latest_url = "https://visionhub.jp/presentations/ai_ranking_report_latest.html"
    latest.write_text(html.replace(dated_url, latest_url), encoding="utf-8")
    print("Latest alias updated:", latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
