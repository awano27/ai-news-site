from src.generators.advanced_schema_generator import AdvancedSchemaGenerator
from src.generators.ranking_report_generator import RankingReportGenerator
from src.generators.daily_news_generator import DailyNewsGenerator
import os

def rebuild_reports():
    input_file = r"C:\develop\ai-news-site\input\20250826.txt"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    # 1. Advanced Intelligence Report
    print("Generating Advanced Intelligence Report...")
    adv_gen = AdvancedSchemaGenerator()
    adv_gen.generate_advanced_intelligence_report(input_file)

    # 2. Ranking Report
    print("Generating Ranking Report...")
    rank_gen = RankingReportGenerator()
    rank_gen.generate_ranking_report(input_file, "ai_ranking_report_20250826.html")

    # 3. Daily News Report
    print("Generating Daily News Report...")
    daily_gen = DailyNewsGenerator()
    daily_gen.generate_daily_news_report(input_file, "daily_ai_news_report_20250826.html")

if __name__ == "__main__":
    rebuild_reports()
