"""
report_dashboard.py — Derive the dashboard layer of the daily report.

The LLM-assigned category, score and evidence label barely vary day to day
(most headlines are "AI Model", 75-85, "Fact"), so they cannot tell a reader
what today was about. This module derives dimensions that do vary — topic
theme, source type, and change against the previous 7 archived reports — and
renders them as the top-of-page dashboard. Everything is deterministic and
computed from the rendered archive, so regenerating a past day is stable.
"""
from __future__ import annotations

import html as _html
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

ARCHIVE_DIR = Path(__file__).resolve().parents[2] / "presentations" / "daily_reports"

# (key, label, css colour var, pattern). First match wins, so narrower
# themes come before broad ones; "other" catches the remainder.
THEMES = [
    ("security", "セキュリティ・不正", "--red",
     r"脆弱性|流出|漏洩|漏えい|サイバー|攻撃|詐欺|パスワード|マルウェア|ランサム|ハッキング|不正アクセス|セキュリティ|CVE|exploit|breach|vulnerab|phishing"),
    ("robotics", "ロボット・物理AI", "--cyan",
     r"ロボット|ヒューマノイド|人型|自動運転|ドローン|robot|humanoid|embodied"),
    ("agents", "エージェント", "--amber",
     r"エージェント|agent|agentic|自律"),
    ("devtools", "開発ツール", "--green",
     r"\bGit\b|コーディング|コード管理|\bIDE\b|\bSDK\b|\bCLI\b|バージョン管理|開発者|developer|copilot|cursor"),
    ("business", "ビジネス・資金", "--orange",
     r"調達|買収|出資|投資|資金|IPO|評価額|売上|提携|ドル|億円|funding|raises|acquir"),
    ("policy", "規制・社会", "--t2",
     r"規制|法案|法律|裁判|訴訟|政府|当局|警察|倫理|著作権|regulat|lawsuit|policy"),
    ("research", "研究・論文", "--plum",
     r"論文|arXiv|ベンチマーク|手法|提案|benchmark|paper"),
    ("models", "モデル", "--blue",
     r"モデル|LLM|GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Mistral|音声認識|画像生成|動画生成|生成AI|ChatGPT|model"),
    ("products", "製品・サービス", "--cream",
     r"アプリ|iPhone|スマホ|Apple|Galaxy|Android|macOS|Windows|サービス|ツール|リリース|発表|提供開始|app|launch"),
    ("other", "その他", "--t3",
     r"."),
]
THEME_INDEX = {key: i for i, (key, *_rest) in enumerate(THEMES)}
_THEME_RES = [(key, re.compile(pat, re.I)) for key, _l, _c, pat in THEMES]

SOURCE_TYPES = [
    ("primary", "一次情報", r"openai|anthropic|google|deepmind|meta ai|microsoft|nvidia|hugging ?face|mistral|blog"),
    ("paper", "論文", r"arxiv|paper"),
    ("community", "コミュニティ", r"hacker news|\bhn\b|reddit|^x$|x\.com|twitter|github"),
    ("media", "メディア", r"."),
]
_SOURCE_RES = [(key, re.compile(pat, re.I)) for key, _l, pat in SOURCE_TYPES]

_ARCHIVE_ROW_RE = re.compile(
    r'<span class="row-title">(?P<title>.*?)</span>'
    r'.*?<span class="row-src">(?P<src>.*?)</span>'
    r'.*?<div class="row-tldr">(?P<tldr>.*?)</div>',
    re.S,
)
_FILE_FMT = "auto_daily_report_{}.html"


def _esc(text) -> str:
    return _html.escape(str(text or ""), quote=True)


def classify_theme(item: Dict) -> str:
    """Theme from title+tldr; the long summary is only a fallback because its
    incidental words (e.g. "攻撃" in a model write-up) would mislabel items."""
    if (item.get("source") or "").lower().startswith("arxiv"):
        head = " ".join(str(item.get(k) or "") for k in ("title", "tldr"))
        for key, rx in _THEME_RES[: THEME_INDEX["research"]]:
            if rx.search(head):
                return key
        return "research"
    for fields in (("title", "tldr"), ("summary",)):
        text = " ".join(str(item.get(k) or "") for k in fields)
        for key, rx in _THEME_RES[:-1]:
            if rx.search(text):
                return key
    return "other"


def source_type(source: str) -> str:
    for key, rx in _SOURCE_RES:
        if rx.search(source or ""):
            return key
    return "media"


def theme_history(report_date: str, days: int = 7, archive_dir: Path = ARCHIVE_DIR) -> List[Dict]:
    """Theme counts for up to `days` archived reports before `report_date`."""
    today = date.fromisoformat(report_date)
    history = []
    for back in range(1, days * 2 + 1):
        if len(history) == days:
            break
        day = today - timedelta(days=back)
        path = archive_dir / _FILE_FMT.format(day.isoformat().replace("-", "_"))
        if not path.exists():
            continue
        counts = {key: 0 for key, *_ in THEMES}
        for m in _ARCHIVE_ROW_RE.finditer(path.read_text(encoding="utf-8", errors="ignore")):
            item = {k: _html.unescape(re.sub(r"<[^>]+>", "", m.group(k))) for k in ("title", "src", "tldr")}
            item["source"] = item.pop("src")
            counts[classify_theme(item)] += 1
        history.append({"date": day.isoformat(), "counts": counts})
    history.reverse()
    return history


def build_dashboard(
    report_date: str,
    headlines: List[Dict],
    item_themes: List[str],
    trend_map: Dict[str, str],
    tools_count: int,
    history: Optional[List[Dict]] = None,
) -> Dict:
    if history is None:
        history = theme_history(report_date)
    total = len(headlines)
    themes = []
    for key, label, color, _pat in THEMES:
        idx = [i for i, t in enumerate(item_themes, 1) if t == key]
        past = [d["counts"].get(key, 0) for d in history]
        avg = sum(past) / len(past) if past else 0.0
        if not idx and (avg < 1 or key == "other"):
            continue
        themes.append({
            "key": key, "label": label, "color": color,
            "count": len(idx), "avg": round(avg, 1),
            "delta": round(len(idx) - avg, 1),
            "spark": past + [len(idx)],
            "items": [{"n": i, "title": headlines[i - 1].get("title", "")} for i in idx],
        })
    themes.sort(key=lambda t: (-t["count"], -t["delta"], THEME_INDEX[t["key"]]))

    sources: Dict[str, int] = {key: 0 for key, *_ in SOURCE_TYPES}
    outlets: Dict[str, int] = {}
    for h in headlines:
        sources[source_type(h.get("source", ""))] += 1
        outlets[h.get("source", "")] = outlets.get(h.get("source", ""), 0) + 1
    top_outlet = max(outlets.items(), key=lambda kv: kv[1]) if outlets else ("", 0)

    new_count = sum(1 for h in headlines if trend_map.get(h.get("title", "")) == "new")
    cont_count = sum(1 for h in headlines if trend_map.get(h.get("title", "")) == "continuing")
    lead = themes[0] if themes and themes[0]["count"] else None
    rising = [t for t in themes if t["key"] != "other" and t["delta"] >= 2 and t["count"] >= 2]
    fading = [t for t in themes if t["key"] != "other" and t["count"] == 0 and t["avg"] >= 1.5]

    return {
        "date": report_date,
        "total": total,
        "new": new_count,
        "continuing": cont_count,
        "lead": lead["key"] if lead else None,
        "themes": themes,
        "rising": [t["key"] for t in rising],
        "fading": [t["key"] for t in fading],
        "sources": sources,
        "primary": sources["primary"] + sources["paper"],
        "top_outlet": {"name": top_outlet[0], "count": top_outlet[1]},
        "history_days": len(history),
        "tools": tools_count,
    }


def brief_sentence(dash: Dict) -> str:
    """One plain-text sentence summarising the day, used as hero-sub."""
    themes = {t["key"]: t for t in dash["themes"]}
    if not dash["lead"]:
        return f"{dash['date']} のAIシグナル{dash['total']}件。"
    lead = themes[dash["lead"]]
    parts = [f"今日の中心は「{lead['label']}」{lead['count']}件"]
    if dash["history_days"]:
        parts[0] += f"（直近{dash['history_days']}日平均 {lead['avg']:g}件）"
    others = [t for t in dash["themes"] if t["key"] != dash["lead"] and t["count"]][:2]
    if others:
        parts.append("次いで" + "・".join(f"{t['label']} {t['count']}件" for t in others))
    parts.append(f"一次情報・論文は {dash['primary']}/{dash['total']}件")
    return "。".join(parts) + "。"


def _spark_svg(values: List[int], color: str) -> str:
    if not values:
        return ""
    w, h, pad = 120, 32, 3
    top = max(max(values), 1)
    step = (w - pad * 2) / max(len(values) - 1, 1)
    pts = [(pad + i * step, h - pad - (v / top) * (h - pad * 2)) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    lx, ly = pts[-1]
    return (
        f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">'
        f'<polyline points="{line}" fill="none" stroke="var({color})" stroke-width="1.6" '
        f'stroke-linejoin="round" vector-effect="non-scaling-stroke" opacity=".75"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.6" fill="var({color})"/></svg>'
    )


def _delta_html(t: Dict, history_days: int) -> str:
    if not history_days:
        return '<span class="dl dl-flat">比較なし</span>'
    d = t["delta"]
    if d >= 1:
        return f'<span class="dl dl-up">▲ {d:g} vs 平均</span>'
    if d <= -1:
        return f'<span class="dl dl-down">▼ {abs(d):g} vs 平均</span>'
    return '<span class="dl dl-flat">平常</span>'


def render_dashboard(dash: Dict) -> str:
    themes = {t["key"]: t for t in dash["themes"]}
    lead = themes.get(dash["lead"]) if dash["lead"] else None
    total = max(dash["total"], 1)

    kpis = [
        (str(dash["total"]), "注目シグナル", f"新規 {dash['new']} · 継続 {dash['continuing']}"),
        (lead["label"] if lead else "—", "主役テーマ",
         f"{lead['count']}件 / 全体の{round(lead['count'] * 100 / total)}%" if lead else ""),
        (f"{dash['primary']}<small>/{dash['total']}</small>", "一次情報・論文",
         f"最多ソース {dash['top_outlet']['name']} {dash['top_outlet']['count']}件"),
        (str(dash["tools"]), "今日試せる", "GitHub・モデル（下段）"),
    ]
    kpi_html = "".join(
        f'<div class="dk"><div class="dk-l">{_esc(l)}</div>'
        f'<div class="dk-n{" dk-n-text" if i == 1 else ""}">{n if i == 2 else _esc(n)}</div>'
        f'<div class="dk-s">{_esc(s)}</div></div>'
        for i, (n, l, s) in enumerate(kpis)
    )

    cards = []
    for t in dash["themes"]:
        links = "".join(
            f'<li><a href="#sig-{it["n"]:02d}">{_esc(it["title"])}</a></li>' for it in t["items"][:2]
        )
        more = len(t["items"]) - 2
        more_html = f'<li class="tc-more">ほか {more}件</li>' if more > 0 else ""
        empty = '<li class="tc-more">今日は該当なし</li>' if not t["items"] else ""
        cards.append(
            f'<div class="tc{" tc-zero" if not t["count"] else ""}" style="--tc:var({t["color"]})">'
            f'<div class="tc-top"><span class="tc-label">{_esc(t["label"])}</span>'
            f'<button class="tc-filter" data-theme="{t["key"]}" aria-label="{_esc(t["label"])}で一覧を絞り込む">一覧で見る</button></div>'
            f'<div class="tc-mid"><span class="tc-n">{t["count"]}</span>'
            f'<span class="tc-meta">{_delta_html(t, dash["history_days"])}'
            f'<span class="tc-avg">直近平均 {t["avg"]:g}</span></span>'
            f'{_spark_svg(t["spark"], t["color"])}</div>'
            f'<ul class="tc-list">{links}{more_html}{empty}</ul></div>'
        )

    changes = []
    for key in dash["rising"]:
        t = themes[key]
        changes.append(f'<li><span class="dl dl-up">急増</span>{_esc(t["label"])}：{t["count"]}件（平均 {t["avg"]:g}）</li>')
    for key in dash["fading"]:
        t = themes[key]
        changes.append(f'<li><span class="dl dl-down">沈静</span>{_esc(t["label"])}：0件（平均 {t["avg"]:g}）</li>')
    if not changes:
        changes.append('<li><span class="dl dl-flat">平常</span>直近平均から大きく外れたテーマはありません</li>')
    changes.append(f'<li><span class="dl dl-flat">新規</span>初出 {dash["new"]}件 · 前日までの続報 {dash["continuing"]}件</li>')

    src_labels = {key: label for key, label, _ in SOURCE_TYPES}
    src_bar = "".join(
        f'<span class="mix-seg mix-{k}" style="flex:{v}" title="{src_labels[k]} {v}件"></span>'
        for k, v in dash["sources"].items() if v
    )
    src_legend = "".join(
        f'<span><i class="mix-dot mix-{k}"></i>{src_labels[k]} {v}</span>'
        for k, v in dash["sources"].items() if v
    )
    concentration = dash["top_outlet"]["count"] / total
    warn = (
        f'<p class="mix-warn">{_esc(dash["top_outlet"]["name"])} が {round(concentration * 100)}% を占めます。'
        f'重要判断の前に一次情報を確認してください。</p>' if concentration >= 0.4 else ""
    )

    return f"""<section class="dash" id="dashboard" aria-label="今日のダッシュボード">
  <div class="dash-kpi">{kpi_html}</div>
  <div class="dash-h"><span>テーマ・ボード</span><small>件数 · 直近{dash['history_days']}日平均との差 · 推移</small></div>
  <div class="tc-grid">{''.join(cards)}</div>
  <div class="dash-side">
    <div class="dp"><div class="dp-h">今日の変化</div><ul class="chg">{''.join(changes)}</ul></div>
    <div class="dp"><div class="dp-h">情報源ミックス</div><div class="mix">{src_bar}</div><div class="mix-legend">{src_legend}</div>{warn}</div>
  </div>
</section>"""


def render_theme_tags(dash: Dict) -> str:
    return "".join(
        f'<button class="tag" data-theme="{t["key"]}">{_esc(t["label"])} <b>{t["count"]}</b></button>'
        for t in dash["themes"] if t["count"]
    )


def theme_label(key: str) -> str:
    for k, label, *_ in THEMES:
        if k == key:
            return label
    return key
