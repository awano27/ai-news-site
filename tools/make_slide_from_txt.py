#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, html, os, re
from pathlib import Path

def sanitize(s: str) -> str:
    if not s: return ''
    s = s.replace('\uFFFD','')
    s = re.sub(r'[\uE000-\uF8FF]', '', s)
    s = re.sub(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])','', s)
    s = re.sub(r'[\u00A0\u2000-\u200B\u3000]+',' ', s)
    s = re.sub(r'\s+',' ', s).strip()
    return s

def guess_title(text: str, default_date: str) -> str:
    if re.search(r'\bCerebras\b', text, re.I) and re.search(r'K2\s*Think', text, re.I):
        return 'Cerebras「K2 Think」公開（OpenAI互換API・~2000 tok/s）'
    for line in text.splitlines():
        sl = sanitize(line)
        if len(re.findall(r'[A-Za-z0-9]', sl)) >= 8:
            return sl[:140]
    return f'{default_date} 日次スライド'

def collect_links(text: str) -> list[str]:
    urls = re.findall(r'https?://[^\s\)＞>"\']+', text)
    seen=set(); out=[]
    for u in urls:
        if u in seen: continue
        seen.add(u); out.append(u)
    return out[:6]

def collect_bullets(text: str) -> list[str]:
    bullets=[]
    for raw in text.splitlines():
        s = sanitize(raw)
        if not s: continue
        if any(k in s for k in ['Cerebras','K2','OpenAI','API','tokens','Apache','Hugging Face','MLPerf']):
            bullets.append(s)
        if len(bullets) >= 5: break
    if not bullets:
        bullets = [sanitize(text)[:200]]
    return bullets[:5]

def find_scores(text: str) -> tuple[str,str,str,str]:
    def pick(tag, default):
        m = re.search(tag + r'.{0,20}?(\d{1,3})', text, re.I)
        return m.group(1) if m else default
    k1 = pick('K1','—'); k2 = pick('K2','—'); k3 = pick('K3','—')
    tot = re.search(r'(?:Total|合計).{0,20}?(\d{1,3}(?:\.\d+)?)', text, re.I)
    total = tot.group(1) if tot else '—'
    return k1,k2,k3,total

TPL = """<!DOCTYPE html>
<html lang=\"ja\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, user-scalable=yes\">
<title>{date_ja} - {title}</title>
<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.css\">
<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/theme/white.css\">
<link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap\" rel=\"stylesheet\">
<style> html, body {{ height:100%; overflow-y:auto!important; overflow-x:hidden; -webkit-overflow-scrolling:touch; background:#fff }} .reveal {{ position:relative!important; height:auto!important; min-height:100vh; overflow:visible!important; font-family:'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif }} .reveal .slides {{ position:relative!important; width:100%!important; height:auto!important; top:0!important; left:0!important; margin:0!important; padding:20px!important; text-align:center!important; overflow:visible!important; transform:none!important }} .reveal .slides section {{ position:relative!important; width:100%!important; max-width:1100px; margin:0 auto 28px; padding:20px; background:#fff; border:1px solid #e5e7eb; border-radius:16px; box-shadow:0 8px 20px rgba(0,0,0,.08); text-align:left; display:block!important; opacity:1!important; visibility:visible!important; transform:none!important }} .reveal .controls, .reveal .progress, .reveal .playback, .reveal .slide-number {{ display:none!important }} h1 {{ font-size:2.6em!important; font-weight:800!important; margin:.2em 0 .1em; color:#0f172a }} h2 {{ font-size:1.8em!important; font-weight:700!important; color:#0f172a!important; border-bottom:3px solid #3b82f6; padding-bottom:.25em; margin-bottom:.5em }} .badge {{ display:inline-block; background:#3b82f6; color:#fff; font-weight:800; border-radius:999px; padding:4px 10px; font-size:.9em }} ul {{ margin-left:1.2em }} .links a {{ display:inline-block; margin:6px 8px 0 0; padding:8px 12px; border-radius:999px; background:#0f172a; color:#fff; text-decoration:none }} table {{ width:100%; border-collapse:collapse }} th,td {{ border-bottom:1px solid #e5e7eb; padding:8px 10px; text-align:left }} th {{ background:#0f172a; color:#fff }} </style>
<script defer src=\"https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.js\"></script>
</head>
<body>
<div class=\"reveal\"><div class=\"slides\">
<section class=\"title\"> <span class=\"badge\">{date_disp}</span> <h1>{title_en}</h1> <p style=\"color:#475569\">日次AIニューススライド（要点ダイジェスト）</p> </section>
<section> <h2>概要</h2> <ul>
{bullets}
</ul></section>
<section> <h2>評価（スコア）</h2> <table> <tr><th style=\"width:40%\">K1</th><td>{k1}</td></tr> <tr><th>K2</th><td>{k2}</td></tr> <tr><th>K3</th><td>{k3}</td></tr> <tr><th>合計</th><td>{total}</td></tr> </table></section>
<section> <h2>参考リンク</h2> <div class=\"links\">
{links}
</div></section>
<section> <h2>ナビゲーション</h2> <div class=\"links\"> <a href=\"../day_slides_index.html\">📅 日次スライド一覧</a> <a href=\"../ai_ranking_report_latest.html\">🏆 ランキングレポート（最新）</a> </div></section>
</div></div>
<script> if (window.Reveal) {{ Reveal.initialize({{ embedded:true, width:'100%', height:'100%', margin:0, minScale:1, maxScale:1, hash:false, controls:false, progress:false, center:false, transition:'none' }}); }} </script>
</body>
</html>
"""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--infile', required=True)
    ap.add_argument('--date', required=True)
    ap.add_argument('--outfile', required=True)
    args = ap.parse_args()

    raw = Path(args.infile).read_text(encoding='utf-8', errors='replace')
    text = sanitize(raw)
    y, m, d = args.date.split('-')
    date_disp = f"{y}/{m}/{d}"
    date_ja = f"{y}年{m}月{d}日"

    title = guess_title(text, date_disp)
    bullets = collect_bullets(raw)
    urls = collect_links(raw)
    k1, k2, k3, total = find_scores(raw)

    bullets_html = '\n'.join(f"<li>{html.escape(sanitize(b))}</li>" for b in bullets)
    links_html = '\n'.join(f"<a href=\"{html.escape(u)}\" target=\"_blank\" rel=\"noopener\">リンク</a>" for u in urls) or '—'

    html_out = TPL.format(
        date_ja=html.escape(date_ja),
        date_disp=html.escape(date_disp),
        title=html.escape(title),
        title_en=html.escape(title.replace('」','').replace('「','')),
        bullets=bullets_html,
        links=links_html,
        k1=html.escape(k1), k2=html.escape(k2), k3=html.escape(k3), total=html.escape(total)
    )

    Path(args.outfile).write_text(html_out, encoding='utf-8', newline='\n')
    print('Wrote', args.outfile)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
