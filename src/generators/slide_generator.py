"""
SlideGenerator: AI News Presentation Generator

Generates monthly HTML presentation slides from daily AI news data
using Reveal.js framework with Chart.js for visualizations.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import calendar

from jinja2 import Environment, FileSystemLoader, select_autoescape


class SlideGenerator:
    """HTMLスライド生成クラス"""
    
    def __init__(self, news_dir: str = "news", templates_dir: str = "templates", 
                 output_dir: str = "presentations"):
        self.news_dir = Path(news_dir)
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        
        # テンプレートエンジンの初期化
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # 出力ディレクトリの作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_monthly_data(self, year: int, month: int) -> List[Dict]:
        """指定月の全ニュースデータを読み込み"""
        monthly_data = []
        
        # 月の日数を計算
        _, last_day = calendar.monthrange(year, month)
        
        for day in range(1, last_day + 1):
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            news_file = self.news_dir / f"{date_str}.json"
            
            if news_file.exists():
                try:
                    with open(news_file, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)
                        # 日付情報を追加
                        for item in daily_data:
                            item['date'] = date_str
                        monthly_data.extend(daily_data)
                except Exception as e:
                    print(f"Warning: Failed to load {news_file}: {e}")
        
        return monthly_data
    
    def analyze_monthly_trends(self, data: List[Dict]) -> Dict:
        """月次トレンド分析"""
        # カテゴリ別集計
        categories = Counter()
        sources = Counter()
        daily_counts = defaultdict(int)
        high_quality_articles = []
        
        for item in data:
            # カテゴリ分析（仮の実装）
            title_lower = item.get('title', '').lower()
            if 'llm' in title_lower or 'language model' in title_lower:
                categories['LLM・言語モデル'] += 1
            elif 'vision' in title_lower or 'cv' in title_lower or 'image' in title_lower:
                categories['コンピュータビジョン'] += 1
            elif 'robotics' in title_lower or 'robot' in title_lower:
                categories['ロボティクス'] += 1
            elif 'agent' in title_lower or 'autonomous' in title_lower:
                categories['AIエージェント'] += 1
            else:
                categories['その他'] += 1
            
            # ソース集計
            source = item.get('source', 'Unknown')
            sources[source] += 1
            
            # 日別集計
            date = item.get('date', '')
            daily_counts[date] += 1
            
            # 高品質記事の選定（スコアが高い記事）
            total_score = item.get('evaluation', {}).get('overall_score', 0)
            if total_score > 0.8:  # 閾値は調整可能
                high_quality_articles.append(item)
        
        return {
            'categories': dict(categories.most_common()),
            'sources': dict(sources.most_common(10)),
            'daily_counts': dict(daily_counts),
            'high_quality_articles': sorted(high_quality_articles, 
                                           key=lambda x: x.get('evaluation', {}).get('overall_score', 0), 
                                           reverse=True)[:10],
            'total_articles': len(data),
            'average_daily': len(data) / max(len(daily_counts), 1)
        }
    
    def generate_monthly_slides(self, year: int, month: int) -> str:
        """月次レポートスライドの生成"""
        # データ読み込みと分析
        monthly_data = self.load_monthly_data(year, month)
        if not monthly_data:
            print(f"No data found for {year}-{month:02d}")
            return ""
        
        trends = self.analyze_monthly_trends(monthly_data)
        
        # テンプレートデータの準備
        template_data = {
            'year': year,
            'month': month,
            'month_name_ja': self._get_japanese_month_name(month),
            'trends': trends,
            'generation_date': datetime.now().strftime('%Y年%m月%d日'),
            'chart_data': {
                'categories': json.dumps(list(trends['categories'].keys())),
                'category_counts': json.dumps(list(trends['categories'].values())),
                'daily_labels': json.dumps(sorted(trends['daily_counts'].keys())),
                'daily_values': json.dumps([trends['daily_counts'].get(date, 0) 
                                          for date in sorted(trends['daily_counts'].keys())])
            }
        }
        
        # テンプレートの読み込みとレンダリング
        try:
            template = self.jinja_env.get_template('monthly_report.html')
            html_content = template.render(**template_data)
            
            # ファイル出力
            output_file = self.output_dir / f"monthly_report_{year:04d}_{month:02d}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Monthly slides generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error generating monthly slides: {e}")
            return ""
    
    def generate_daily_slide(self, date: str) -> str:
        """指定日の日次スライドを生成"""
        news_file = self.news_dir / f"{date}.json"
        
        if not news_file.exists():
            print(f"No data found for {date}")
            return ""
        
        try:
            with open(news_file, 'r', encoding='utf-8') as f:
                daily_data = json.load(f)
            
            # 高品質記事のフィルタリング
            high_quality = [item for item in daily_data 
                           if item.get('evaluation', {}).get('overall_score', 0) > 0.7]
            
            template_data = {
                'date': date,
                'date_formatted': datetime.strptime(date, '%Y-%m-%d').strftime('%Y年%m月%d日'),
                'articles': high_quality[:5],  # 上位5記事
                'total_articles': len(daily_data),
                'high_quality_count': len(high_quality),
                'generation_date': datetime.now().strftime('%Y年%m月%d日')
            }
            
            template = self.jinja_env.get_template('daily_slide.html')
            html_content = template.render(**template_data)
            
            output_file = self.output_dir / f"daily_slide_{date}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Daily slide generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error generating daily slide: {e}")
            return ""
    
    def update_presentation_index(self) -> None:
        """プレゼンテーション一覧のインデックスページを更新"""
        # 生成済みプレゼンテーションのスキャン
        presentations = []
        
        for file_path in self.output_dir.glob("*.html"):
            if file_path.name.startswith("monthly_report_"):
                # monthly_report_2024_08.html 形式を解析
                parts = file_path.stem.split("_")
                if len(parts) >= 3:
                    try:
                        year = int(parts[2])
                        month = int(parts[3])
                        presentations.append({
                            'type': 'monthly',
                            'year': year,
                            'month': month,
                            'month_name': self._get_japanese_month_name(month),
                            'file': file_path.name,
                            'date': f"{year:04d}-{month:02d}"
                        })
                    except ValueError:
                        continue
            elif file_path.name.startswith("daily_slide_"):
                # daily_slide_2024-08-26.html 形式を解析
                date_part = file_path.stem.replace("daily_slide_", "")
                try:
                    date_obj = datetime.strptime(date_part, '%Y-%m-%d')
                    presentations.append({
                        'type': 'daily',
                        'date': date_part,
                        'date_formatted': date_obj.strftime('%Y年%m月%d日'),
                        'file': file_path.name
                    })
                except ValueError:
                    continue
        
        # 日付順でソート
        presentations.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        try:
            template = self.jinja_env.get_template('index.html')
            html_content = template.render(presentations=presentations)
            
            index_file = self.output_dir / "index.html"
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Index updated: {index_file}")
            
        except Exception as e:
            print(f"Error updating index: {e}")
    
    def _get_japanese_month_name(self, month: int) -> str:
        """月番号を日本語月名に変換"""
        month_names = {
            1: "1月", 2: "2月", 3: "3月", 4: "4月", 5: "5月", 6: "6月",
            7: "7月", 8: "8月", 9: "9月", 10: "10月", 11: "11月", 12: "12月"
        }
        return month_names.get(month, f"{month}月")
    
    def generate_current_month_slides(self) -> str:
        """今月のスライドを生成（便利メソッド）"""
        now = datetime.now()
        return self.generate_monthly_slides(now.year, now.month)
    
    def generate_previous_month_slides(self) -> str:
        """先月のスライドを生成（便利メソッド）"""
        now = datetime.now()
        if now.month == 1:
            return self.generate_monthly_slides(now.year - 1, 12)
        else:
            return self.generate_monthly_slides(now.year, now.month - 1)


# 使用例とテスト関数
def main():
    """メイン実行関数"""
    generator = SlideGenerator()
    
    # 今月のスライド生成
    monthly_slide = generator.generate_current_month_slides()
    
    # 今日のスライド生成
    today = datetime.now().strftime('%Y-%m-%d')
    daily_slide = generator.generate_daily_slide(today)
    
    # インデックスページ更新
    generator.update_presentation_index()
    
    if monthly_slide:
        print(f"Generated monthly slide: {monthly_slide}")
    if daily_slide:
        print(f"Generated daily slide: {daily_slide}")


if __name__ == "__main__":
    main()