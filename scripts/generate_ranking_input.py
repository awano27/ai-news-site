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

import argparse
import difflib
import html as htmllib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.auto_collect.dedup import _entity_jaccard, _norm_title

NEWS_DIR = REPO_ROOT / "news"
DAILY_REPORT_DIR = REPO_ROOT / "presentations" / "daily_reports"
OUTPUT = REPO_ROOT / "presentations" / "ai_ranking_input_latest.txt"

WINDOW_DAYS = 30
TOP_N = 30

# Append-only keyword lists for is_ai_relevant(). Short Latin tokens use
# lookaround so "brain" / "retailers" / "email" do not count as AI.
AI_RELEVANT_SHORT_TOKENS = (
    "AI", "AIs", "LLM", "LLMs", "GPT", "AGI", "NLP", "MoE", "HBM",
    "GPU", "GPUs", "RAG", "MCP", "NVIDIA",
)
AI_RELEVANT_KEYWORDS = (
    "ChatGPT", "OpenAI", "Anthropic", "DeepSeek", "Gemini", "Claude", "Grok",
    "Cerebras", "Taalas", "Copilot", "Midjourney", "DeepMind", "Gemma",
    "Hugging Face", "HuggingFace", "LLaMA", "Llama", "Qwen", "Mistral", "xAI",
    "transformer",
    "人工知能", "生成AI", "機械学習", "大規模言語", "深層学習", "言語モデル",
    "生成モデル", "ディープラーニング", "推論", "超知能", "エージェント",
    "プロンプト", "ファインチューニング", "ベンチマーク",
    "データセンター", "半導体", "AIモデル", "基盤モデル", "オープンモデル",
)

# Short Latin tokens: not embedded in an English word. Allows 常時稼働AI同僚
# and AIデータセンター, but rejects brain / retailers / email / available.
_SHORT_AI_RE = re.compile(
    r"(?<![A-Za-z])(?:" + "|".join(re.escape(t) for t in AI_RELEVANT_SHORT_TOKENS) + r")(?![A-Za-z])",
    re.IGNORECASE,
)

# Longer Latin / product names — substring, case-insensitive.
_AI_NAME_RE = re.compile(
    r"(?:ChatGPT|OpenAI|Anthropic|DeepSeek|Gemini|Claude|Grok|"
    r"Cerebras|Taalas|Copilot|Midjourney|DeepMind|Gemma|"
    r"Hugging\s*Face|HuggingFace|LLaMA|Llama|Qwen|Mistral|xAI|transformer)",
    re.IGNORECASE,
)

_INFERENCE_RE = re.compile(r"(?<![A-Za-z])inference(?![A-Za-z])", re.IGNORECASE)
_AGENT_RE = re.compile(r"(?<![A-Za-z])agents?(?![A-Za-z])", re.IGNORECASE)
# "モデル" but not Moderna (モデルナ).
_MODEL_RE = re.compile(r"モデル(?!ナ)")

# JP multi-char (and mixed) phrases as substring.
_AI_JP_PHRASES = tuple(
    kw for kw in AI_RELEVANT_KEYWORDS if any(ord(ch) > 127 for ch in kw)
)

# Title denylist — overrides a positive category (熊本 was mislabeled AI Model/95)
# and a positive AI token (キオクシア earnings leaked via 「AI需要」).
_DENY_SUBSTRINGS = (
    "地震",
    "電力小売",
    "eo光",
    "DNA検査",
    "東日本大震災",
    "NFCキー",
    "Writing by hand",
    "海底光ファイバー",
    "宇宙レーザー",
    "キオクシア",
    "Kioxia",
)

# Daily-report categories that are clearly AI. "tech" alone is not enough.
_AI_CATEGORY_RE = re.compile(
    r"(?:^|[\s/_])ai(?:\s|$|[\s/_])",
    re.IGNORECASE,
)

def parse_output_date(value: str | None) -> date:
    """Parse YYYYMMDD or YYYY-MM-DD. None → today (local clock)."""
    if not value:
        return datetime.now().date()
    raw = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"invalid --output-date: {value!r} (use YYYYMMDD)")


def _text_has_ai_signal(text: str) -> bool:
    """True when text contains at least one AI keyword. Fail closed on short Latin."""
    if not text:
        return False
    if _SHORT_AI_RE.search(text):
        return True
    if _AI_NAME_RE.search(text):
        return True
    if _INFERENCE_RE.search(text):
        return True
    if _AGENT_RE.search(text):
        return True
    if _MODEL_RE.search(text):
        return True
    for phrase in _AI_JP_PHRASES:
        if phrase in text:
            return True
    return False


def title_has_ai_signal(title: str) -> bool:
    """True when the title itself is AI-relevant. Fail closed.

    Short tokens use Latin lookaround (not raw substring ``ai``).
    """
    return _text_has_ai_signal(title)


def is_ai_relevant(title: str, blurb: str) -> bool:
    """Rule-based AI gate. True if title or blurb has at least one keyword."""
    return _text_has_ai_signal(title) or _text_has_ai_signal(blurb)


def is_denied_title(title: str) -> bool:
    """Denylist wins over category (and over a positive AI token)."""
    t = title or ""
    low = t.lower()
    for needle in _DENY_SUBSTRINGS:
        if needle.isascii():
            if needle.lower() in low:
                return True
        elif needle in t:
            return True
    if re.search(r"Accel", t, re.IGNORECASE) and (
        "インド" in t or re.search(r"\bIndia\b", t, re.IGNORECASE)
    ):
        return True
    return False


def category_is_clearly_ai(cat: str) -> bool:
    """Daily-report cats like 'AI Model' / 'AI Technology' count as positive."""
    c = (cat or "").strip()
    if not c:
        return False
    return bool(_AI_CATEGORY_RE.search(c))


def is_thin_blurb(title: str, blurb: str) -> bool:
    """Empty, very short, or title-echo blurbs are thin."""
    b = (blurb or "").strip()
    if len(b) < 24:
        return True
    nt, nb = _norm_title(title or ""), _norm_title(b)
    return bool(nt and nb and nt == nb)


def is_ai_relevant_item(item: dict) -> bool:
    """Fail-closed keep decision for one ranking candidate."""
    title = item.get("title") or ""
    blurb = item.get("blurb") or ""
    if is_denied_title(title):
        return False
    if title_has_ai_signal(title):
        return True
    if is_thin_blurb(title, blurb):
        return False
    # Category may count only when the blurb also has an AI signal.
    # Category-alone let 熊本-class mislabels through (denylist is the backstop).
    raw = item.get("raw_category") or item.get("category") or ""
    return category_is_clearly_ai(raw) and title_has_ai_signal(blurb)


def _dedupe_priority(item: dict) -> tuple[int, int]:
    return (int(item.get("stars") or 0), len(item.get("blurb") or ""))


def _lead_katakana_company(title: str) -> str:
    """First 4+ katakana run at the start of a headline (e.g. キオクシア)."""
    t = (title or "").strip()
    m = re.match(r"^[A-Za-z0-9]*[、,\s]*([ァ-ヶー]{4,})", t)
    if m:
        return m.group(1)
    m = re.match(r"^([ァ-ヶー]{4,})", t)
    return m.group(1) if m else ""


def is_same_story(title_a: str, title_b: str) -> bool:
    """Exact / fuzzy title match, entity-Jaccard, or lead-katakana collapse."""
    a, b = (title_a or "").strip(), (title_b or "").strip()
    if not a or not b:
        return False
    if a == b:
        return True
    na, nb = _norm_title(a), _norm_title(b)
    if na and nb and na == nb:
        return True
    if na and nb and difflib.SequenceMatcher(None, na, nb).ratio() >= 0.78:
        return True
    ratio, shared = _entity_jaccard(a, b)
    if shared >= 2 and ratio >= 0.40:
        return True
    # JP company at the start (キオクシア) + moderate overlap.
    # English lead names (OpenAI / Anthropic / Google) are too common
    # to use this way — they glue unrelated stories together.
    ka, kb = _lead_katakana_company(a), _lead_katakana_company(b)
    if ka and ka == kb and na and nb:
        if difflib.SequenceMatcher(None, na, nb).ratio() >= 0.40:
            return True
    return False


def fuzzy_dedupe_items(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """Collapse near-duplicate stories. Keep highest stars, then longest blurb."""
    if not items:
        return [], []
    ranked = sorted(items, key=_dedupe_priority, reverse=True)
    survivors: list[dict] = []
    dropped: list[dict] = []
    for it in ranked:
        title = it.get("title") or ""
        hit = next((s for s in survivors if is_same_story(title, s.get("title") or "")), None)
        if hit is None:
            survivors.append(it)
        else:
            dropped.append({**it, "dropped_as": "duplicate", "kept_title": hit.get("title")})
            hit["n_merged"] = int(hit.get("n_merged") or 0) + 1
    return survivors, dropped


def apply_quality_gate(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """AI filter then fuzzy dedupe. Returns (kept, dropped)."""
    dropped: list[dict] = []
    relevant: list[dict] = []
    for it in items:
        if is_ai_relevant_item(it):
            relevant.append(it)
        else:
            reason = "denylist" if is_denied_title(it.get("title") or "") else "not_ai"
            dropped.append({**it, "dropped_as": reason})
    kept, dupes = fuzzy_dedupe_items(relevant)
    dropped.extend(dupes)
    return kept, dropped


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
        "hardware": "ハードウェア",
    }
    return table.get((cat or "").lower(), cat or "その他")


def _scores_for(stars: int, category: str) -> tuple[int, int]:
    """Map stars (1-5) and category to (eng_tool, biz_eff).

    Tech-leaning items skew toward eng_tool; business/policy toward biz_eff.
    """
    s = max(1, min(5, int(stars or 0)))
    c = (category or "").lower()
    # hardware and clearly-AI daily cats use the same tech-leaning split
    # so they are not dumped into the tied その他 bucket.
    if (
        c in {"tech", "research", "tool", "tools", "hardware"}
        or c.startswith("ai")
        or "ai " in c
    ):
        eng = s
        biz = max(1, s - 1)
    elif c in {"biz", "business", "company", "policy"} or c.startswith("business"):
        eng = max(1, s - 1)
        biz = s
    else:
        # AI ranking default: tech-leaning, not a tied その他 dump.
        eng = s
        biz = max(1, s - 1)
    return eng, biz


def _collect_archive_files(as_of: date | None = None) -> list[Path]:
    """Per day, prefer the legacy news JSON, else the daily report HTML."""
    today = as_of or datetime.now().date()
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
        raw_cat = _strip_tags(m.group("cat"))
        cat = raw_cat.lower()
        items.append({
            "title": title,
            "blurb": _strip_tags(m.group("tldr")),
            "stars": max(1, min(5, int(score / 20 + 0.5))),
            "category": _CATEGORY_NORM.get(cat, cat),
            "raw_category": raw_cat,
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
            raw_cat = hl.get("category") or "highlight"
            items.append({
                "title": hl.get("title", ""),
                "blurb": hl.get("summary") or hl.get("blurb") or "",
                "stars": int(hl.get("stars") or 5),
                "category": str(raw_cat).lower(),
                "raw_category": raw_cat,
                "source": (hl.get("sources") or [{}])[0],
            })

        for cat, lst in (data.get("sections") or {}).items():
            for raw in lst or []:
                if not raw or not raw.get("title"):
                    continue
                raw_cat = raw.get("category") or cat or ""
                items.append({
                    "title": raw.get("title", ""),
                    "blurb": raw.get("blurb") or raw.get("summary") or "",
                    "stars": int(raw.get("stars") or 0),
                    "category": str(raw_cat).lower(),
                    "raw_category": raw_cat,
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

    enriched.sort(
        key=lambda x: (x["total"], x["stars"], int(x.get("n_merged") or 0), len(x.get("blurb") or "")),
        reverse=True,
    )
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
        if cat in {"tool", "tools", "tech", "research", "hardware"}:
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


def _log_dropped(dropped: list[dict]) -> None:
    if not dropped:
        print("quality-gate: dropped 0 items")
        return
    print(f"quality-gate: dropped {len(dropped)} items")
    for it in dropped:
        reason = it.get("dropped_as") or "?"
        extra = f" → kept {it['kept_title']}" if it.get("kept_title") else ""
        print(f"  - [{reason}] {it.get('title', '')}{extra}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate ranking input from archives")
    parser.add_argument(
        "--output-date",
        default=None,
        help="Pin today as YYYYMMDD (keeps dated output on 20260813 across UTC midnight)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print kept/dropped and do not write the output file",
    )
    args = parser.parse_args(argv)

    today = parse_output_date(args.output_date)
    files = _collect_archive_files(today)
    if not files:
        print(f"No archives found under {NEWS_DIR} for the last {WINDOW_DAYS} days.")
        return 1

    items = _dedupe(_load_items(files))
    if not items:
        print("No items collected from archives.")
        return 2

    before = len(items)
    items = [it for it in items if is_ai_relevant(it.get("title") or "", it.get("blurb") or "")]
    print(f"[filter] excluded {before - len(items)} non-AI items")

    kept, dropped = apply_quality_gate(items)
    _log_dropped(dropped)
    if not kept:
        print("No items survived the ranking quality gate.")
        return 3

    ranking_block, top = _build_ranking_section(kept)
    key_points = _build_key_points(top)
    sectors_block = _build_sectors(top)

    start_d = today - timedelta(days=WINDOW_DAYS - 1)
    period = (
        f"{start_d.year}年{start_d.month}月{start_d.day}日から"
        f"{today.year}年{today.month}月{today.day}日"
    )

    out_lines = [
        f"直近1ヶ月（{period}）",
        "",
        "**キー points:**",
        *(f"- {kp}" for kp in key_points),
        "",
        ranking_block,
        "",
        sectors_block,
        "",
    ]

    print(f"quality-gate: kept {len(kept)} (top {len(top)}), archives_scanned={len(files)}")
    if args.dry_run:
        print("--- kept titles ---")
        for it in top:
            print(f"  * {it.get('title')}")
        print(f"dry-run: not writing {OUTPUT}")
        return 0

    OUTPUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote: {OUTPUT}  (items={len(top)}, archives_scanned={len(files)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
