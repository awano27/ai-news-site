#!/usr/bin/env python3
from __future__ import annotations

import re, html
from pathlib import Path

try:
    from ftfy import fix_text  # type: ignore
except Exception:
    def fix_text(s: str) -> str:
        return s


def summarize(text: str) -> tuple[str, list[str], list[str]]:
    text = fix_text(text)
    sentences = [s.strip() for s in re.split(r'[。！？!?]\s*', text) if s.strip()]
    paras = [p.strip() for p in re.split(r'\n\s*\n+', text) if p.strip()]
    summary = (paras[1] if len(paras)>1 else paras[0]) if paras else (sentences[0] if sentences else '')
    summary = summary[:280]
    pts: list[str] = []
    for s in sentences:
        if s and s not in summary:
            pts.append(s)
        if len(pts) >= 5:
            break
    urls = re.findall(r'https?://[^\s<>\)]+', text)
    # de-dup keep order
    seen = set(); out = []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return summary, pts, out[:6]


def build_html(date_disp: str, summary: str, points: list[str], links: list[str]) -> str:
    points_li = '\n'.join(f'<li>{html.escape(p)}</li>' for p in points[:5]) or '<li>（ポイントは準備中です）</li>'
    links_a = ' '.join(f'<a class="btn" href="{u}" target="_blank" rel="noopener">{html.escape(u)}</a>' for u in links) or '<span class="note">（リンク情報なし）</span>'
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>{date_disp} - AI News Analysis</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/theme/white.css">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{ --primary:#0f172a; --accent:#3b82f6; --ok:#10b981; --warn:#f59e0b; --bg2: linear-gradient(135deg,#0f172a 0%,#1e293b 100%); }}
    .reveal{{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif}}
    .reveal .controls,.reveal .progress,.reveal .playback,.reveal .slide-number{{display:none!important}}
    .reveal .slides section{{text-align:left}}
    .reveal h1,.reveal h2,.reveal h3{{color:var(--primary);font-weight:600;text-align:center}}
    .title-slide{{background:var(--bg2);color:#fff;padding:2rem;border-radius:15px;text-align:center;position:relative;overflow:hidden}}
    .title-slide h1{{color:#fff;font-size:2.5em;margin-bottom:.5em;text-shadow:2px 2px 4px rgba(0,0,0,.3)}}
    .impact-badge{{display:inline-block;background:#e5f0ff;color:#1e3a8a;padding:.35rem .9rem;border-radius:999px;font-weight:700;margin:.25rem}}
    .feature-box{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px}}
    .btn{{display:inline-block;border:1px solid #e2e8f0;border-radius:10px;padding:8px 12px;color:var(--accent);text-decoration:none;font-weight:700;margin-right:8px}}
    ul.points{{margin-left:1.2rem}}
  </style>
</head>
<body>
  <div class="reveal"><div class="slides">
      <section class="title-slide">
        <h1>Daily AI News</h1>
        <h2 style="color:#fff !important; border:none;">AIニュースダイジェスト（{date_disp}）</h2>
        <div style="margin:18px 0;">
          <span class="impact-badge">注目トピック</span>
          <span class="impact-badge">要点サマリ</span>
          <span class="impact-badge">リンク付き</span>
        </div>
      </section>

      <section>
        <h2>概要とポイント</h2>
        <div class="feature-box">
          <p>{html.escape(summary) if summary else '（概要は準備中です）'}</p>
          <ul class="points">
{points_li}
          </ul>
        </div>
      </section>

      <section>
        <h2>リンク</h2>
        <div class="feature-box">
          {links_a}
        </div>
      </section>
  </div></div>
</body>
</html>
'''


def main():
    src = Path(r'C:/Users/yoshitaka/input/day/0907.txt')
    text = src.read_text(encoding='utf-8')
    summary, points, links = summarize(text)
    html = build_html('2025/09/07', summary, points, links)
    Path('presentations/day_slides/day_slide_2025_09_07.html').write_text(html, encoding='utf-8')
    print('OK')


if __name__ == '__main__':
    main()

