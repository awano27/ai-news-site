"""
DetailAnalysisGenerator

Generates a detailed analysis report from news/latest.json and available
daily slide files. Designed to complement the ranking report by providing
source-level detail, timeline, category distribution, and per-day slide links.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
import re


class DetailAnalysisGenerator:
    def __init__(self, root: Path | None = None, output_dir: Path | None = None):
        self.root = root or Path(__file__).resolve().parents[2]
        self.output_dir = output_dir or (self.root / 'presentations')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---------- data collection ----------
    def load_news_latest(self) -> dict:
        news_path = self.root / 'news' / 'latest.json'
        if not news_path.exists():
            return {}
        with open(news_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_daily_news_files(self, limit: int = 45) -> list[tuple[str, dict]]:
        """Load per-day news JSON files and return list of (date, data).
        Only files matching YYYY-MM-DD.json are considered. Sorted desc.
        """
        news_dir = self.root / 'news'
        out: list[tuple[str, dict]] = []
        if not news_dir.exists():
            return out
        files: list[tuple[str, Path]] = []
        for p in news_dir.glob('*.json'):
            m = re.match(r'^(\d{4}-\d{2}-\d{2})\.json$', p.name)
            if m:
                files.append((m.group(1), p))
        files.sort(key=lambda x: x[0], reverse=True)
        for date, path in files[:limit]:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                out.append((date, data))
            except Exception:
                continue
        return out

    def find_daily_slides(self) -> dict[str, str]:
        """Return map: 'YYYY-MM-DD' -> relative URL to slide HTML (day_slides only)"""
        mapping: dict[str, str] = {}
        day_dir = self.root / 'presentations' / 'day_slides'
        if day_dir.exists():
            for p in day_dir.glob('day_slide_*.html'):
                m = re.match(r'day_slide_(\d{4})_(\d{2})_(\d{2})\.html$', p.name)
                if not m:
                    continue
                y, mth, d = m.groups()
                date = f"{y}-{mth}-{d}"
                mapping[date] = f"day_slides/{p.name}"
        return mapping

    # ---------- analysis ----------
    def _flatten_items(self, data: dict) -> list[dict]:
        items: list[dict] = []
        sections = (data or {}).get('sections', {})
        for key in ['business', 'tools', 'company', 'sns']:
            for it in sections.get(key, []) or []:
                it2 = dict(it)
                it2['category'] = it.get('category') or key
                items.append(it2)
        return items

    def analyze(self, data: dict, slide_map: dict[str, str]) -> dict:
        # Prefer aggregating from per-day files for robust counts
        daily_files = self.load_daily_news_files(limit=45)
        agg_items: list[dict] = []
        for day, d in daily_files:
            for it in self._flatten_items(d):
                if not it.get('date'):
                    it['date'] = day
                agg_items.append(it)
        if not agg_items:
            agg_items = self._flatten_items(data)
        # timeline
        timeline = Counter()
        for it in agg_items:
            date = it.get('date')
            if not date:
                continue
            timeline[date] += 1
        timeline_sorted = sorted(timeline.items())

        # categories
        cat_counter = Counter(it.get('category') or 'other' for it in agg_items)

        # sources
        src_counter = Counter()
        for it in agg_items:
            src = (it.get('source') or {}).get('name') or 'unknown'
            src_counter[src] += 1

        # top items by stars (desc), fallback to recency
        def _stars(it):
            try:
                return int(it.get('stars') or 0)
            except Exception:
                return 0
        def _date_key(it):
            return it.get('date') or ''
        top_items = sorted(agg_items, key=lambda x: (_stars(x), _date_key(x)), reverse=True)[:12]

        # per-day slide links
        day_entries = []
        for date, count in sorted(timeline.items(), reverse=True):
            entry = {
                'date': date,
                'count': count,
                'slide_url': slide_map.get(date)
            }
            day_entries.append(entry)

        return {
            'item_count': len(agg_items),
            'timeline': timeline_sorted,
            'categories': cat_counter.most_common(),
            'sources': src_counter.most_common(12),
            'top_items': top_items,
            'day_entries': day_entries
        }

    # ---------- rendering ----------
    def _safe(self, s: str | None) -> str:
        if not s:
            return ''
        return (str(s)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

    def render_html(self, data: dict, analysis: dict) -> str:
        gen_at = data.get('generated_at')
        ts = gen_at or datetime.now(timezone(timedelta(hours=9))).isoformat()
        items = analysis.get('top_items', [])

        # Prepare chart arrays
        cat_labels = [self._safe(k) for k, _ in analysis.get('categories', [])]
        cat_values = [v for _, v in analysis.get('categories', [])]

        src_labels = [self._safe(k) for k, _ in analysis.get('sources', [])]
        src_values = [v for _, v in analysis.get('sources', [])]

        tl_labels = [d[-5:] for d, _ in analysis.get('timeline', [])]  # MM-DD
        tl_values = [c for _, c in analysis.get('timeline', [])]

        # Build cards
        item_cards = []
        for it in items:
            title = self._safe(it.get('title'))
            blurb = self._safe(it.get('blurb'))
            date = self._safe(it.get('date'))
            cat = self._safe(it.get('category'))
            stars = int(it.get('stars') or 0)
            src = it.get('source') or {}
            src_name = self._safe(src.get('name') or 'link')
            src_url = self._safe(src.get('url') or '#')
            stars_str = '★' * stars + '☆' * max(0, 5 - stars)
            card = f'''
            <article class="card">
              <span class="category">{cat}</span>
              <span class="stars">{stars_str}</span>
              <h3>{title}</h3>
              <p>{blurb}</p>
              <div class="meta"><span>{date}</span> <a class="source-link" href="{src_url}" target="_blank" rel="noopener">出典: {src_name}</a></div>
            </article>
            '''
            item_cards.append(card)

        # Build day entries
        day_rows = []
        for e in analysis.get('day_entries', []):
            date = self._safe(e['date'])
            count = e['count']
            slide = e.get('slide_url')
            link = f'<a href="{self._safe(slide)}" target="_blank" rel="noopener">スライド</a>' if slide else '<span style="color:#94a3b8">-</span>'
            day_rows.append(f'<tr><td>{date}</td><td style="text-align:right">{count}</td><td style="text-align:center">{link}</td></tr>')

        return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AIニュース 詳細分析レポート</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{ --primary:#0f172a; --accent:#3b82f6; --light:#f8fafc; --border:#e2e8f0; --muted:#64748b; }}
    * {{ box-sizing:border-box }}
    body {{ font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; margin:0; background: #fff; color:#0f172a }}
    .container {{ max-width: 1400px; margin:0 auto; padding:24px }}
    .header {{ background:linear-gradient(135deg,#0f172a,#1e293b); color:#fff; border-radius:12px; padding:20px 24px; margin-bottom:16px }}
    .header h1 {{ margin:0 0 6px; font-size:1.4rem }}
    .muted {{ color:#cbd5e1; font-size:.9rem }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(320px,1fr)); gap:16px; margin:16px 0 }}
    .card {{ background:#fff; border:1px solid var(--border); border-radius:12px; padding:16px; box-shadow:0 1px 2px rgba(0,0,0,.03) }}
    .stats {{ display:flex; gap:16px }}
    .stat {{ flex:1; text-align:center; background:#0f172a; color:#fff; border-radius:8px; padding:14px }}
    .stat .v {{ font-weight:700; font-size:1.3rem }}
    .category {{ background:#eef2ff; color:#4338ca; padding:2px 8px; border-radius:12px; font-size:.8rem }}
    .stars {{ float:right; color:#f59e0b }}
    .meta {{ color:#64748b; font-size:.9rem; margin-top:6px }}
    .source-link {{ margin-left:8px }}
    table {{ width:100%; border-collapse:collapse }}
    th,td {{ padding:8px 10px; border-bottom:1px solid var(--border) }}
    th {{ background:#0f172a; color:#fff; text-align:left }}
    .chart {{ position:relative; height:340px }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AIニュース 詳細分析レポート</h1>
      <div class="muted">更新: {ts}</div>
    </div>

    <div class="grid">
      <div class="card stats">
        <div class="stat"><div class="v">{analysis.get('item_count',0)}</div><div>ニュース件数</div></div>
        <div class="stat"><div class="v">{len(analysis.get('day_entries',[]))}</div><div>日数</div></div>
        <div class="stat"><div class="v">{len(analysis.get('categories',[]))}</div><div>カテゴリ</div></div>
      </div>
      <div class="card">
        <h3>カテゴリ分布</h3>
        <div class="chart"><canvas id="catChart"></canvas></div>
      </div>
      <div class="card">
        <h3>ソースTop</h3>
        <div class="chart"><canvas id="srcChart"></canvas></div>
      </div>
      <div class="card" style="grid-column:1/-1">
        <h3>タイムライン（過去30日）</h3>
        <div class="chart"><canvas id="tlChart"></canvas></div>
      </div>
    </div>

    <div class="card">
      <h3>深掘り（スコア上位）</h3>
      <div class="grid">
        {''.join(item_cards) or '<div class="muted">データが不足しています</div>'}
      </div>
    </div>

    <div class="card">
      <h3>日次一覧（スライド連携）</h3>
      <table>
        <thead><tr><th>日付</th><th style="text-align:right">件数</th><th style="text-align:center">スライド</th></tr></thead>
        <tbody>
          {''.join(day_rows) or '<tr><td colspan="3" class="muted">データがありません</td></tr>'}
        </tbody>
      </table>
    </div>

  </div>
  <script>
    const catLabels = {json.dumps(cat_labels, ensure_ascii=False)};
    const catValues = {json.dumps(cat_values)};
    const srcLabels = {json.dumps(src_labels, ensure_ascii=False)};
    const srcValues = {json.dumps(src_values)};
    const tlLabels = {json.dumps(tl_labels, ensure_ascii=False)};
    const tlValues = {json.dumps(tl_values)};

    const catCtx = document.getElementById('catChart').getContext('2d');
    new Chart(catCtx, {type:'pie', data:{labels:catLabels, datasets:[{data:catValues, backgroundColor:['#3b82f6','#10b981','#8b5cf6','#f59e0b','#ef4444','#94a3b8']}]}, options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom'}}}});

    const srcCtx = document.getElementById('srcChart').getContext('2d');
    new Chart(srcCtx, {type:'bar', data:{labels:srcLabels, datasets:[{data:srcValues, backgroundColor:'#3b82f6'}]}, options:{responsive:true, maintainAspectRatio:false, scales:{y:{beginAtZero:true}}, plugins:{legend:{display:false}}}});

    const tlCtx = document.getElementById('tlChart').getContext('2d');
    new Chart(tlCtx, {type:'line', data:{labels:tlLabels, datasets:[{label:'件数', data:tlValues, borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,0.12)', tension:0.35, fill:true}]}, options:{responsive:true, maintainAspectRatio:false, scales:{y:{beginAtZero:true}}}});
  </script>
</body>
</html>'''

    # ---------- main ----------
    def generate(self) -> tuple[Path | None, Path | None]:
        data = self.load_news_latest()
        slides = self.find_daily_slides()
        analysis = self.analyze(data, slides)

        today = datetime.now().strftime('%Y%m%d')
        html = self.render_html(data, analysis)
        dated = self.output_dir / f'ai_news_detail_{today}.html'
        latest = self.output_dir / 'ai_news_detail_latest.html'
        dated.write_text(html, encoding='utf-8')
        latest.write_text(html, encoding='utf-8')
        return dated, latest


def main():
    gen = DetailAnalysisGenerator()
    dated, latest = gen.generate()
    print('generated:', dated)
    print('updated latest:', latest)


if __name__ == '__main__':
    main()
