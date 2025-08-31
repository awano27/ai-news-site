"""
Generate latest AI ranking report from presentations/ai_ranking_input_latest.txt

This script uses RankingReportGenerator's parsing/analysis and renders the
embedded template directly, skipping sanitize() to avoid brittle failures.
It outputs a dated report and updates ai_ranking_report_latest.html.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from jinja2 import Template, select_autoescape
import re

from src.generators.ranking_report_generator import RankingReportGenerator


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / "presentations" / "ai_ranking_input_latest.txt"
    out_dir = repo_root / "presentations"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Input not found: {input_path}")
        return 2

    gen = RankingReportGenerator(templates_dir=str(repo_root / "templates"),
                                 output_dir=str(out_dir))

    # Parse and analyze using existing methods
    data = gen.parse_ranking_data(str(input_path))
    if not data:
        print("Failed to parse ranking data. Aborting.")
        return 3

    analysis = gen.analyze_ranking_metrics(data)

    # Prepare template data (mirrors generator implementation)
    # Override period to "last 30 days from today" for clarity
    today = datetime.now()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    # Use 30 days as an approximation of 1 month
    from datetime import timedelta
    start_30 = start - timedelta(days=30)

    template_data = {
        'title': 'AIニューステクノロジーランキング・レポート',
        'period_start': start_30.strftime('%Y年%m月%d日'),
        'period_end': today.strftime('%Y年%m月%d日'),
        'generation_timestamp': datetime.now().strftime('%Y年%m月%d日 %H:%M'),

        'ranking_items': data['ranking_items'],
        'key_points': data['key_points'],
        'sectors': data['sectors'],
        'total_items': data['total_items'],

        'analysis': analysis,
        'score_stats': analysis.get('score_stats', {}),
        'categories': analysis.get('categories', {}),
        'top_performers': analysis.get('top_performers', {}),
        'impact_distribution': analysis.get('impact_distribution', {}),

        'chart_data': gen._prepare_ranking_chart_data(data, analysis),
    }

    # Render using the embedded template
    template_content = gen._get_requirements_doc_style_template()
    template = Template(template_content, autoescape=select_autoescape(['html', 'xml']))
    html = template.render(**template_data)

    # Normalize footer generation timestamp and item count in <p id="gen-ts">...</p>
    footer_text = f"{template_data['generation_timestamp']} | Based on {template_data['total_items']} AI technologies analysis"
    html = re.sub(r'(\<p id="gen-ts"\>).*?(\</p\>)', rf"\1{footer_text}\2", html, flags=re.S)

    # Write outputs
    dated = out_dir / f"ai_ranking_report_{datetime.now().strftime('%Y%m%d')}.html"
    latest = out_dir / "ai_ranking_report_latest.html"
    dated.write_text(html, encoding='utf-8')
    latest.write_text(html, encoding='utf-8')

    print(f"Generated: {dated}")
    print(f"Updated : {latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
