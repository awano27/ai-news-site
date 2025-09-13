#!/usr/bin/env python3
"""
Build a formal ranking HTML report from the preview input text
presentations/ai_ranking_input_latest.txt using RankingReportGenerator.

Outputs:
  - presentations/ai_ranking_report_YYYYMMDD.html
  - presentations/ai_ranking_report_latest.html (alias)
"""
import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from generators.ranking_report_generator import RankingReportGenerator  # type: ignore


def main() -> int:
    input_file = ROOT / 'presentations' / 'ai_ranking_input_latest.txt'
    if not input_file.exists():
        print('Input not found:', input_file)
        return 1

    gen = RankingReportGenerator(templates_dir=str(ROOT / 'templates'),
                                 output_dir=str(ROOT / 'presentations'))
    title = 'AIニューステクノロジーランキング・レポート（プレビュー）'
    out = gen.generate_ranking_report(str(input_file), title)
    if not out:
        print('Failed to generate report')
        return 2
    # Copy to latest alias
    latest = ROOT / 'presentations' / 'ai_ranking_report_latest.html'
    latest.write_text(Path(out).read_text(encoding='utf-8'), encoding='utf-8')
    print('Latest alias updated:', latest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
