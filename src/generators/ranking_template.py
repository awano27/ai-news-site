"""
ranking_template.py — Pure string: the HTML template for ranking reports.

Zero imports by design (pure data). Extracted from ranking_report_generator.py.
"""
from __future__ import annotations


def get_template_string() -> str:
    """Return the Jinja2 HTML template string for ranking reports."""
    return '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='14' fill='%23070F26'/><text x='50' y='66' text-anchor='middle' font-family='sans-serif' font-weight='700' font-size='38' fill='%23FFCC00'>AI</text></svg>" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700;900&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        :root {
            --navy: #070F26;
            --navy-2: #0c1838;
            --navy-line: rgba(255,255,255,0.08);
            --primary: #070F26;
            --accent: #0d6efd;
            --accent-d: #0a59cf;
            --yellow: #FFCC00;
            --yellow-d: #e6b800;
            --success: #1f9d57;
            --warning: #e6b800;
            --danger: #d6453a;
            --light: #F6F7F9;
            --panel: #ffffff;
            --border: #e6e8ee;
            --text-primary: #1a1f2e;
            --text-secondary: #4a5260;
            --text-muted: #8a93a3;
            --sans: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', system-ui, sans-serif;
            --serif: 'Source Serif 4', 'Hiragino Mincho ProN', 'YuMincho', 'Yu Mincho', 'Noto Serif JP', Georgia, serif;
            --maxw: 1180px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--sans);
            font-size: 15px;
            line-height: 1.7;
            color: var(--text-primary);
            background: var(--light);
        }
        a { color: inherit; text-decoration: none; }

        /* ---- Top header (matches visionhub TOP) ---- */
        .site-header {
            position: sticky; top: 0; z-index: 50;
            background: rgba(7,15,38,0.92);
            backdrop-filter: saturate(140%) blur(16px);
            -webkit-backdrop-filter: saturate(140%) blur(16px);
            border-bottom: 1px solid var(--navy-line);
        }
        .header-row {
            display: flex; align-items: center; justify-content: space-between;
            gap: 18px; height: 68px;
        }
        .brand {
            display: inline-flex; align-items: center; gap: 12px;
            font-weight: 700; font-size: 17px; color: #fff; letter-spacing: 0.04em;
            white-space: nowrap;
        }
        .brand-mark {
            width: 36px; height: 36px; border-radius: 50%;
            border: 2px solid var(--yellow); color: var(--yellow);
            display: inline-flex; align-items: center; justify-content: center;
            font-weight: 900; font-size: 15px;
        }
        .nav {
            display: flex; align-items: center; gap: 2px; font-size: 14px; flex-wrap: nowrap;
        }
        .nav a {
            color: #fff; padding: 8px 12px; font-weight: 500; white-space: nowrap;
            border-radius: 8px; transition: color 0.15s ease, background 0.15s ease;
        }
        .nav a:hover { color: var(--yellow); }
        .cta {
            background: var(--yellow); color: var(--navy);
            padding: 11px 20px; border-radius: 999px; font-weight: 700; font-size: 14px;
            white-space: nowrap; transition: background 0.15s ease;
            display: inline-flex; align-items: center; gap: 7px;
        }
        .cta:hover { background: var(--yellow-d); }

        .container {
            max-width: var(--maxw); margin: 0 auto;
            padding-inline: clamp(20px, 4vw, 48px);
        }

        /* ---- Hero band ---- */
        .report-hero {
            background:
              radial-gradient(900px 460px at 82% -12%, rgba(13,110,253,0.20), transparent 60%),
              radial-gradient(700px 420px at 4% 6%, rgba(255,204,0,0.10), transparent 58%),
              var(--navy);
            color: #fff; padding: 56px 0 60px; border-bottom: 1px solid var(--navy-line);
        }
        .report-hero .eyebrow {
            display: inline-flex; align-items: center; gap: 9px;
            font-size: 12px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
            color: var(--yellow); margin-bottom: 18px;
        }
        .report-hero .eyebrow::before {
            content: ""; width: 22px; height: 2px; background: var(--yellow); display: inline-block;
        }
        .report-hero h1 {
            font-family: var(--serif); font-weight: 700;
            font-size: clamp(30px, 4.6vw, 50px); line-height: 1.22; color: #fff;
            letter-spacing: 0.005em; margin-bottom: 16px; max-width: 22ch;
        }
        .report-hero .period {
            font-size: 15px; color: var(--on-dark-mu, #a8b2c3); font-weight: 500;
            display: inline-flex; align-items: center; gap: 10px;
        }
        .report-hero .period .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--yellow); }

        .main-content { padding: 0 0 40px; background: var(--light); }
        section { scroll-margin-top: 84px; }
        .section-wrap { padding: 46px 0; }
        .section-wrap + .section-wrap { border-top: 1px solid var(--border); }

        h1 { font-size: 2rem; color: var(--primary); font-family: var(--serif); }
        h2 { font-size: 1.5rem; margin: 0 0 18px; color: var(--primary); font-family: var(--serif); font-weight: 700; }
        h3 { font-size: 1.12rem; margin: 22px 0 12px; color: var(--primary); font-weight: 700; }
        h4 { font-size: 1rem; color: var(--primary); font-weight: 700; }

        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            margin-bottom: 16px;
        }

        .stats-card {
            background: var(--navy);
            color: white;
            text-align: center;
            border: 1px solid var(--navy-line);
        }

        .stats-value {
            font-size: 2rem;
            font-weight: 900;
            color: var(--yellow);
            font-family: var(--serif);
            line-height: 1.1;
        }
        .stats-card > div:last-child { color: #cdd4e0; font-size: 0.82rem; margin-top: 6px; }

        .feature-card {
            background: #fffdf2;
            border-left: 3px solid var(--yellow);
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
            background: var(--navy);
            color: white;
            padding: 11px 13px;
            text-align: left;
            font-size: 0.88rem;
            font-weight: 700;
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
        .badge.medium { background: var(--warning); color: var(--navy); }
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
            background: var(--yellow);
            color: var(--navy);
            width: 34px;
            height: 34px;
            min-width: 34px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-family: var(--serif);
            margin-right: 14px;
        }
        .ranking-item:nth-child(-n+4) .ranking-number { box-shadow: 0 0 0 3px rgba(255,204,0,0.22); }

        .ranking-title {
            font-size: 1.12rem;
            font-weight: 700;
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

        .score-eng { background: #e7f0ff; color: var(--accent-d); }
        .score-biz { background: #e8f6ee; color: var(--success); }
        .score-total { background: var(--navy); color: var(--yellow); }

        .section-header {
            border-left: 4px solid var(--yellow);
            padding: 4px 0 4px 18px;
            margin: 0 0 22px 0;
        }
        .section-header h2 { margin: 0 0 4px; }
        .section-header p { color: var(--text-secondary); font-size: 0.92rem; }

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

        .text-secondary { color: var(--text-secondary); }
        .card { border-radius: 12px; }
        .card h3, .card h4 { font-family: var(--sans); }
        .chart-container {
            background: var(--panel);
            border-radius: 10px;
        }
        ul { padding-left: 1.2em; }
        li { margin: 4px 0; }

        @media (max-width: 900px) {
            .nav { display: none; }
            .report-hero { padding: 40px 0 44px; }
        }
        @media (max-width: 560px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .brand-text { display: none; }
        }
    </style>
</head>
<body>
    <header class="site-header">
        <div class="container header-row">
            <a class="brand" href="../index.html">
                <span class="brand-mark">AI</span>
                <span class="brand-text">AI Intelligence Hub</span>
            </a>
            <nav class="nav" aria-label="セクション">
                <a href="#overview">概要</a>
                <a href="#rankings">ランキング</a>
                <a href="#analysis">分析</a>
                <a href="#categories">カテゴリ別</a>
                <a href="#trends">トレンド</a>
                <a href="#recommendations">推奨</a>
            </nav>
            <a class="cta" href="../index.html"><span aria-hidden="true">←</span> TOPページ</a>
        </div>
    </header>

    <div class="report-hero">
        <div class="container">
            <span class="eyebrow">AI Technology Ranking</span>
            <h1>{{ title }}</h1>
            <p class="period"><span class="dot"></span>{{ period_start }} 〜 {{ period_end }}　|　生成 {{ generation_timestamp }}</p>
        </div>
    </div>

    <div class="main-content">
      <div class="container">
        <section id="overview" class="section-wrap">
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

        <section id="rankings" class="section-wrap">
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

        <section id="analysis" class="section-wrap">
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

        <section id="categories" class="section-wrap">
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

        <section id="trends" class="section-wrap">
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

        <section id="insights" class="section-wrap">
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

        <section id="recommendations" class="section-wrap">
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

      </div>
    </div>

    <footer class="site-footer">
        <div class="container">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px;">
                <span class="brand-mark">AI</span>
                <strong style="color:#fff; letter-spacing:0.04em;">AI Intelligence Hub</strong>
            </div>
            <p style="margin-bottom:6px;">{{ generation_timestamp }} ｜ {{ total_items }} 技術を分析（直近1ヶ月）</p>
            <p style="margin-bottom:16px; color:#7e8799;"><em>本レポートは直近1ヶ月のAIニュースアーカイブから抽出・スコアリングしたデータに基づきます。</em></p>
            <div style="display:flex; gap:18px; flex-wrap:wrap; font-size:13px;">
                <a href="../index.html" style="color:var(--yellow); font-weight:600;">← TOPページに戻る</a>
                <a href="day_slides_index.html" style="color:#fff;">日次スライド</a>
                <a href="news_archive.html" style="color:#fff;">ニュースアーカイブ</a>
            </div>
        </div>
    </footer>

    <script>
        // Mermaid初期化（ブランドテーマ）
        mermaid.initialize({
            startOnLoad: true,
            theme: 'base',
            themeVariables: {
                primaryColor: '#070F26',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#FFCC00',
                lineColor: '#0d6efd',
                fontFamily: "'Noto Sans JP', sans-serif"
            }
        });

        // スコア分布チャート
        const scoreCtx = document.getElementById('scoreDistributionChart').getContext('2d');
        new Chart(scoreCtx, {
            type: 'doughnut',
            data: {
                labels: {{ chart_data.score_labels|safe }},
                datasets: [{
                    data: {{ chart_data.score_values|safe }},
                    backgroundColor: ['#FFCC00', '#0d6efd', '#1f9d57', '#94a3b8']
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
                    backgroundColor: '#0d6efd'
                }, {
                    label: 'ビジネス効率化',
                    data: {{ chart_data.biz_scores|safe }},
                    backgroundColor: '#FFCC00'
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
                    backgroundColor: ['#0d6efd', '#FFCC00', '#1f9d57', '#8b5cf6']
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

        // ヘッダー内アンカーのスムーススクロール
        document.querySelectorAll('.nav a[href^="#"]').forEach(item => {
            item.addEventListener('click', function(e) {
                const target = this.getAttribute('href');
                const el = target && target !== '#' ? document.querySelector(target) : null;
                if (el) { e.preventDefault(); el.scrollIntoView({ behavior: 'smooth' }); }
            });
        });

        console.log('✅ AI Ranking Report with improved-requirements-doc.html style loaded');
        console.log('📊 Analyzed {{ total_items }} technologies, Average Score: {{ "%.1f"|format(chart_data.avg_total_score) }}');
    </script>
</body>
</html>'''
