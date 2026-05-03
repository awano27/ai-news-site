"""
RankingReportGenerator: AIニュースランキング用レポート生成クラス

improved-requirements-doc.htmlのデザインフォーマットを使用して
AIニュースランキングデータからプロフェッショナルなレポートを生成
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from src.utils.sanitize import sanitize_html


class RankingReportGenerator:
    """AIニュースランキング専用レポート生成クラス"""
    
    def __init__(self, templates_dir: str = "templates", output_dir: str = "presentations"):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # テンプレートエンジンの初期化
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def parse_ranking_data(self, file_path: str) -> Dict[str, Any]:
        """ランキングデータファイルを解析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ランキング項目の抽出
            ranking_items = []
            
            # 各ランキング項目を正規表現で抽出
            # 注意: [^.] は \n も含むため、ライン境界を跨いで貪欲にマッチし
            # 全 30 件が 1 件に潰れる事故が起きていた。description / benefits を
            # 改行でアンカーし、1 行 1 エントリで抽出する。
            pattern = r'(\d+)\.\s\*\*([^*]+)\*\*:\s([^.\n]+\.)\sEng Tool:\s(\d+),\sBiz Eff:\s(\d+),\s合計:\s(\d+)\.\s([^\n]+)'
            matches = re.findall(pattern, content)
            
            for match in matches:
                rank, name, description, eng_tool, biz_eff, total, benefits = match
                ranking_items.append({
                    'rank': int(rank),
                    'name': name.strip(),
                    'description': description.strip(),
                    'eng_tool': int(eng_tool),
                    'biz_eff': int(biz_eff),
                    'total_score': int(total),
                    'benefits': benefits.strip()
                })
            
            # メタデータの抽出
            period_match = re.search(r'直近1ヶ月（(.+?)から(.+?)）', content)
            period_start = period_match.group(1) if period_match else "2025年7月27日"
            period_end = period_match.group(2) if period_match else "2025年8月27日"
            
            # キーポイントの抽出
            key_points = []
            if "**キー points:**" in content:
                key_section = content.split("**キー points:**")[1].split("**ランキング概要**")[0]
                for line in key_section.split('\n'):
                    if line.strip().startswith('- '):
                        key_points.append(line.strip()[2:])
            
            # セクター分析の抽出
            sectors = []
            if "| セクター |" in content:
                lines = content.split("| セクター |")[1].split('\n')
                for line in lines[1:]:  # ヘッダー行をスキップ
                    if line.startswith('|') and line.count('|') >= 6:
                        parts = [p.strip() for p in line.split('|')[1:-1]]
                        if len(parts) >= 5:
                            sectors.append({
                                'name': parts[0],
                                'representative': parts[1],
                                'count': int(parts[2]) if parts[2].isdigit() else 0,
                                'avg_score': float(parts[3]) if parts[3].replace('.', '').isdigit() else 0.0,
                                'use_case': parts[4]
                            })
            
            return {
                'period_start': period_start,
                'period_end': period_end,
                'ranking_items': ranking_items,
                'key_points': key_points,
                'sectors': sectors,
                'total_items': len(ranking_items)
            }
            
        except Exception as e:
            print(f"Error parsing ranking data: {e}")
            return {}
    
    def analyze_ranking_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ランキングデータの詳細分析"""
        items = data.get('ranking_items', [])
        
        if not items:
            return {}
        
        # スコア分布分析
        eng_scores = [item['eng_tool'] for item in items]
        biz_scores = [item['biz_eff'] for item in items]
        total_scores = [item['total_score'] for item in items]
        
        # カテゴリ別分類
        categories = defaultdict(list)
        for item in items:
            name = item['name'].lower()
            if any(keyword in name for keyword in ['gpt', 'claude', 'llm', 'model']):
                categories['LLMモデル'].append(item)
            elif any(keyword in name for keyword in ['video', 'image', 'visual', 'genie']):
                categories['ビジュアル・メディア'].append(item)
            elif any(keyword in name for keyword in ['copilot', 'excel', 'pdf', 'productivity']):
                categories['生産性ツール'].append(item)
            else:
                categories['その他・特殊'].append(item)
        
        # トップパフォーマー分析
        top_eng = sorted(items, key=lambda x: x['eng_tool'], reverse=True)[:5]
        top_biz = sorted(items, key=lambda x: x['biz_eff'], reverse=True)[:5]
        top_overall = sorted(items, key=lambda x: x['total_score'], reverse=True)[:10]
        
        # トレンド分析
        high_impact = [item for item in items if item['total_score'] >= 8]
        medium_impact = [item for item in items if 6 <= item['total_score'] < 8]
        low_impact = [item for item in items if item['total_score'] < 6]
        
        return {
            'score_stats': {
                'avg_eng_score': round(sum(eng_scores) / len(eng_scores), 1),
                'avg_biz_score': round(sum(biz_scores) / len(biz_scores), 1),
                'avg_total_score': round(sum(total_scores) / len(total_scores), 1),
                'max_total_score': max(total_scores),
                'min_total_score': min(total_scores)
            },
            'categories': dict(categories),
            'top_performers': {
                'engineering': top_eng,
                'business': top_biz,
                'overall': top_overall
            },
            'impact_distribution': {
                'high': high_impact,
                'medium': medium_impact,
                'low': low_impact
            }
        }
    
    def generate_ranking_report(self, data_file: str, 
                               report_title: str = None) -> str:
        """improved-requirements-doc.htmlスタイルのランキングレポート生成"""
        
        # データの読み込みと解析
        data = self.parse_ranking_data(data_file)
        if not data:
            return ""
        
        # 詳細分析の実行
        analysis = self.analyze_ranking_metrics(data)
        
        # レポート用データの準備
        template_data = {
            'title': report_title or 'AI技術トレンドランキング・レポート',
            'period_start': data['period_start'],
            'period_end': data['period_end'],
            'generation_timestamp': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
            
            # 基本データ
            'ranking_items': data['ranking_items'],
            'key_points': data['key_points'],
            'sectors': data['sectors'],
            'total_items': data['total_items'],
            
            # 分析結果
            'analysis': analysis,
            'score_stats': analysis.get('score_stats', {}),
            'categories': analysis.get('categories', {}),
            'top_performers': analysis.get('top_performers', {}),
            'impact_distribution': analysis.get('impact_distribution', {}),
            
            # チャート用データ
            'chart_data': self._prepare_ranking_chart_data(data, analysis)
        }
        
        # improved-requirements-doc.html スタイルのテンプレート生成
        template_content = self._get_requirements_doc_style_template()
        template = Template(template_content, autoescape=select_autoescape(['html', 'xml']))
        
        try:
            # HTMLの生成
            html_content = template.render(**template_data)
            html_content = sanitize_html(html_content)
            
            # ファイル出力
            output_file = self.output_dir / f"ai_ranking_report_{datetime.now().strftime('%Y%m%d')}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ AI Ranking Report generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"❌ Error generating ranking report: {e}")
            import traceback
            print(traceback.format_exc())
            return ""
    
    def _prepare_ranking_chart_data(self, data: Dict, analysis: Dict) -> Dict:
        """ランキング用チャートデータの準備"""
        items = data.get('ranking_items', [])
        
        # スコア分布
        score_ranges = {'8-9点': 0, '7点': 0, '6点': 0, '5点以下': 0}
        for item in items:
            score = item['total_score']
            if score >= 8:
                score_ranges['8-9点'] += 1
            elif score == 7:
                score_ranges['7点'] += 1
            elif score == 6:
                score_ranges['6点'] += 1
            else:
                score_ranges['5点以下'] += 1
        
        # カテゴリ分布
        categories = analysis.get('categories', {})
        category_data = {name: len(items) for name, items in categories.items()}
        
        # エンジニア vs ビジネス スコア比較（上位10項目）
        top_10 = items[:10]
        eng_scores = [item['eng_tool'] for item in top_10]
        biz_scores = [item['biz_eff'] for item in top_10]
        item_names = [item['name'][:20] + '...' if len(item['name']) > 20 else item['name'] for item in top_10]
        
        return {
            # スコア分布
            'score_labels': json.dumps(list(score_ranges.keys())),
            'score_values': json.dumps(list(score_ranges.values())),
            
            # カテゴリ分布
            'category_labels': json.dumps(list(category_data.keys())),
            'category_values': json.dumps(list(category_data.values())),
            
            # エンジニア vs ビジネス比較
            'comparison_labels': json.dumps(item_names),
            'eng_scores': json.dumps(eng_scores),
            'biz_scores': json.dumps(biz_scores),
            
            # 統計値
            'avg_total_score': analysis.get('score_stats', {}).get('avg_total_score', 0)
        }
    
    def _get_requirements_doc_style_template(self) -> str:
        """improved-requirements-doc.htmlスタイルのテンプレート"""
        return '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        :root {
            --primary: #0f172a;
            --accent: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #020617;
            --light: #f8fafc;
            --border: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--light);
        }

        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100vh;
            background: var(--primary);
            padding: 24px 16px;
            overflow-y: auto;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
            z-index: 1000;
        }

        .sidebar h1 {
            color: white;
            font-size: 1.3rem;
            margin-bottom: 24px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
            padding-bottom: 16px;
        }

        .nav-item {
            color: #94a3b8;
            display: block;
            padding: 8px 12px;
            border-radius: 6px;
            text-decoration: none;
            margin-bottom: 4px;
            transition: all 0.2s;
        }

        .nav-item:hover {
            background: rgba(255,255,255,0.08);
            color: white;
        }

        .nav-item.active {
            background: var(--accent);
            color: white;
        }

        .main-content {
            margin-left: 260px;
            padding: 32px 48px;
            max-width: 1600px;
            background: white;
            min-height: 100vh;
        }

        h1 { font-size: 2.2rem; color: var(--primary); }
        h2 { font-size: 1.5rem; margin: 32px 0 16px; color: var(--primary); }
        h3 { font-size: 1.1rem; margin: 24px 0 12px; color: var(--primary); }

        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            margin-bottom: 16px;
        }

        .stats-card {
            background: var(--primary);
            color: white;
            text-align: center;
        }

        .stats-value {
            font-size: 1.8rem;
            font-weight: bold;
        }

        .feature-card {
            background: #f8f9fa;
            border-left: 3px solid var(--accent);
        }

        .tier-card {
            border-left: 4px solid var(--success);
            background: linear-gradient(to right, rgba(16, 185, 129, 0.05), transparent);
        }

        .tier-card.tier-1 {
            border-left-color: var(--danger);
            background: linear-gradient(to right, rgba(239, 68, 68, 0.05), transparent);
        }

        .tier-card.tier-2 {
            border-left-color: var(--warning);
            background: linear-gradient(to right, rgba(245, 158, 11, 0.05), transparent);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }

        th {
            background: var(--primary);
            color: white;
            padding: 10px 12px;
            text-align: left;
            font-size: 0.9rem;
        }

        td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }

        .badge {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .badge.high { background: var(--danger); color: white; }
        .badge.medium { background: var(--warning); color: white; }
        .badge.low { background: var(--success); color: white; }
        .badge.score { background: var(--accent); color: white; }

        .chart-container {
            position: relative;
            height: 350px;
            margin: 20px 0;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }

        .ranking-item {
            background: white;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            transition: all 0.2s;
        }

        .ranking-item:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.12);
            transform: translateY(-2px);
        }

        .ranking-number {
            background: var(--primary);
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 12px;
        }

        .ranking-title {
            font-size: 1.1rem;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 8px;
        }

        .ranking-scores {
            display: flex;
            gap: 10px;
            margin: 8px 0;
        }

        .score-pill {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .score-eng { background: #e6f3ff; color: var(--accent); }
        .score-biz { background: #e6f9f0; color: var(--success); }
        .score-total { background: var(--primary); color: white; }

        .section-header {
            background: linear-gradient(135deg, var(--primary), #1e293b);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 32px 0 16px 0;
        }

        .trend-indicator {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .trend-up { background: var(--success); color: white; }
        .trend-stable { background: var(--warning); color: white; }
        .trend-down { background: var(--danger); color: white; }

        .mermaid {
            text-align: center;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h1>🚀 AIランキング・レポート</h1>
        <a href="#overview" class="nav-item active">📊 概要</a>
        <a href="#rankings" class="nav-item">🏆 ランキング</a>
        <a href="#analysis" class="nav-item">📈 分析</a>
        <a href="#categories" class="nav-item">🏷️ カテゴリ別</a>
        <a href="#trends" class="nav-item">📊 トレンド</a>
        <a href="#insights" class="nav-item">💡 洞察</a>
        <a href="#recommendations" class="nav-item">🎯 推奨事項</a>
    </div>

    <div class="main-content">
        <section id="overview">
            <h1>{{ title }}</h1>
            <p class="text-secondary">{{ period_start }} 〜 {{ period_end }}</p>
            
            <div class="stats-grid">
                <div class="card stats-card">
                    <div class="stats-value">{{ total_items }}</div>
                    <div>分析対象技術</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ "%.1f"|format(score_stats.avg_total_score) }}</div>
                    <div>平均総合スコア</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ "%.1f"|format(score_stats.avg_eng_score) }}</div>
                    <div>平均エンジニアスコア</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ "%.1f"|format(score_stats.avg_biz_score) }}</div>
                    <div>平均ビジネススコア</div>
                </div>
            </div>

            <div class="card feature-card">
                <h3>📋 レポートサマリー</h3>
                <p>直近1ヶ月間のAI技術トレンドを、エンジニア活用度とビジネス効率化の2軸で評価・ランキング化。</p>
                <p><strong>生成日時:</strong> {{ generation_timestamp }}</p>
            </div>

            <div class="card">
                <h3>🔍 キーポイント</h3>
                <ul>
                    {% for point in key_points %}
                    <li>{{ point }}</li>
                    {% endfor %}
                </ul>
            </div>
        </section>

        <section id="rankings">
            <div class="section-header">
                <h2>🏆 AIニューステクノロジーランキング Top 30</h2>
                <p>エンジニア活用度 + ビジネス効率化度の総合評価</p>
            </div>

            {% for item in ranking_items %}
            <div class="ranking-item">
                <div style="display: flex; align-items: flex-start;">
                    <div class="ranking-number">{{ item.rank }}</div>
                    <div style="flex: 1;">
                        <div class="ranking-title">{{ item.name }}</div>
                        <p class="text-secondary">{{ item.description }}</p>
                        <div class="ranking-scores">
                            <span class="score-pill score-eng">Eng: {{ item.eng_tool }}/5</span>
                            <span class="score-pill score-biz">Biz: {{ item.biz_eff }}/5</span>
                            <span class="score-pill score-total">Total: {{ item.total_score }}/10</span>
                        </div>
                        <p><strong>活用ポイント:</strong> {{ item.benefits }}</p>
                    </div>
                </div>
            </div>
            {% endfor %}
        </section>

        <section id="analysis">
            <div class="section-header">
                <h2>📈 詳細分析</h2>
            </div>

            <div class="card">
                <h3>📊 スコア分布分析</h3>
                <div class="chart-container">
                    <canvas id="scoreDistributionChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>⚖️ エンジニア vs ビジネス スコア比較 (Top 10)</h3>
                <div class="chart-container">
                    <canvas id="comparisonChart"></canvas>
                </div>
            </div>
        </section>

        <section id="categories">
            <div class="section-header">
                <h2>🏷️ カテゴリ別分析</h2>
            </div>

            <div class="card">
                <h3>📋 技術カテゴリ分布</h3>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>

            {% for category, items in categories.items() %}
            <div class="card tier-card">
                <h3>{{ category }} ({{ items|length }}件)</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                    {% for item in items[:6] %}
                    <div style="padding: 12px; background: white; border-radius: 6px; border: 1px solid var(--border);">
                        <h4>{{ loop.index }}. {{ item.name }}</h4>
                        <div class="ranking-scores" style="margin-top: 8px;">
                            <span class="score-pill score-total">{{ item.total_score }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </section>

        <section id="trends">
            <div class="section-header">
                <h2>📊 トレンド分析</h2>
            </div>

            <div class="card feature-card">
                <h3>🚀 高インパクト技術 (8-9点)</h3>
                <p><strong>{{ impact_distribution.high|length }}件</strong> - 即座に実用導入を検討すべき技術</p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; margin-top: 16px;">
                    {% for item in impact_distribution.high %}
                    <div class="ranking-item">
                        <div class="ranking-title">{{ item.name }}</div>
                        <span class="badge high">HIGH IMPACT</span>
                        <div class="ranking-scores">
                            <span class="score-pill score-total">{{ item.total_score }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="card">
                <h3>⚡ 中インパクト技術 (7点)</h3>
                <p><strong>{{ impact_distribution.medium|length }}件</strong> - 導入検討・PoC実施を推奨</p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 8px; margin-top: 16px;">
                    {% for item in impact_distribution.medium %}
                    <div style="padding: 12px; background: #f8f9fa; border-radius: 6px; border-left: 3px solid var(--warning);">
                        <strong>{{ item.name }}</strong>
                        <span class="badge medium">MEDIUM</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </section>

        <section id="insights">
            <div class="section-header">
                <h2>💡 インサイト・洞察</h2>
            </div>

            <div class="card feature-card">
                <h3>🎯 エンジニア向けトップ技術</h3>
                <table>
                    <thead>
                        <tr>
                            <th>順位</th>
                            <th>技術名</th>
                            <th>Engスコア</th>
                            <th>活用領域</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in top_performers.engineering[:5] %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td><strong>{{ item.name }}</strong></td>
                            <td><span class="badge score">{{ item.eng_tool }}/5</span></td>
                            <td>{{ item.benefits[:50] }}...</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="card feature-card">
                <h3>💼 ビジネス向けトップ技術</h3>
                <table>
                    <thead>
                        <tr>
                            <th>順位</th>
                            <th>技術名</th>
                            <th>Bizスコア</th>
                            <th>効率化効果</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in top_performers.business[:5] %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td><strong>{{ item.name }}</strong></td>
                            <td><span class="badge score">{{ item.biz_eff }}/5</span></td>
                            <td>{{ item.benefits[:50] }}...</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            {% if sectors %}
            <div class="card">
                <h3>🏢 セクター別パフォーマンス</h3>
                <table>
                    <thead>
                        <tr>
                            <th>セクター</th>
                            <th>代表技術</th>
                            <th>件数</th>
                            <th>平均スコア</th>
                            <th>活用例</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for sector in sectors %}
                        <tr>
                            <td><strong>{{ sector.name }}</strong></td>
                            <td>{{ sector.representative }}</td>
                            <td>{{ sector.count }}</td>
                            <td><span class="badge score">{{ sector.avg_score }}</span></td>
                            <td>{{ sector.use_case }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </section>

        <section id="recommendations">
            <div class="section-header">
                <h2>🎯 推奨事項・アクションプラン</h2>
            </div>

            <div class="card tier-card tier-1">
                <h3>⚡ 即時導入推奨 (スコア8-9)</h3>
                <p><strong>優先度: 最高</strong> - 今週〜来月での導入検討</p>
                <ul>
                    {% for item in impact_distribution.high %}
                    <li><strong>{{ item.name }}:</strong> {{ item.benefits[:100] }}...</li>
                    {% endfor %}
                </ul>
            </div>

            <div class="card tier-card tier-2">
                <h3>🔍 PoC・検証推奨 (スコア7)</h3>
                <p><strong>優先度: 高</strong> - 2-3ヶ月での概念実証</p>
                <ul>
                    {% for item in impact_distribution.medium[:5] %}
                    <li><strong>{{ item.name }}:</strong> {{ item.description[:80] }}...</li>
                    {% endfor %}
                </ul>
            </div>

            <div class="card">
                <h3>📊 活用戦略マトリクス</h3>
                
                <div class="mermaid">
                    quadrantChart
                        title AIテクノロジー活用戦略
                        x-axis "ビジネス効率化" --> "高効率化"
                        y-axis "エンジニア活用度" --> "高活用度"
                        quadrant-1 "戦略的投資領域"
                        quadrant-2 "優先導入領域"
                        quadrant-3 "検討領域"
                        quadrant-4 "ビジネス特化領域"
                        {% for item in top_performers.overall[:8] %}
                        "{{ item.name[:10] }}": [{{ item.biz_eff * 20 }}, {{ item.eng_tool * 20 }}]
                        {% endfor %}
                </div>
            </div>

            <div class="card feature-card">
                <h3>🗓️ 実装ロードマップ</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                    <div class="card">
                        <h4>Phase 1: 即時 (1-2週間)</h4>
                        <ul>
                            <li>OpenAI GPT-OSS 評価・導入</li>
                            <li>Claude 4.1 Opus コーディング支援</li>
                            <li>Microsoft Copilot Excel統合</li>
                        </ul>
                    </div>
                    <div class="card">
                        <h4>Phase 2: 短期 (1-3ヶ月)</h4>
                        <ul>
                            <li>Google Genie 3 プロトタイプ</li>
                            <li>DeepSeek V3.1 コスト評価</li>
                            <li>NVIDIA Nemotron エッジ検証</li>
                        </ul>
                    </div>
                    <div class="card">
                        <h4>Phase 3: 中期 (3-6ヶ月)</h4>
                        <ul>
                            <li>ビジュアル・メディア技術統合</li>
                            <li>エージェント技術の業務応用</li>
                            <li>セキュアプラットフォーム構築</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>📈 成功指標 (KPI)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>指標</th>
                            <th>現状</th>
                            <th>目標 (3ヶ月)</th>
                            <th>測定方法</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>開発生産性</td>
                            <td>ベースライン</td>
                            <td>30% 向上</td>
                            <td>コード生成・デバッグ時間測定</td>
                        </tr>
                        <tr>
                            <td>業務効率化</td>
                            <td>ベースライン</td>
                            <td>25% 向上</td>
                            <td>定型業務処理時間削減</td>
                        </tr>
                        <tr>
                            <td>技術導入率</td>
                            <td>0%</td>
                            <td>70%</td>
                            <td>チーム内AI技術活用率</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <div style="margin-top: 60px; padding: 20px; background: var(--light); border-radius: 8px; text-align: center;">
            <p><strong>Generated by AI News Intelligence Platform v2.0</strong></p>
            <p>{{ generation_timestamp }} | Based on {{ total_items }} AI technologies analysis</p>
            <p><em>このレポートは直近1ヶ月のX(Twitter)投稿から抽出・分析されたデータに基づいています</em></p>
        </div>
    </div>

    <script>
        // Mermaid初期化
        mermaid.initialize({ startOnLoad: true });

        // スコア分布チャート
        const scoreCtx = document.getElementById('scoreDistributionChart').getContext('2d');
        new Chart(scoreCtx, {
            type: 'doughnut',
            data: {
                labels: {{ chart_data.score_labels|safe }},
                datasets: [{
                    data: {{ chart_data.score_values|safe }},
                    backgroundColor: ['#ef4444', '#f59e0b', '#10b981', '#94a3b8']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: '総合スコア分布' }
                }
            }
        });

        // エンジニア vs ビジネス比較チャート
        const comparisonCtx = document.getElementById('comparisonChart').getContext('2d');
        new Chart(comparisonCtx, {
            type: 'bar',
            data: {
                labels: {{ chart_data.comparison_labels|safe }},
                datasets: [{
                    label: 'エンジニア活用度',
                    data: {{ chart_data.eng_scores|safe }},
                    backgroundColor: '#3b82f6'
                }, {
                    label: 'ビジネス効率化',
                    data: {{ chart_data.biz_scores|safe }},
                    backgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: 'エンジニア vs ビジネス活用度比較' }
                },
                scales: {
                    y: { beginAtZero: true, max: 5 }
                }
            }
        });

        // カテゴリ分布チャート
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {
            type: 'pie',
            data: {
                labels: {{ chart_data.category_labels|safe }},
                datasets: [{
                    data: {{ chart_data.category_values|safe }},
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: '技術カテゴリ分布' }
                }
            }
        });

        // サイドバーナビゲーション
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                this.classList.add('active');
                const target = this.getAttribute('href');
                if (target && target !== '#') {
                    document.querySelector(target).scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        console.log('✅ AI Ranking Report with improved-requirements-doc.html style loaded');
        console.log('📊 Analyzed {{ total_items }} technologies, Average Score: {{ "%.1f"|format(chart_data.avg_total_score) }}');
    </script>
</body>
</html>'''


# 使用例
def main():
    """メイン関数"""
    generator = RankingReportGenerator()
    
    # ランキングレポート生成
    input_file = r"C:\Users\yoshitaka\input\20250826AIニュースランキング 直近1ヶ月間のトップ30.txt"
    result = generator.generate_ranking_report(
        input_file, 
        "AIニューステクノロジーランキング・レポート 2025"
    )
    
    if result:
        print(f"🎉 AI Ranking Report generated: {result}")
        print(f"🌐 ブラウザで開く: file://{Path(result).absolute()}")
    else:
        print("❌ Report generation failed")


if __name__ == "__main__":
    main()
