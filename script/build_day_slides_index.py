#!/usr/bin/env python3
"""
Scan presentations/day_slides/day_slide_YYYY_MM_DD.html and emit a rich,
machine-readable metadata index at presentations/day_slides/meta_index.json.

Unlike list.json (date/url/label for nav), this index carries everything the
newsstand list page needs to render visual cards without opening each deck:

    {
      "generated_from": 361,
      "since": "2025-07-30",
      "latest": "2026-07-18",
      "categories": {"agent": 120, ...},
      "issues": [
        {
          "date": "2026-07-18",
          "no": 354,
          "file": "day_slide_2026_07_18.html",
          "url": "https://visionhub.jp/presentations/day_slides/day_slide_2026_07_18.html",
          "title": "チャット型AIの終着点 — SearchOS-V1",
          "description": "SearchOS-V1が検索進捗を...",
          "section": "AI Agent Architecture",
          "cat": "agent",
          "cat_label": "エージェント",
          "cover": "day_slides/images/0718/cover.jpg"   # or null
        }, ...
      ]
    }

Every value is extracted from metadata already present in each deck
(og:title / meta description / JSON-LD articleSection / og:image), so the
index needs no hand maintenance. Sections that match no category rule are
reported on stderr so the mapping table below can be grown over time.
"""
from __future__ import annotations

import html as html_lib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAY_DIR = ROOT / "presentations" / "day_slides"
OUT = DAY_DIR / "meta_index.json"
BASE_URL = "https://visionhub.jp/presentations/day_slides/"

FILE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
OG_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]*)"')
TITLE_TAG_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
OG_DESC_RE = re.compile(r'<meta property="og:description" content="([^"]*)"')
SECTION_RE = re.compile(r'"articleSection"\s*:\s*"([^"]*)"')
OG_IMAGE_RE = re.compile(r'<meta property="og:image" content="([^"]*)"')
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
# Trailing date/branding junk seen across a year of title formats,
# e.g. "… | 2026-04-24 · AI Daily", "… - 2026/04/12", "…｜AI News 2026/05/10",
# "… | 2026年4月15日", "… 2026/05/17". Stripped iteratively.
TITLE_TRAIL_RES = [
    re.compile(r"\s*[|｜]\s*\d{4}-\d{2}-\d{2}(\s*[·・].*)?$"),
    re.compile(r"\s*[|｜]\s*(AI\s*(News|Daily)(\s*Briefing)?)?\s*\d{4}[年/\-]\d{1,2}[月/\-]\d{1,2}日?\s*$"),
    re.compile(r"\s*[-–—]\s*\d{4}/\d{1,2}/\d{1,2}\s*$"),
    re.compile(r"\s+\d{4}/\d{1,2}/\d{1,2}\s*$"),
    re.compile(r"\s*[|｜]\s*AI\s*(News|Daily)(\s*Briefing)?\s*$"),
]
# Leading date junk from 2025-era titles, e.g. "2025/09/09 - Title",
# "2025年09月04日 - Title".
TITLE_LEAD_RE = re.compile(r"^\d{4}[年/\-]\d{1,2}[月/\-]\d{1,2}日?\s*[-–—:：]\s*")

# Ordered category rules: first match wins. Patterns run case-insensitively
# against articleSection first, then title, then description.
# Grow these lists when build output reports unmatched sections.
CATEGORY_RULES = [
    ("agent", "エージェント",
     r"agent|agentic|autonom|operation|workforce|エージェント|自律|同僚|秘書|自走"),
    ("gov", "ガバナンス",
     r"governance|policy|regulat|ethic|sovereign|ガバナンス|規制|政府|主権|国家戦略|義務教育|教育革命|安全保障"),
    ("infra", "インフラ",
     r"infrastructur|compute|datacenter|semiconductor|chip|gpu|nvidia|energy|インフラ|半導体|データセンター|メモリの壁"),
    ("prod", "プロダクト",
     r"wearable|workstation|desktop|product|consumer|device|glass|office|app\b|アプリ|プロダクト|グラス|デスクトップ|パーソナル|生活|財務|医療|健康|オフィス|ブラウザ|マウス|ポインタ|CRM"),
    ("model", "モデル",
     r"model|frontier|llm|moe|quant|multimodal|オープンウェイト|パラメータ|モデル|画像生成|音声|正式発表|リリース"),
    ("arch", "アーキテクチャ",
     r"architect|engineer|develop|platform|sdk|framework|tool|code|coding|context|memory|oss|cli\b|api\b|mcp|ide\b|git|アーキテクチャ|開発|設計|基盤|プラットフォーム|ツール|エンジン|レイヤー|メモリ|記憶|知識|ターミナル|エディタ|コード|訓練|仕様駆動"),
]
FALLBACK_CAT = ("other", "その他")


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def first_match(pattern: re.Pattern, text: str) -> str:
    m = pattern.search(text)
    return html_lib.unescape(m.group(1)).strip() if m else ""


def clean_title(title: str) -> str:
    title = TITLE_LEAD_RE.sub("", title).strip()
    while True:
        before = title
        for pattern in TITLE_TRAIL_RES:
            title = pattern.sub("", title).strip()
        if title == before:
            return title


def classify(section: str, title: str, description: str) -> tuple[str, str, bool]:
    """Return (cat, cat_label, matched_by_section)."""
    # Boilerplate sections carry no signal — skip straight to the title.
    # Bare "AI Architecture" is on this list because early-summer decks used it
    # as a default regardless of content (e.g. governance decks); the real
    # architecture decks carry compound values like "AI Agent Architecture".
    if re.fullmatch(r"AI\s*(News( Digest)?|Daily|Strategy|Architecture)?", section or "", re.I):
        section = ""
    for source, by_section in ((section, True), (title, False), (description, False)):
        if not source:
            continue
        for cat, label, pattern in CATEGORY_RULES:
            if re.search(pattern, source, re.I):
                return cat, label, by_section
    return FALLBACK_CAT[0], FALLBACK_CAT[1], False


def extract(path: Path, date: str) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")

    title = first_match(OG_TITLE_RE, text)
    if not title:
        m = TITLE_TAG_RE.search(text)
        title = html_lib.unescape(strip_tags(m.group(1))) if m else ""
    if not title:
        m = H1_RE.search(text)
        title = html_lib.unescape(strip_tags(m.group(1))) if m else "AI News"
    title = clean_title(title) or "AI News"

    description = first_match(DESC_RE, text) or first_match(OG_DESC_RE, text)
    section = first_match(SECTION_RE, text)

    # Resolve the cover image to a repo-local path so the list page can lazy
    # load it relative to presentations/. og:image is authoritative when its
    # file exists; images/MMDD/cover.jpg by date convention is the fallback.
    cover = None
    og_image = first_match(OG_IMAGE_RE, text)
    if og_image and "/day_slides/" in og_image:
        rel = og_image.split("/day_slides/", 1)[1]
        if (DAY_DIR / rel).exists():
            cover = f"day_slides/{rel}"
    if cover is None:
        mmdd = date[5:7] + date[8:10]
        conventional = DAY_DIR / "images" / mmdd / "cover.jpg"
        if conventional.exists():
            cover = f"day_slides/images/{mmdd}/cover.jpg"

    cat, cat_label, by_section = classify(section, title, description)
    if cat == FALLBACK_CAT[0]:
        print(f"[meta_index] unclassified: {path.name} section={section!r} "
              f"title={title[:40]!r}", file=sys.stderr)

    return {
        "date": date,
        "file": path.name,
        "url": BASE_URL + path.name,
        "title": title,
        "description": description,
        "section": section,
        "cat": cat,
        "cat_label": cat_label,
        "cover": cover,
    }


def main() -> int:
    issues = []
    for path in sorted(DAY_DIR.glob("day_slide_*.html")):
        m = FILE_RE.match(path.name)
        if not m:
            continue
        date = "-".join(m.groups())
        issues.append(extract(path, date))

    if not issues:
        print("[meta_index] no day slides found", file=sys.stderr)
        return 1

    issues.sort(key=lambda x: x["date"])
    for no, issue in enumerate(issues, start=1):
        issue["no"] = no
    issues.reverse()  # newest first for consumers

    categories: dict[str, int] = {}
    for issue in issues:
        categories[issue["cat"]] = categories.get(issue["cat"], 0) + 1

    payload = {
        "generated_from": len(issues),
        "since": issues[-1]["date"],
        "latest": issues[0]["date"],
        "categories": categories,
        "issues": issues,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT} ({len(issues)} issues, categories: {categories})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
