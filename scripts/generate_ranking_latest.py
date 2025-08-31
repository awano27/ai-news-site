"""
Generate latest AI ranking report from presentations/ai_ranking_input_latest.txt

This script uses RankingReportGenerator's parsing/analysis and renders the
embedded template directly, skipping sanitize() to avoid brittle failures.
It outputs a dated report and updates ai_ranking_report_latest.html.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Template, select_autoescape
import re

from src.generators.ranking_report_generator import RankingReportGenerator


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / "presentations" / "ai_ranking_input_latest.txt"
    out_dir = repo_root / "presentations"
    out_dir.mkdir(parents=True, exist_ok=True)

    gen = RankingReportGenerator(templates_dir=str(repo_root / "templates"),
                                 output_dir=str(out_dir))

    data = {}
    analysis = {}
    parsed_items = []

    # Strategy 1: parse markdown-like ranking input if available
    if input_path.exists():
        data = gen.parse_ranking_data(str(input_path))
        parsed_items = data.get('ranking_items', []) if data else []

    # Strategy 2: if parsed items are too few, fall back to structured JSON (last 30 days)
    if not parsed_items or len(parsed_items) < 15:
        struct_file = Path(r"C:\Users\yoshitaka\input") / "����1�����f�[�^.txt"  # 直近1ヶ月のデータ.txt (mojibake path in this environment)
        # If mojibake path fails, try scanning directory for a JSON-like txt
        if not struct_file.exists():
            candidates = list(Path(r"C:\Users\yoshitaka\input").glob("*データ*.txt"))
            if candidates:
                struct_file = candidates[0]
        if struct_file.exists():
            try:
                raw = struct_file.read_text(encoding='utf-8')
                import json as _json
                try:
                    j = _json.loads(raw)
                except Exception:
                    # Fallback: try to heuristically trim trailing non-JSON content
                    json_end = raw.rfind('}') + 1
                    j = _json.loads(raw[:json_end])
                items = j.get('items', [])

                # Build ranking_items from structured items with heuristics
                ranking_items = []
                for it in items:
                    A = it.get('A', {})
                    B = it.get('B', '') or ''
                    C = it.get('C', []) or []
                    F = it.get('F', {})
                    G = it.get('G', {})
                    impact = int(F.get('impact_score', 0) or 0)
                    reason = F.get('reason', '') or ''

                    # Title/name: prefer slide_title, fallback to trimmed B
                    name = (G.get('slide_title') or '').strip()
                    if not name:
                        name = B.strip().split('、')[0][:60] if B else (A.get('url') or '')

                    # Description: first sentence of B
                    description = B.strip().split('。')[0][:120] if B else ''

                    # Extract scores from reason (e.g., 実用性23/25、業界波及20/25)
                    eng_tool = None
                    biz_eff = None
                    m1 = re.search(r'実用性(\d+)\s*/\s*25', reason)
                    if m1:
                        eng_tool = max(1, min(5, round(int(m1.group(1)) / 5)))
                    m2 = re.search(r'(?:業界波及|波及)(\d+)\s*/\s*25', reason)
                    if m2:
                        biz_eff = max(1, min(5, round(int(m2.group(1)) / 5)))
                    # Fallbacks from impact
                    if eng_tool is None:
                        eng_tool = max(1, min(5, round(impact / 20)))
                    if biz_eff is None:
                        biz_eff = max(1, min(5, round(impact / 20)))

                    # Total score approx on 5-9 scale
                    total_score = max(5, min(9, round(impact / 12)))

                    benefits = ' / '.join([str(x) for x in C[:3]])[:160]

                    ranking_items.append({
                        'rank': 0,  # assign after sorting
                        'name': name,
                        'description': description,
                        'eng_tool': int(eng_tool),
                        'biz_eff': int(biz_eff),
                        'total_score': int(total_score),
                        'benefits': benefits or '—'
                    })

                # Take top 30 by impact score (we already have items in original order; re-sort by impact)
                # Recompute sorting key based on impact parsed above
                def _impact_key(x):
                    # approximate back from total_score to impact
                    return x.get('total_score', 0)

                ranking_items.sort(key=_impact_key, reverse=True)
                for i, it in enumerate(ranking_items[:30], 1):
                    it['rank'] = i
                ranking_items = ranking_items[:30]

                # Build data structure expected by generator
                today = datetime.now()
                start_30 = (today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30))
                data = {
                    'period_start': start_30.strftime('%Y年%m月%d日'),
                    'period_end': today.strftime('%Y年%m月%d日'),
                    'ranking_items': ranking_items,
                    'key_points': [],
                    'sectors': [],
                    'total_items': len(ranking_items)
                }
            except Exception as e:
                print(f"Fallback to structured JSON failed: {e}")

    if not data:
        print("Failed to build ranking data. Aborting.")
        return 3

    analysis = gen.analyze_ranking_metrics(data)

    # Prepare template data (mirrors generator implementation)
    # Override period to "last 30 days from today" for clarity
    today = datetime.now()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
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

    # Ensure Mermaid quadrantChart has safe labels and plotted points
    def _sanitize_label(s: str) -> str:
        s = (s or '').strip()
        # Remove quotes and control characters
        s = s.replace('"', '').replace("'", '')
        s = re.sub(r"[\r\n\t]+", " ", s)
        # Trim length to avoid overflow
        return s[:20]

    overall = analysis.get('top_performers', {}).get('overall') if analysis else None
    items_for_quad = overall or sorted(data['ranking_items'], key=lambda x: x.get('total_score', 0), reverse=True)
    points = []
    for it in items_for_quad[:8]:
        label = _sanitize_label(it.get('name', '')) or 'Item'
        x = int(it.get('biz_eff', 0)) * 20
        y = int(it.get('eng_tool', 0)) * 20
        if x == 0 and y == 0:
            continue
        points.append(f'        "{label}": [{x}, {y}]')

    quad_block = (
        "quadrantChart\n"
        "        title AIテクノロジー活用戦略\n"
        "        x-axis ビジネス効率 --> 高効率\n"
        "        y-axis エンジニア活用度 --> 高活用度\n"
        "        quadrant-1 戦略的投資領域\n"
        "        quadrant-2 優先導入領域\n"
        "        quadrant-3 検討領域\n"
        "        quadrant-4 ビジネス特化領域\n"
        + ("\n".join(points) if points else "        \"No Data\": [10, 10]")
        + "\n"
    )

    # Replace existing quadrantChart block within the mermaid div
    html = re.sub(r'(\<div class=\"mermaid\"\>)[\s\S]*?quadrantChart[\s\S]*?(\</div\>)',
                  rf"\1\n{quad_block}\2", html)

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
