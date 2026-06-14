"""
RankingReportGenerator: AIニュースランキング用レポート生成クラス

improved-requirements-doc.htmlのデザインフォーマットを使用して
AIニュースランキングデータからプロフェッショナルなレポートを生成
"""

from datetime import datetime
from pathlib import Path

from jinja2 import Template, select_autoescape

from src.utils.sanitize import sanitize_html

# Re-export public symbols so existing callers are unaffected
from .ranking_data_parser import (
    parse_ranking_data,
    analyze_ranking_metrics,
    prepare_ranking_chart_data,
)
from .ranking_template import get_template_string


class RankingReportGenerator:
    """AIニュースランキング専用レポート生成クラス"""

    def __init__(self, templates_dir: str = "templates", output_dir: str = "presentations"):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_ranking_data(self, file_path: str):
        return parse_ranking_data(file_path)

    def analyze_ranking_metrics(self, data):
        return analyze_ranking_metrics(data)

    def generate_ranking_report(self, data_file: str, report_title: str = None) -> str:
        """improved-requirements-doc.htmlスタイルのランキングレポート生成"""
        data = self.parse_ranking_data(data_file)
        if not data:
            return ""

        analysis = self.analyze_ranking_metrics(data)

        template_data = {
            "title": report_title or "AI技術トレンドランキング・レポート",
            "period_start": data["period_start"],
            "period_end": data["period_end"],
            "generation_timestamp": datetime.now().strftime("%Y年%m月%d日 %H:%M"),
            "ranking_items": data["ranking_items"],
            "key_points": data["key_points"],
            "sectors": data["sectors"],
            "total_items": data["total_items"],
            "analysis": analysis,
            "score_stats": analysis.get("score_stats", {}),
            "categories": analysis.get("categories", {}),
            "top_performers": analysis.get("top_performers", {}),
            "impact_distribution": analysis.get("impact_distribution", {}),
            "chart_data": prepare_ranking_chart_data(data, analysis),
        }

        template_content = get_template_string()
        template = Template(template_content, autoescape=select_autoescape(["html", "xml"]))

        try:
            html_content = template.render(**template_data)
            html_content = sanitize_html(html_content)

            output_file = self.output_dir / f"ai_ranking_report_{datetime.now().strftime('%Y%m%d')}.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"✅ AI Ranking Report generated: {output_file}")
            return str(output_file)

        except Exception as e:
            print(f"❌ Error generating ranking report: {e}")
            import traceback
            print(traceback.format_exc())
            return ""

    # ---------------------------------------------------------------------------
    # Backward-compat shims for callers using private names on the class instance
    # ---------------------------------------------------------------------------
    _prepare_ranking_chart_data = staticmethod(prepare_ranking_chart_data)
    _get_requirements_doc_style_template = staticmethod(get_template_string)


def main():
    """メイン関数"""
    generator = RankingReportGenerator()

    input_file = r"C:\Users\yoshitaka\input\20250826AIニュースランキング 直近1ヶ月間のトップ30.txt"
    result = generator.generate_ranking_report(
        input_file,
        "AIニューステクノロジーランキング・レポート 2025",
    )

    if result:
        print(f"🎉 AI Ranking Report generated: {result}")
        print(f"🌐 ブラウザで開く: file://{Path(result).absolute()}")
    else:
        print("❌ Report generation failed")


if __name__ == "__main__":
    main()
