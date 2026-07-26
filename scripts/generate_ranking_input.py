"""
Generate presentations/ai_ranking_input_latest.txt from the last 30 days of
news archives.

Per-day source priority (root news/*.json stopped being written on
2026-06-14, which starved the 30-day window and broke the cron on 07-14):
  1. news/YYYY-MM-DD.json                                   (legacy schema)
  2. presentations/daily_reports/auto_daily_report_YYYY_MM_DD.html
     — parsed via the stable ".row" card markup (title / cat / src /
     score / tldr), score 0-100 mapped to stars 1-5.

The output format mirrors the markdown-like structure that
RankingReportGenerator.parse_ranking_data() expects:

  直近1ヶ月（YYYY年M月D日からYYYY年M月D日）

  **キー points:**
  - ...

  **ランキング概要**
  1. **NAME**: DESCRIPTION. Eng Tool: X, Biz Eff: Y, 合計: Z. BENEFITS.
  ...

  | セクター | 代表技術 | 件数 | 平均スコア | 活用例 |
  ...

Source data shape (news/YYYY-MM-DD.json):
  {
    "highlight": {title, stars, summary, sources:[{name,url}], category},
    "sections": {category: [{title, blurb, stars, source:{name,url}}, ...]}
  }
"""
from __future__ import annotations

import html as htmllib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NEWS_DIR = REPO_ROOT / "news"
DAILY_REPORT_DIR = REPO_ROOT / "presentations" / "daily_reports"
OUTPUT = REPO_ROOT / "presentations" / "ai_ranking_input_latest.txt"

WINDOW_DAYS = 30
TOP_N = 30


def _safe_text(s: str, max_len: int = 120) -> str:
    """Strip newlines and any chars that break the parser regex.

    The parser splits the line on '.', so internal periods are not allowed
    in NAME or DESCRIPTION. Asterisks break the **NAME** delimiters.
    """
    s = (s or "").replace("\r", " ").replace("\n", " ")
    s = s.replace("*", "＊")
    s = s.replace(".", "．")  # full-width period — preserves shape, dodges regex
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        s = s[: max_len - 1] + "…"
    return s


def _benefits_text(s: str, max_len: int = 160) -> str:
    """Benefits field may contain '.' internally per the regex. Just normalize."""
    s = (s or "").replace("\r", " ").replace("\n", " ")
    s = s.replace("*", "＊")
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        s = s[: max_len - 1] + "…"
    return s.rstrip("。.") or "—"


def _category_jp(cat: str) -> str:
    table = {
        "tech": "技術",
        "biz": "ビジネス",
        "business": "ビジネス",
        "research": "研究",
        "tool": "ツール",
        "tools": "ツール",
        "sns": "SNS",
        "policy": "政策",
        "company": "企業",
        "posts": "投稿",
    }
    return table.get((cat or "").lower(), cat or "その他")


def _scores_for(stars: int, category: str) -> tuple[int, int]:
    """Map stars (1-5) and category to (eng_tool, biz_eff).

    Tech-leaning items skew toward eng_tool; business/policy toward biz_eff.
    """
    s = max(1, min(5, int(stars or 0)))
    c = (category or "").lower()
    if c in {"tech", "research", "tool", "tools"}:
        eng = s
        biz = max(1, s - 1)
    elif c in {"biz", "business", "company", "policy"}:
        eng = max(1, s - 1)
        biz = s
    else:
        eng = s
        biz = s
    return eng, biz


def _collect_archive_files() -> list[Path]:
    """Per day, prefer the legacy news JSON, else the daily report HTML."""
    today = datetime.now().date()
    files: list[Path] = []
    for delta in range(WINDOW_DAYS):
        d = today - timedelta(days=delta)
        p = NEWS_DIR / f"{d.isoformat()}.json"
        if p.exists():
            files.append(p)
            continue
        rp = DAILY_REPORT_DIR / f"auto_daily_report_{d.strftime('%Y_%m_%d')}.html"
        if rp.exists():
            files.append(rp)
    return files


# Matches one headline card in auto_daily_report_*.html. The markup is
# machine-generated and stable: row-trend/row-label chips between the title
# and the category are optional, hence the non-greedy gaps.
ROW_RE = re.compile(
    r'<span class="row-title">(?P<title>.*?)</span>'
    r'.*?<span class="row-cat[^"]*">(?P<cat>.*?)</span>'
    r'.*?<span class="row-src">(?P<src>.*?)</span>'
    r'.*?<span class="row-score[^"]*">(?P<score>\d+)</span>'
    r'.*?<div class="row-tldr">(?P<tldr>.*?)</div>',
    re.DOTALL,
)

_CATEGORY_NORM = {
    "ai model": "tech",
    "model": "tech",
    "business": "biz",
    "funding": "biz",
    "research": "research",
    "paper": "research",
    "repo": "tool",
    "repository": "tool",
    "product": "tool",
    "regulation": "policy",
}


def _strip_tags(s: str) -> str:
    return htmllib.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def _items_from_report_html(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"skip {path.name}: {e}")
        return []
    items: list[dict] = []
    for m in ROW_RE.finditer(text):
        title = _strip_tags(m.group("title"))
        if not title:
            continue
        score = int(m.group("score"))
        cat = _strip_tags(m.group("cat")).lower()
        items.append({
            "title": title,
            "blurb": _strip_tags(m.group("tldr")),
            "stars": max(1, min(5, int(score / 20 + 0.5))),
            "category": _CATEGORY_NORM.get(cat, cat),
            "source": {"name": _strip_tags(m.group("src")) or "—"},
        })
    return items


def _load_items(files: list[Path]) -> list[dict]:
    items: list[dict] = []
    for f in files:
        if f.suffix == ".html":
            items.extend(_items_from_report_html(f))
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"skip {f.name}: {e}")
            continue

        hl = data.get("highlight") or {}
        if hl.get("title"):
            items.append({
                "title": hl.get("title", ""),
                "blurb": hl.get("summary") or hl.get("blurb") or "",
                "stars": int(hl.get("stars") or 5),
                "category": (hl.get("category") or "highlight").lower(),
                "source": (hl.get("sources") or [{}])[0],
            })

        for cat, lst in (data.get("sections") or {}).items():
            for raw in lst or []:
                if not raw or not raw.get("title"):
                    continue
                items.append({
                    "title": raw.get("title", ""),
                    "blurb": raw.get("blurb") or raw.get("summary") or "",
                    "stars": int(raw.get("stars") or 0),
                    "category": (raw.get("category") or cat or "").lower(),
                    "source": raw.get("source") or {},
                })
    return items


def _dedupe(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for it in items:
        key = it["title"].strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _build_ranking_section(items: list[dict]) -> tuple[str, list[dict]]:
    enriched = []
    for it in items:
        eng, biz = _scores_for(it["stars"], it["category"])
        enriched.append({**it, "eng_tool": eng, "biz_eff": biz, "total": eng + biz})

    enriched.sort(key=lambda x: (x["total"], x["stars"]), reverse=True)
    top = enriched[:TOP_N]

    lines = ["**ランキング概要**"]
    for i, it in enumerate(top, 1):
        name = _safe_text(it["title"], max_len=80)
        desc = _safe_text(it["blurb"] or it["title"], max_len=120)
        if not desc:
            desc = name
        src_name = (it.get("source") or {}).get("name") or "—"
        cat_jp = _category_jp(it["category"])
        benefits = _benefits_text(f"活用領域: {cat_jp}。出典: {src_name}")
        lines.append(
            f"{i}. **{name}**: {desc}. "
            f"Eng Tool: {it['eng_tool']}, Biz Eff: {it['biz_eff']}, 合計: {it['total']}. "
            f"{benefits}."
        )
    return "\n".join(lines), top


def _build_key_points(top: list[dict]) -> list[str]:
    if not top:
        return ["対象期間内の集計データが見つかりませんでした。"]
    cat_counts = Counter(_category_jp(it["category"]) for it in top)
    top_cats = ", ".join(f"{c}: {n}件" for c, n in cat_counts.most_common(3))
    avg = sum(it["total"] for it in top) / len(top)
    return [
        f"トップカテゴリ: {top_cats}",
        f"平均スコア(Eng+Biz): {avg:.1f}",
        f"期間内件数: {len(top)}（候補から上位{TOP_N}件を抽出）",
    ]


def _build_sectors(top: list[dict]) -> str:
    """Produce the 3-row sector table the parser expects (>=6 pipes per row)."""
    buckets = {"モデル・LLM": [], "ツール・SDK": [], "ビジネス活用": []}

    def _bucket_of(it: dict) -> str:
        title = (it["title"] or "").lower()
        cat = it["category"]
        if any(k in title for k in ["gpt", "claude", "llm", "model", "gemini", "grok", "llama"]):
            return "モデル・LLM"
        if cat in {"tool", "tools", "tech", "research"}:
            return "ツール・SDK"
        return "ビジネス活用"

    for it in top:
        buckets[_bucket_of(it)].append(it)

    examples = {
        "モデル・LLM": ("LLM/生成モデル", "生成/要約/対話"),
        "ツール・SDK": ("開発・運用", "開発効率/自動化"),
        "ビジネス活用": ("業務適用", "業務効率/導入効果"),
    }

    rows = ["| セクター | 代表技術 | 件数 | 平均スコア | 活用例 |", "|---|---|---:|---:|---|"]
    for name, lst in buckets.items():
        rep, use = examples[name]
        count = len(lst)
        avg = (sum(x["total"] for x in lst) / count) if count else 0.0
        rows.append(f"| {name} | {rep} | {count} | {avg:.1f} | {use} |")
    return "\n".join(rows)


def main() -> int:
    files = _collect_archive_files()
    if not files:
        print(f"No archives found under {NEWS_DIR} for the last {WINDOW_DAYS} days.")
        return 1

    items = _dedupe(_load_items(files))
    if not items:
        print("No items collected from archives.")
        return 2

    ranking_block, top = _build_ranking_section(items)
    key_points = _build_key_points(top)
    sectors_block = _build_sectors(top)

    today = datetime.now().date()
    start = today - timedelta(days=WINDOW_DAYS - 1)
    period = f"{start.year}年{start.month}月{start.day}日から{today.year}年{today.month}月{today.day}日"

    out_lines = [
        f"直近1ヶ月（{period}）",
        "",
        "**キー points:**",
        *(f"- {p}" for p in key_points),
        "",
        ranking_block,
        "",
        sectors_block,
        "",
    ]

    OUTPUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote: {OUTPUT}  (items={len(top)}, archives_scanned={len(files)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
