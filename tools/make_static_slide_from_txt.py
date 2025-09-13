#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, html, re
from pathlib import Path

def sanitize(s: str) -> str:
    if not s: return ''
    s = s.replace('\uFFFD','')
    s = re.sub(r'[\uE000-\uF8FF]', '', s)
    s = re.sub(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])','', s)
    s = re.sub(r'[\u00A0\u2000-\u200B\u3000]+',' ', s)
    s = re.sub(r'\s+',' ', s).strip()
    return s

def guess_title(text: str, date_disp: str) -> str:
    t = text
    if re.search(r'\bCerebras\b', t, re.I) and re.search(r'K2\s*Think', t, re.I):
        return 'Cerebras「K2 Think」公開（OpenAI互換API・~2000 tok/s）'
    for line in text.splitlines():
        sl = sanitize(line)
        if len(re.findall(r'[A-Za-z0-9]', sl)) >= 8:
            return sl[:140]
    return f'{date_disp} 日次スライド'

def collect_bullets(text: str) -> list[str]:
    bullets=[]
    for raw in text.splitlines():
        s = sanitize(raw)
        if not s: continue
        if any(k in s for k in ['Cerebras','K2','OpenAI','API','tokens','Apache','Hugging Face','MLPerf','MBZUAI','G42']):
            bullets.append(s)
        if len(bullets) >= 5: break
    if not bullets:
        bullets = [sanitize(text)[:200]]
    return bullets[:5]

def collect_links(text: str) -> list[str]:
    urls = re.findall(r'https?://[^\s\)＞>"\']+', text)
    seen=set(); out=[]
    for u in urls:
        if u in seen: continue
        seen.add(u); out.append(u)
    return out[:6]

def find_scores(text: str) -> tuple[str,str,str,str]:
    def pick(tag, default):
        m = re.search(tag + r'.{0,20}?(\d{1,3}(?:\.\d+)?)', text, re.I)
        return m.group(1) if m else default
    return pick('K1','—'), pick('K2','—'), pick('K3','—'), (re.search(r'(?:Total|合計).{0,20}?(\d{1,3}(?:\.\d+)?)', text, re.I).group(1) if re.search(r'(?:Total|合計).{0,20}?(\d{1,3}(?:\.\d+)?)', text, re.I) else '—')

TPL = """<!DOCTYPE html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{date_ja} - {title}</title>
  <style>
    :root{{ --fg:#0f172a; --muted:#475569; --accent:#3b82f6; --border:#e5e7eb; }}
    *{{ box-sizing:border-box }}
    body{{ margin:0; font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,Arial,\"Noto Sans JP\",sans-serif; color:var(--fg); background:#fff }}
    header{{ padding:14px 16px; border-bottom:1px solid var(--border); position:sticky; top:0; background:#fff; z-index:10 }}
    header .nav a{{ text-decoration:none; color:var(--accent); font-weight:800 }}
    .wrap{{ max-width:1100px; margin:0 auto; padding:20px 16px 40px }}
    .title{{ background:linear-gradient(135deg,#0f172a,#1e293b); color:#fff; border-radius:14px; padding:20px }}
    .date{{ display:inline-block; background:rgba(255,255,255,.18); padding:6px 12px; border-radius:999px; font-weight:800 }}
    h1{{ margin:.4em 0 .2em; font-size:28px; letter-spacing:-.02em }}
    .subtitle{{ color:#cbd5e1 }}
    section{{ background:#fff; border:1px solid var(--border); border-radius:12px; padding:16px; margin-top:16px }}
    h2{{ margin:0 0 8px 0; font-size:20px; border-bottom:3px solid var(--accent); padding-bottom:6px }}
    ul{{ margin:0 0 0 1.2em; padding:0 }}
    li{{ line-height:1.75; margin:.25em 0 }}
    .grid{{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px }}
    .card{{ background:#fff; border:1px solid var(--border); border-radius:12px; padding:12px }}
    .btns a{{ display:inline-block; margin:6px 8px 0 0; padding:10px 12px; border-radius:10px; text-decoration:none; font-weight:800 }}
    .btn{{ background:#0f172a; color:#fff }}
    .btn.secondary{{ background:#fff; color:var(--fg); border:1px solid var(--border) }}
    footer{{ margin-top:18px; color:#64748b; font-size:12px; text-align:right }}
  </style>
</head>
<body>
  <header><div class=\"nav\"><a href=\"../day_slides_index.html\">← 日次スライド一覧</a></div></header>
  <div class=\"wrap\">
    <section class=\"title\">
      <span class=\"date\">{date_disp}</span>
      <h1>{title}</h1>
      <div class=\"subtitle\">{subtitle}</div>
    </section>
    <section>
      <h2>概要</h2>
      <ul>
{bullets}
      </ul>
    </section>
    <section>
      <h2>評価（スコア）</h2>
      <div class=\"grid\">
        <div class=\"card\">
          <h3 style=\"margin:0 0 6px 0; font-size:16px\">スコア</h3>
          <table style=\"width:100%; border-collapse:collapse\">
            <tr><th style=\"text-align:left; border-bottom:1px solid var(--border); padding:6px 4px; width:40%\">K1</th><td style=\"border-bottom:1px solid var(--border); padding:6px 4px\">{k1}</td></tr>
            <tr><th style=\"text-align:left; border-bottom:1px solid var(--border); padding:6px 4px\">K2</th><td style=\"border-bottom:1px solid var(--border); padding:6px 4px\">{k2}</td></tr>
            <tr><th style=\"text-align:left; border-bottom:1px solid var(--border); padding:6px 4px\">K3</th><td style=\"border-bottom:1px solid var(--border); padding:6px 4px\">{k3}</td></tr>
            <tr><th style=\"text-align:left; padding:6px 4px\">合計</th><td style=\"padding:6px 4px\"><strong>{total}</strong></td></tr>
          </table>
        </div>
        <div class=\"card\">
          <h3 style=\"margin:0 0 6px 0; font-size:16px\">解釈</h3>
          <ul>
            <li>K1: 新規性・影響の度合い</li>
            <li>K2: 実装・適用性</li>
            <li>K3: 話題性</li>
          </ul>
        </div>
      </div>
    </section>
    <section>
      <h2>参考リンク</h2>
      <div class=\"btns\">
{links}
      </div>
    </section>
    <section>
      <h2>ナビゲーション</h2>
      <div class=\"btns\">
        <a class=\"btn secondary\" href=\"../day_slides_index.html\">📅 日次スライド一覧</a>
        <a class=\"btn\" href=\"../ai_ranking_report_latest.html\">🏆 ランキングレポート（最新）</a>
      </div>
    </section>
    <footer>© AI Intelligence</footer>
  </div>
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
    y, m, d = args.date.split('-')
    date_disp = f"{y}/{m}/{d}"; date_ja = f"{y}年{m}月{d}日"

    title = guess_title(raw, date_disp)
    bullets = collect_bullets(raw)
    urls = collect_links(raw)
    k1,k2,k3,total = find_scores(raw)

    bullets_html = '\n'.join('        <li>'+html.escape(sanitize(b))+'</li>' for b in bullets)
    links_html = '\n'.join('        <a class="btn" href="'+html.escape(u)+'" target="_blank" rel="noopener">リンク</a>' for u in urls) or '        —'

    html_out = TPL.format(
        date_ja=html.escape(date_ja), date_disp=html.escape(date_disp),
        title=html.escape(title), subtitle='自動生成（0912.txt 由来・UTF-8整形）',
        bullets=bullets_html, links=links_html,
        k1=html.escape(k1), k2=html.escape(k2), k3=html.escape(k3), total=html.escape(total)
    )
    Path(args.outfile).write_text(html_out, encoding='utf-8', newline='\n')
    print('Wrote', args.outfile)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
