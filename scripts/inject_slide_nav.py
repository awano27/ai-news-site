#!/usr/bin/env python3
"""Inject idempotent navigation into every dated day slide."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "presentations" / "day_slides"
START, END = "<!-- slide-nav:start -->", "<!-- slide-nav:end -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html$")
InjectionStatus = Literal["changed", "unchanged", "skipped-no-body"]


def build_block(
    path: Path,
    previous: Path | None,
    following: Path | None,
    *,
    had_report_link: bool = False,
    had_news_link: bool = False,
) -> str:
    match = DATE_RE.search(path.name)
    assert match
    iso = "-".join(match.groups())
    stamp = "_".join(match.groups())
    links = []
    if previous:
        links.append((previous.name, "← 前日"))
    links.extend((("../day_slides_index.html", "一覧"), ("/", "ホーム")))
    report = ROOT / "presentations" / "daily_reports" / f"auto_daily_report_{stamp}.html"
    news = ROOT / "daily-news" / "archive" / f"{iso}.html"
    # exists() reflects whichever machine runs this script, which can differ
    # (local PC vs. cloud CI vs. another worktree). Once a link has been
    # committed, keep it even if this run can't see the file locally, so
    # repeated runs across environments converge instead of flapping.
    if report.exists() or had_report_link:
        links.append((f"../daily_reports/{report.name}", "同日のレポート"))
    if news.exists() or had_news_link:
        links.append((f"../../daily-news/archive/{news.name}", "同日のニュース"))
    links.append((following.name, "翌日 →") if following else ("../day_slides_index.html", "一覧へ"))
    anchors = "".join(
        f'<a href="{href}" style="display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:8px 14px;border:1px solid rgba(255,255,255,.35);border-radius:999px;color:#fff;text-decoration:none;font:600 14px/1.2 sans-serif;white-space:nowrap">{label}</a>'
        for href, label in links
    )
    return f'{START}\n<nav aria-label="スライド相互ナビゲーション" style="box-sizing:border-box;width:min(100% - 24px,1100px);margin:24px auto;padding:12px;background:rgba(5,12,25,.88);border:1px solid rgba(255,255,255,.22);border-radius:14px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px;overflow:hidden">{anchors}</nav>\n{END}'


def inject(path: Path, block: str) -> InjectionStatus:
    text = path.read_text(encoding="utf-8")
    if not re.search(r"</body>", text, flags=re.I):
        return "skipped-no-body"
    if START in text:
        updated = BLOCK_RE.sub(block, text, count=1)
    else:
        updated = re.sub(r"</body>", block + "\n</body>", text, count=1, flags=re.I)
    if updated == text:
        return "unchanged"
    path.write_text(updated, encoding="utf-8", newline="\n")
    return "changed"


def existing_links(path: Path) -> tuple[bool, bool]:
    match = BLOCK_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        return False, False
    block = match.group(0)
    return "同日のレポート" in block, "同日のニュース" in block


def main() -> int:
    slides = sorted(SLIDES.glob("day_slide_????_??_??.html"))
    changed = 0
    skipped = 0
    for i, path in enumerate(slides):
        had_report_link, had_news_link = existing_links(path)
        status = inject(
            path,
            build_block(
                path,
                slides[i - 1] if i else None,
                slides[i + 1] if i + 1 < len(slides) else None,
                had_report_link=had_report_link,
                had_news_link=had_news_link,
            ),
        )
        if status == "changed":
            changed += 1
        elif status == "skipped-no-body":
            skipped += 1
            print(f"[inject_slide_nav] {path}: skipped (no </body>)")
    print(f"[inject_slide_nav] {len(slides)} files, {changed} changed, {skipped} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
