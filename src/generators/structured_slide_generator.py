"""
StructuredSlideGenerator: 構造化データ用スライド生成クラス

20250826.txt のような構造化されたAIニュースデータから
HTMLプレゼンテーションを生成します。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from src.utils.sanitize import sanitize_html


class StructuredSlideGenerator:
    """構造化データからHTMLスライドを生成するクラス"""
    
    def __init__(self, templates_dir: str = "templates", output_dir: str = "presentations"):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        
        # 出力ディレクトリの作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # テンプレートエンジンの初期化
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def load_structured_data(self, file_path: str) -> Dict[str, Any]:
        """構造化データファイルを読み込む"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # JSONパート（最初の}まで）を抽出
            json_end = content.find('\n}') + 2
            if json_end == 1:  # \n}が見つからない場合
                json_end = content.find('}') + 1
            
            json_str = content[:json_end]
            data = json.loads(json_str)
            
            return data
            
        except Exception as e:
            print(f"Error loading structured data: {e}")
            return {}
    
    def generate_comprehensive_presentation(self, data_file: str, 
                                         presentation_title: str = None) -> str:
        """包括的なプレゼンテーションを生成"""
        
        # データの読み込み
        data = self.load_structured_data(data_file)
        if not data:
            return ""
        
        # 基本情報の抽出
        date_indexed = data.get('date_indexed', 'Unknown')
        items = data.get('items', [])
        themes = data.get('themes', [])
        daily_top = data.get('daily_top', [])
        narrative = data.get('narrative', '')
        
        # プレゼンテーション用データの準備
        template_data = {
            'title': presentation_title or f'AIニュース分析レポート - {date_indexed}',
            'date_indexed': date_indexed,
            'date_formatted': self._format_japanese_date(date_indexed),
            'total_items': len(items),
            'themes': themes,
            'top_items': sorted(items, key=lambda x: x.get('impact_score', 0), reverse=True)[:10],
            'daily_highlights': daily_top[:10] if daily_top else [],
            'narrative': narrative,
            'generation_timestamp': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
            'chart_data': self._prepare_chart_data(items, themes)
        }
        
        # カスタムテンプレートの作成（インラインで定義）
        template_content = self._get_comprehensive_template()
        template = Template(template_content, autoescape=select_autoescape(['html', 'xml']))
        
        try:
            # HTMLの生成
            html_content = template.render(**template_data)
            html_content = sanitize_html(html_content)
            
            # ファイル出力
            output_file = self.output_dir / f"structured_presentation_{date_indexed}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Comprehensive presentation generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"❌ Error generating presentation: {e}")
            return ""
    
    def _prepare_chart_data(self, items: List[Dict], themes: List[Dict]) -> Dict:
        """チャート用データの準備"""
        
        # インパクトスコア分布
        impact_scores = [item.get('impact_score', 0) for item in items]
        score_ranges = {'0-50': 0, '51-70': 0, '71-85': 0, '86-95': 0, '96-100': 0}
        
        for score in impact_scores:
            if score <= 50:
                score_ranges['0-50'] += 1
            elif score <= 70:
                score_ranges['51-70'] += 1
            elif score <= 85:
                score_ranges['71-85'] += 1
            elif score <= 95:
                score_ranges['86-95'] += 1
            else:
                score_ranges['96-100'] += 1
        
        # テーマ別統計
        theme_data = {}
        for theme in themes:
            theme_name = theme.get('theme', 'その他')
            theme_data[theme_name] = len(theme.get('top3', []))
        
        return {
            'impact_labels': json.dumps(list(score_ranges.keys())),
            'impact_values': json.dumps(list(score_ranges.values())),
            'theme_labels': json.dumps(list(theme_data.keys())),
            'theme_values': json.dumps(list(theme_data.values())),
            'avg_impact': sum(impact_scores) / len(impact_scores) if impact_scores else 0
        }
    
    def _format_japanese_date(self, date_str: str) -> str:
        """日付を日本語形式にフォーマット"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%Y年%m月%d日')
        except:
            return date_str
    
    def _get_comprehensive_template(self) -> str:
        """包括的なプレゼンテーションテンプレートを返す"""
        return '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    
    <!-- Reveal.js CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.0.4/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.0.4/dist/theme/white.css">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    
    <style>
        .reveal .slides section { text-align: left; }
        .reveal h1, .reveal h2 { text-align: center; color: #007acc; }
        .highlight-box { background: #f0f8ff; border-left: 4px solid #007acc; padding: 15px; margin: 15px 0; }
        .success-box { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; }
        .warning-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }
        .article-card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .score-badge { background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; float: right; }
        .theme-card { background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 10px 0; border-left: 3px solid #007acc; }
        .chart-container { position: relative; height: 350px; margin: 20px 0; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007acc; }
        .daily-item { padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; border-left: 3px solid #28a745; }
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            
            <!-- タイトルスライド -->
            <section>
                <h1>🤖 {{ title }}</h1>
                <div class="highlight-box">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{{ total_items }}</div>
                            <div>分析記事数</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ themes|length }}</div>
                            <div>主要テーマ数</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ "%.1f"|format(chart_data.avg_impact) }}</div>
                            <div>平均インパクト</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ daily_highlights|length }}</div>
                            <div>日次ハイライト</div>
                        </div>
                    </div>
                    <p><strong>分析日時:</strong> {{ date_formatted }} | <strong>生成:</strong> {{ generation_timestamp }}</p>
                </div>
            </section>

            <!-- インパクト分析 -->
            <section>
                <h2>📊 インパクト分析</h2>
                <div class="chart-container">
                    <canvas id="impactChart"></canvas>
                </div>
                <div class="highlight-box">
                    <h3>インパクト評価の分布</h3>
                    <p>総計<strong>{{ total_items }}件</strong>の記事を分析し、影響度を5段階で評価</p>
                    <p>平均インパクトスコア: <strong>{{ "%.1f"|format(chart_data.avg_impact) }}</strong>/100</p>
                </div>
            </section>

            <!-- テーマ分析 -->
            <section>
                <h2>🏷️ 主要テーマ分析</h2>
                <div class="chart-container">
                    <canvas id="themeChart"></canvas>
                </div>
                {% for theme in themes[:4] %}
                <div class="theme-card">
                    <h3>{{ theme.theme }}</h3>
                    <p>{{ theme.slide_overview }}</p>
                    <ul>
                        {% for item in theme.top3 %}
                        <li>{{ item }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endfor %}
            </section>

            <!-- 高インパクト記事 Top5 -->
            <section>
                <h2>🌟 高インパクト記事 Top 5</h2>
                {% for item in top_items[:5] %}
                <div class="article-card">
                    <div class="score-badge">{{ item.impact_score }}</div>
                    <h3>{{ item.slide_meta.title }}</h3>
                    <p><strong>要約:</strong> {{ item.summary }}</p>
                    <div class="success-box">
                        <strong>キーメッセージ:</strong>
                        <ul>
                            {% for message in item.slide_meta.key_messages %}
                            <li>{{ message }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    <p><small><strong>出典:</strong> {{ item.metadata.author }} ({{ item.metadata.date }})</small></p>
                </div>
                {% endfor %}
            </section>

            <!-- 個別記事詳細スライド -->
            {% for item in top_items[:3] %}
            <section>
                <h2>📰 {{ item.slide_meta.title }}</h2>
                <div class="article-card">
                    <div class="score-badge">{{ item.impact_score }}</div>
                    <h3>詳細分析</h3>
                    
                    <div class="highlight-box">
                        <p><strong>要約:</strong> {{ item.summary }}</p>
                    </div>
                    
                    <div class="success-box">
                        <h4>キーポイント:</h4>
                        <ul>
                            {% for bullet in item.bullets %}
                            <li>{{ bullet }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    
                    <div class="warning-box">
                        <p><strong>技術評価:</strong> {{ item.tech_eval }}</p>
                        <p><strong>信頼性:</strong> {{ item.reliability }}</p>
                    </div>
                    
                    {% if item.slide_meta.speaker_notes %}
                    <div class="highlight-box">
                        <p><strong>スピーカーノート:</strong> {{ item.slide_meta.speaker_notes }}</p>
                    </div>
                    {% endif %}
                    
                    <p><small><strong>出典:</strong> 
                    {% for source in item.sources %}
                    <a href="{{ source }}" target="_blank">{{ loop.index }}</a>{{ " " }}
                    {% endfor %}
                    </small></p>
                </div>
            </section>
            {% endfor %}

            <!-- 日次ハイライト -->
            <section>
                <h2>📅 期間中の主要ハイライト</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    {% for daily in daily_highlights %}
                    <div class="daily-item">
                        <strong>{{ daily.date }}:</strong><br>
                        {{ daily.top }}
                    </div>
                    {% endfor %}
                </div>
            </section>

            <!-- ナラティブ & まとめ -->
            <section>
                <h2>📝 分析ナラティブ</h2>
                <div class="highlight-box">
                    <h3>期間総括</h3>
                    <p>{{ narrative }}</p>
                </div>
                
                <div class="success-box">
                    <h3>🎯 キー・インサイト</h3>
                    <ul>
                        <li>{{ total_items }}件の記事から厳選された高インパクト情報</li>
                        <li>{{ themes|length }}の主要テーマにわたる包括的分析</li>
                        <li>平均インパクトスコア {{ "%.1f"|format(chart_data.avg_impact) }}の質の高い情報</li>
                        <li>技術革新から実用化まで幅広いカバレッジ</li>
                    </ul>
                </div>
                
                <div class="warning-box">
                    <h3>🔍 注目ポイント</h3>
                    <ul>
                        <li>オープンソースLLMの活発なリリース動向</li>
                        <li>特定領域（宇宙天気予報など）への特化型モデル展開</li>
                        <li>評価ベンチマークの進化と実用性向上</li>
                        <li>AI安全性・倫理に関する議論の深化</li>
                    </ul>
                </div>
            </section>

        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.0.4/dist/reveal.js"></script>
    <script>
        Reveal.initialize({
            hash: true,
            transition: 'slide',
            controls: true,
            progress: true,
            center: true
        });

        // インパクト分析チャート
        const impactCtx = document.getElementById('impactChart').getContext('2d');
        new Chart(impactCtx, {
            type: 'doughnut',
            data: {
                labels: {{ chart_data.impact_labels|safe }},
                datasets: [{
                    data: {{ chart_data.impact_values|safe }},
                    backgroundColor: ['#dc3545', '#ffc107', '#28a745', '#007acc', '#6f42c1']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: 'インパクトスコア分布' }
                }
            }
        });

        // テーマ分析チャート
        const themeCtx = document.getElementById('themeChart').getContext('2d');
        new Chart(themeCtx, {
            type: 'bar',
            data: {
                labels: {{ chart_data.theme_labels|safe }},
                datasets: [{
                    label: '記事数',
                    data: {{ chart_data.theme_values|safe }},
                    backgroundColor: '#007acc'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: 'テーマ別記事数' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>'''


# 使用例
def main():
    """メイン関数 - 実際に使用する場合"""
    generator = StructuredSlideGenerator()
    
    # 構造化データからプレゼンテーション生成
    input_file = r"C:\Users\yoshitaka\input\20250826.txt"
    result = generator.generate_comprehensive_presentation(
        input_file, 
        "AIニュース インテリジェンス・レポート 2025-08-26"
    )
    
    if result:
        print(f"🎉 プレゼンテーション生成完了: {result}")
        print(f"🌐 ブラウザで開く: file://{Path(result).absolute()}")
    else:
        print("❌ プレゼンテーション生成に失敗しました")


if __name__ == "__main__":
    main()
