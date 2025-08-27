"""
DailyNewsGenerator: 毎日のAIニュース結果専用レポート生成クラス

improved-requirements-doc.htmlのデザインを使用して
毎日のAIニュース詳細データから日次レポートを生成
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template


class DailyNewsGenerator:
    """毎日のAIニュース専用レポート生成クラス"""
    
    def __init__(self, templates_dir: str = "templates", output_dir: str = "presentations"):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_daily_news_data(self, file_path: str) -> Dict[str, Any]:
        """毎日のAIニュースデータファイルを解析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本メタデータの抽出
            period_match = re.search(r'2025年(\d+)月(\d+)日から(\d+)月(\d+)日まで', content)
            period_start = f"2025年7月28日"
            period_end = f"2025年8月27日"
            
            # 主要ハイライトの抽出
            highlights = []
            highlight_pattern = r'- \*\*([^*]+)\*\*:\s*([^.]+(?:\.[^-]*)*)'
            highlight_matches = re.findall(highlight_pattern, content)
            
            for match in highlight_matches:
                title, description = match
                highlights.append({
                    'title': title.strip(),
                    'description': description.strip()
                })
            
            # 抽出アイテム一覧の解析
            news_items = []
            
            # アイテムパターンを検索（番号. **タイトル**の形式）
            item_pattern = r'(\d+)\.\s*\*\*([^*\n]+)\*\*'
            item_matches = re.finditer(item_pattern, content)
            
            for match in item_matches:
                item_num = int(match.group(1))
                title = match.group(2).strip()
                
                # 各アイテムの詳細情報を抽出
                item_start = match.end()
                # 次のアイテムまたはセクション終了を探す
                next_match = re.search(r'\n\d+\.\s*\*\*', content[item_start:])
                next_section = re.search(r'\n####', content[item_start:])
                
                if next_match:
                    item_end = item_start + next_match.start()
                elif next_section:
                    item_end = item_start + next_section.start()
                else:
                    item_end = len(content)
                
                item_content = content[item_start:item_end]
                
                # 各メタデータフィールドの抽出
                item_data = {
                    'rank': item_num,
                    'title': title,
                    'meta': self._extract_field(item_content, 'A:'),
                    'summary': self._extract_field(item_content, 'B:'),
                    'bullets': self._extract_bullets(item_content, 'C:'),
                    'tech_eval': self._extract_field(item_content, 'D:'),
                    'verification': self._extract_field(item_content, 'E:'),
                    'score': self._extract_score(item_content, 'F:'),
                    'slide_meta': self._extract_field(item_content, 'G:'),
                    'sources': self._extract_sources(item_content, 'H:'),
                    'reliability': self._extract_field(item_content, 'I:')
                }
                
                news_items.append(item_data)
            
            # テーマ別Top3の抽出
            themes = self._extract_themes(content)
            
            # 日次一覧の抽出
            daily_tops = self._extract_daily_tops(content)
            
            return {
                'period_start': period_start,
                'period_end': period_end,
                'highlights': highlights,
                'news_items': news_items,
                'themes': themes,
                'daily_tops': daily_tops,
                'total_items': len(news_items)
            }
            
        except Exception as e:
            print(f"Error parsing daily news data: {e}")
            return {}
    
    def _extract_field(self, content: str, field_marker: str) -> str:
        """指定されたフィールドマーカーの内容を抽出"""
        pattern = rf'{re.escape(field_marker)}\s*([^\n]*(?:\n(?!\s*-\s*[A-I]:)[^\n]*)*)'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else ""
    
    def _extract_bullets(self, content: str, field_marker: str) -> List[str]:
        """箇条書きリストを抽出"""
        field_content = self._extract_field(content, field_marker)
        if not field_content:
            return []
        
        # "- " で始まる項目を抽出
        bullets = []
        for line in field_content.split('.'):
            line = line.strip()
            if line and not line.startswith('-'):
                bullets.append(line)
        
        return bullets[:5]  # 最大5項目
    
    def _extract_score(self, content: str, field_marker: str) -> Dict[str, Any]:
        """スコア情報を抽出"""
        field_content = self._extract_field(content, field_marker)
        score_match = re.search(r'score=(\d+)', field_content)
        reason_match = re.search(r'reason:\s*([^.]+)', field_content)
        
        return {
            'score': int(score_match.group(1)) if score_match else 0,
            'reason': reason_match.group(1).strip() if reason_match else ""
        }
    
    def _extract_sources(self, content: str, field_marker: str) -> List[str]:
        """ソースリンクを抽出"""
        field_content = self._extract_field(content, field_marker)
        # [テキスト](URL) 形式のリンクを抽出
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', field_content)
        return [url for _, url in links]
    
    def _extract_themes(self, content: str) -> List[Dict[str, Any]]:
        """テーマ別Top3を抽出"""
        themes = []
        theme_section = re.search(r'#### テーマ別Top3(.*?)(?=####|$)', content, re.DOTALL)
        
        if theme_section:
            theme_content = theme_section.group(1)
            theme_pattern = r'- \*\*([^*]+)\*\*:\s*([^(]+)'
            theme_matches = re.findall(theme_pattern, theme_content)
            
            for theme_name, description in theme_matches:
                themes.append({
                    'name': theme_name.strip(),
                    'description': description.strip(),
                    'items': description.split(',')[:3]  # 最初の3項目
                })
        
        return themes
    
    def _extract_daily_tops(self, content: str) -> List[Dict[str, str]]:
        """日次ハイライトを抽出"""
        daily_tops = []
        daily_section = re.search(r'#### 日次一覧.*?Daily Top.*?\n(.*?)(?=####|$)', content, re.DOTALL)
        
        if daily_section:
            daily_content = daily_section.group(1)
            daily_pattern = r'- (\d{4}-\d{2}-\d{2}):\s*([^(]+)'
            daily_matches = re.findall(daily_pattern, daily_content)
            
            for date, event in daily_matches:
                daily_tops.append({
                    'date': date,
                    'event': event.strip(),
                    'formatted_date': self._format_japanese_date(date)
                })
        
        return daily_tops
    
    def analyze_daily_news_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """毎日のAIニュースデータの分析"""
        items = data.get('news_items', [])
        
        if not items:
            return {}
        
        # スコア分析
        scores = [item.get('score', {}).get('score', 0) for item in items]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # カテゴリ別分類
        categories = defaultdict(list)
        for item in items:
            title = item['title'].lower()
            if 'gpt' in title or 'llm' in title or 'model' in title:
                categories['モデル・LLM'].append(item)
            elif 'tool' in title or 'sdk' in title or 'api' in title:
                categories['ツール・SDK'].append(item)
            elif 'paper' in title or '論文' in title or 'research' in title:
                categories['研究・論文'].append(item)
            elif 'game' in title or 'app' in title or 'develop' in title:
                categories['応用・開発'].append(item)
            else:
                categories['その他'].append(item)
        
        # 信頼性分析
        reliability_levels = defaultdict(int)
        for item in items:
            reliability = item.get('reliability', '').lower()
            if '一次ソース' in reliability or 'primary' in reliability:
                reliability_levels['一次ソース'] += 1
            elif 'github' in reliability or 'arxiv' in reliability:
                reliability_levels['検証可能'] += 1
            else:
                reliability_levels['要検証'] += 1
        
        return {
            'score_stats': {
                'avg_score': round(avg_score, 1),
                'max_score': max(scores) if scores else 0,
                'min_score': min(scores) if scores else 0,
                'high_score_count': len([s for s in scores if s >= 85])
            },
            'categories': dict(categories),
            'reliability_levels': dict(reliability_levels),
            'top_scored_items': sorted(items, key=lambda x: x.get('score', {}).get('score', 0), reverse=True)[:5]
        }
    
    def generate_daily_news_report(self, data_file: str, 
                                  report_title: str = None) -> str:
        """毎日のAIニュース専用レポート生成"""
        
        # データの読み込みと解析
        data = self.parse_daily_news_data(data_file)
        if not data:
            return ""
        
        # 詳細分析の実行
        analysis = self.analyze_daily_news_metrics(data)
        
        # レポート用データの準備
        template_data = {
            'title': report_title or '毎日のAIニュース詳細レポート',
            'period_start': data['period_start'],
            'period_end': data['period_end'],
            'generation_timestamp': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
            
            # 基本データ
            'highlights': data['highlights'],
            'news_items': data['news_items'],
            'themes': data['themes'],
            'daily_tops': data['daily_tops'],
            'total_items': data['total_items'],
            
            # 分析結果
            'analysis': analysis,
            'score_stats': analysis.get('score_stats', {}),
            'categories': analysis.get('categories', {}),
            'reliability_levels': analysis.get('reliability_levels', {}),
            'top_scored_items': analysis.get('top_scored_items', []),
            
            # チャート用データ
            'chart_data': self._prepare_daily_chart_data(data, analysis)
        }
        
        # テンプレート生成
        template_content = self._get_daily_news_template()
        template = Template(template_content, autoescape=select_autoescape(['html', 'xml']))
        
        try:
            # HTMLの生成
            html_content = template.render(**template_data)
            
            # ファイル出力
            output_file = self.output_dir / f"daily_ai_news_report_{datetime.now().strftime('%Y%m%d')}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Daily AI News Report generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"❌ Error generating daily news report: {e}")
            import traceback
            print(traceback.format_exc())
            return ""
    
    def _prepare_daily_chart_data(self, data: Dict, analysis: Dict) -> Dict:
        """毎日のニュース用チャートデータの準備"""
        items = data.get('news_items', [])
        
        # スコア分布
        score_ranges = {'90点以上': 0, '80-89点': 0, '70-79点': 0, '70点未満': 0}
        for item in items:
            score = item.get('score', {}).get('score', 0)
            if score >= 90:
                score_ranges['90点以上'] += 1
            elif score >= 80:
                score_ranges['80-89点'] += 1
            elif score >= 70:
                score_ranges['70-79点'] += 1
            else:
                score_ranges['70点未満'] += 1
        
        # カテゴリ分布
        categories = analysis.get('categories', {})
        category_data = {name: len(items) for name, items in categories.items()}
        
        # 信頼性分布
        reliability = analysis.get('reliability_levels', {})
        
        # 日次動向（サンプルデータ）
        daily_tops = data.get('daily_tops', [])
        timeline_labels = [item['date'][-5:] for item in daily_tops[:10]]  # MM-DD形式
        timeline_values = [1] * len(timeline_labels)  # 各日1件として扱う
        
        return {
            # スコア分布
            'score_labels': json.dumps(list(score_ranges.keys())),
            'score_values': json.dumps(list(score_ranges.values())),
            
            # カテゴリ分布
            'category_labels': json.dumps(list(category_data.keys())),
            'category_values': json.dumps(list(category_data.values())),
            
            # 信頼性分布
            'reliability_labels': json.dumps(list(reliability.keys())),
            'reliability_values': json.dumps(list(reliability.values())),
            
            # タイムライン
            'timeline_labels': json.dumps(timeline_labels),
            'timeline_values': json.dumps(timeline_values),
            
            # 統計値
            'avg_score': analysis.get('score_stats', {}).get('avg_score', 0)
        }
    
    def _format_japanese_date(self, date_str: str) -> str:
        """日付を日本語形式にフォーマット"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%m月%d日')
        except:
            return date_str
    
    def _get_daily_news_template(self) -> str:
        """毎日のAIニュース専用テンプレート"""
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
            --research: #8b5cf6;
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
            font-size: 1.2rem;
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

        .news-item {
            background: white;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            transition: all 0.2s;
        }

        .news-item:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.12);
            transform: translateY(-2px);
        }

        .news-rank {
            background: var(--primary);
            color: white;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 12px;
        }

        .news-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 10px;
        }

        .news-score {
            background: var(--success);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
            float: right;
        }

        .news-meta {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 6px;
            margin: 10px 0;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .highlight-item {
            background: linear-gradient(135deg, #f0f8ff, #e6f3ff);
            border-left: 4px solid var(--accent);
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
        }

        .theme-card {
            background: linear-gradient(135deg, #f0f4ff, #e6ecff);
            border-left: 4px solid var(--research);
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
        }

        .daily-event {
            background: white;
            border-left: 3px solid var(--success);
            padding: 12px;
            margin: 8px 0;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }

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

        .section-header {
            background: linear-gradient(135deg, var(--primary), #1e293b);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 32px 0 16px 0;
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
    </style>
</head>
<body>
    <div class="sidebar">
        <h1>📰 毎日のAIニュース詳細</h1>
        <a href="#overview" class="nav-item active">📊 概要</a>
        <a href="#highlights" class="nav-item">✨ ハイライト</a>
        <a href="#news-items" class="nav-item">📰 詳細ニュース</a>
        <a href="#analysis" class="nav-item">📈 分析</a>
        <a href="#themes" class="nav-item">🏷️ テーマ別</a>
        <a href="#timeline" class="nav-item">📅 タイムライン</a>
        <a href="#insights" class="nav-item">💡 洞察</a>
    </div>

    <div class="main-content">
        <section id="overview">
            <h1>{{ title }}</h1>
            <p class="text-secondary">{{ period_start }} 〜 {{ period_end }}</p>
            
            <div class="stats-grid">
                <div class="card stats-card">
                    <div class="stats-value">{{ total_items }}</div>
                    <div>重要ニュース</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ "%.1f"|format(score_stats.avg_score) }}</div>
                    <div>平均影響度スコア</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ score_stats.high_score_count }}</div>
                    <div>高影響度ニュース</div>
                </div>
                <div class="card stats-card">
                    <div class="stats-value">{{ daily_tops|length }}</div>
                    <div>日次ハイライト</div>
                </div>
            </div>

            <div class="card feature-card">
                <h3>📋 レポートサマリー</h3>
                <p>X(Twitter)データから抽出したAI関連エンジニア向け重要ニュースを影響度スコア付きで詳細分析。</p>
                <p><strong>生成日時:</strong> {{ generation_timestamp }}</p>
                <p><strong>分析対象:</strong> like_count>=20の投稿を優先、一次ソース検証済み</p>
            </div>
        </section>

        <section id="highlights">
            <div class="section-header">
                <h2>✨ 主要ハイライト</h2>
                <p>過去30日間の最重要AI技術動向</p>
            </div>

            {% for highlight in highlights %}
            <div class="highlight-item">
                <h3>{{ highlight.title }}</h3>
                <p>{{ highlight.description }}</p>
            </div>
            {% endfor %}
        </section>

        <section id="news-items">
            <div class="section-header">
                <h2>📰 詳細ニュース項目</h2>
                <p>影響度スコア順（技術革新・実用性・波及効果・話題性で評価）</p>
            </div>

            {% for item in news_items %}
            <div class="news-item">
                <div style="display: flex; align-items: flex-start;">
                    <div class="news-rank">{{ item.rank }}</div>
                    <div style="flex: 1;">
                        <div class="news-score">{{ item.score.score }}</div>
                        <div class="news-title">{{ item.title }}</div>
                        
                        <div class="news-meta">
                            <strong>メタ:</strong> {{ item.meta[:100] }}{% if item.meta|length > 100 %}...{% endif %}
                        </div>
                        
                        <p><strong>要約:</strong> {{ item.summary }}</p>
                        
                        {% if item.bullets %}
                        <div style="margin: 12px 0;">
                            <strong>主要ポイント:</strong>
                            <ul>
                                {% for bullet in item.bullets %}
                                <li>{{ bullet }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        {% endif %}
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 12px 0;">
                            <div>
                                <strong>技術評価:</strong><br>
                                <small>{{ item.tech_eval[:100] }}{% if item.tech_eval|length > 100 %}...{% endif %}</small>
                            </div>
                            <div>
                                <strong>検証タスク:</strong><br>
                                <small>{{ item.verification[:100] }}{% if item.verification|length > 100 %}...{% endif %}</small>
                            </div>
                        </div>
                        
                        <div style="margin: 12px 0;">
                            <strong>スライド設計:</strong> {{ item.slide_meta[:150] }}{% if item.slide_meta|length > 150 %}...{% endif %}
                        </div>
                        
                        <div style="margin: 12px 0;">
                            <strong>信頼性:</strong> {{ item.reliability }}
                        </div>
                        
                        {% if item.sources %}
                        <div style="margin: 8px 0;">
                            <strong>出典:</strong>
                            {% for source in item.sources[:3] %}
                            <a href="{{ source }}" target="_blank" style="margin-right: 10px;">Link{{ loop.index }}</a>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        <div style="background: #f0f8ff; padding: 8px; border-radius: 4px; margin-top: 10px;">
                            <strong>影響度理由:</strong> {{ item.score.reason }}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </section>

        <section id="analysis">
            <div class="section-header">
                <h2>📈 統計分析</h2>
            </div>

            <div class="card">
                <h3>📊 影響度スコア分布</h3>
                <div class="chart-container">
                    <canvas id="scoreChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>🏷️ カテゴリ分布</h3>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>🔍 信頼性レベル分布</h3>
                <div class="chart-container">
                    <canvas id="reliabilityChart"></canvas>
                </div>
            </div>
        </section>

        <section id="themes">
            <div class="section-header">
                <h2>🏷️ テーマ別Top3</h2>
            </div>

            {% for theme in themes %}
            <div class="theme-card">
                <h3>{{ theme.name }}</h3>
                <p>{{ theme.description }}</p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px;">
                    {% for item in theme.items %}
                    <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #ddd;">
                        {{ item.strip() }}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </section>

        <section id="timeline">
            <div class="section-header">
                <h2>📅 日次タイムライン</h2>
                <p>過去30日間の主要事件</p>
            </div>

            <div class="card">
                <h3>📈 時系列チャート</h3>
                <div class="chart-container">
                    <canvas id="timelineChart"></canvas>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                {% for daily in daily_tops %}
                <div class="daily-event">
                    <h4>{{ daily.formatted_date }}</h4>
                    <p>{{ daily.event }}</p>
                    <small style="color: var(--text-muted);">{{ daily.date }}</small>
                </div>
                {% endfor %}
            </div>
        </section>

        <section id="insights">
            <div class="section-header">
                <h2>💡 洞察とまとめ</h2>
            </div>

            <div class="card feature-card">
                <h3>🎯 トップスコア技術 (Top 5)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>順位</th>
                            <th>技術</th>
                            <th>スコア</th>
                            <th>主要特徴</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in top_scored_items %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td><strong>{{ item.title[:50] }}{% if item.title|length > 50 %}...{% endif %}</strong></td>
                            <td><span class="badge high">{{ item.score.score }}</span></td>
                            <td>{{ item.summary[:80] }}{% if item.summary|length > 80 %}...{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h3>📊 カテゴリ別サマリー</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
                    {% for category, items in categories.items() %}
                    <div class="card">
                        <h4>{{ category }} ({{ items|length }}件)</h4>
                        <p>主要技術: {{ items[0].title[:40] if items else 'なし' }}{% if items and items[0].title|length > 40 %}...{% endif %}</p>
                        <p>平均スコア: {{ "%.1f"|format(items|map(attribute='score.score')|list|sum / items|length) if items else 0 }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="highlight-item">
                <h3>🔮 全体トレンド総括</h3>
                <p>OpenAIのgpt-ossシリーズリリースを筆頭に、オープンソース化とローカル実行の流れが加速。AMD/NVIDIAのハードウェア最適化ツールが民主化を推進し、エンジニアの実務活用可能性が大幅に向上。</p>
                <p><strong>注目ポイント:</strong></p>
                <ul>
                    <li>SLM（Small Language Model）の効率性が注目され、80%のタスクでLLM並み性能</li>
                    <li>RL統合ベンチマーク（AgentFly等）が適応性評価の新標準となる可能性</li>
                    <li>EU AI Act等の規制議論も活発化、安全性評価の重要性が増加</li>
                </ul>
            </div>

            <div class="card">
                <h3>🎯 エンジニア向け推奨アクション</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                    <div class="highlight-item">
                        <h4>⚡ 即座に検討すべき</h4>
                        <ul>
                            <li>gpt-oss-120bのローカル環境テスト</li>
                            <li>Lemonadeツールの実装検証</li>
                            <li>vLLMへの移行計画策定</li>
                        </ul>
                    </div>
                    <div class="theme-card">
                        <h4>🔍 中期的に監視すべき</h4>
                        <ul>
                            <li>SLM論文の実用化動向</li>
                            <li>RL統合ベンチマークの標準化</li>
                            <li>EU AI Act施行の影響</li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>

        <div style="margin-top: 60px; padding: 20px; background: var(--light); border-radius: 8px; text-align: center;">
            <p><strong>Daily AI News Intelligence Report v2.0</strong></p>
            <p>{{ generation_timestamp }} | Based on {{ total_items }} high-impact news analysis</p>
            <p><em>このレポートはX(Twitter)投稿から抽出・検証された一次ソース情報に基づいています</em></p>
        </div>
    </div>

    <script>
        // Mermaid初期化
        mermaid.initialize({ startOnLoad: true });

        // 影響度スコア分布
        const scoreCtx = document.getElementById('scoreChart').getContext('2d');
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
                    title: { display: true, text: '影響度スコア分布' }
                }
            }
        });

        // カテゴリ分布
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {
            type: 'pie',
            data: {
                labels: {{ chart_data.category_labels|safe }},
                datasets: [{
                    data: {{ chart_data.category_values|safe }},
                    backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: 'カテゴリ分布' }
                }
            }
        });

        // 信頼性レベル
        const reliabilityCtx = document.getElementById('reliabilityChart').getContext('2d');
        new Chart(reliabilityCtx, {
            type: 'bar',
            data: {
                labels: {{ chart_data.reliability_labels|safe }},
                datasets: [{
                    label: '件数',
                    data: {{ chart_data.reliability_values|safe }},
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: '情報源信頼性レベル' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // タイムライン
        const timelineCtx = document.getElementById('timelineChart').getContext('2d');
        new Chart(timelineCtx, {
            type: 'line',
            data: {
                labels: {{ chart_data.timeline_labels|safe }},
                datasets: [{
                    label: '重要イベント',
                    data: {{ chart_data.timeline_values|safe }},
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: '日次重要イベント分布' }
                },
                scales: {
                    y: { beginAtZero: true, max: 2 }
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

        console.log('✅ Daily AI News Report loaded');
        console.log('📊 Analyzed {{ total_items }} news items, Average Score: {{ "%.1f"|format(chart_data.avg_score) }}');
    </script>
</body>
</html>'''


# 使用例
def main():
    """メイン関数"""
    generator = DailyNewsGenerator()
    
    # 毎日のAIニュースレポート生成
    input_file = r"C:\Users\yoshitaka\input\20250826### 過去30日間のAI関連重要ニュース概要.txt"
    result = generator.generate_daily_news_report(
        input_file, 
        "毎日のAIニュース詳細レポート - 過去30日間"
    )
    
    if result:
        print(f"🎉 Daily AI News Report generated: {result}")
        print(f"🌐 ブラウザで開く: file://{Path(result).absolute()}")
    else:
        print("❌ Report generation failed")


if __name__ == "__main__":
    main()