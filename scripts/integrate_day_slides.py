#!/usr/bin/env python3
"""Add the day slides that meta_index.json does not list to the curated hub files.

    python scripts/integrate_day_slides.py [--root PATH] [--topics STAMP=name,...] [--dry]

Updates meta_index.json, list.json, day_slides_index.html and llms.txt. Rerunning changes
nothing. Afterwards run script/build_day_slides_list.py, scripts/build_feed.py,
scripts/update_home_fallback.py and node scripts/build-homepage-latest.js.
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SLIDES = Path("presentations", "day_slides")
META = SLIDES / "meta_index.json"
LIST = SLIDES / "list.json"
INDEX = Path("presentations", "day_slides_index.html")
LLMS = Path("llms.txt")
# meta_index.json goes last: discovery keys off it, so a run cut short is redone in full.
WRITE_ORDER = (LIST, INDEX, LLMS, META)
BASE_URL = "https://visionhub.jp/presentations/day_slides/"
ISSUE_KEYS = ("date", "no", "file", "url", "title", "description", "section", "cat", "cat_label", "cover")
SLIDE_FILE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html")
CARD = '<a class="slide-card"'


class IntegrationError(Exception):
    pass


@dataclass(frozen=True)
class Slide:
    date: str
    no: int
    file: str
    url: str
    title: str
    description: str
    section: str
    cat: str
    cat_label: str
    cover: str | None
    short: str

    def issue(self) -> dict:
        return {key: getattr(self, key) for key in ISSUE_KEYS}


@dataclass(frozen=True)
class Plan:
    slides: list[Slide]
    meta: dict
    cards: int | None
    changes: dict[Path, str]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise IntegrationError(f"missing {path}") from None


def read_json(path: Path):
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"{path.name}: {exc}") from None


def dump_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def short_title(page: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", page, re.S)
    if not match:
        return None
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).split())
    return re.sub(r"\s*(?:\|\s*)?\d{4}-\d{2}-\d{2}\s*$", "", text.split(" | ")[0]).strip()


def short_title_of(root: Path, file: str) -> str:
    title = short_title(read_text(root / SLIDES / file))
    if title is None:
        raise IntegrationError(f"{file}: no <title> on the page")
    return title


def load_index_builder(root: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_day_slides_index", root / "script" / "build_day_slides_index.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover(root: Path, meta: dict) -> list[Slide]:
    listed = {issue["date"] for issue in meta["issues"]}
    pending = []
    for path in sorted((root / SLIDES).glob("day_slide_????_??_??.html")):
        match = SLIDE_FILE.fullmatch(path.name)
        if not match:
            continue
        date = "-".join(match.groups())
        if date not in listed:
            pending.append((path, date))
    if not pending:
        return []
    builder = load_index_builder(root)
    slides = []
    for path, date in pending:
        number = re.search(r"No\.\s?(\d+)", read_text(path))
        if not number:
            raise IntegrationError(f"{path.name}: no 'No.NNN' on the page; cannot assign an issue number")
        issue = {**builder.extract(path, date), "no": int(number.group(1))}
        slides.append(Slide(**{key: issue[key] for key in ISSUE_KEYS}, short=short_title_of(root, path.name)))
    taken = {issue["no"] for issue in meta["issues"]}
    numbers = Counter(slide.no for slide in slides)
    clashes = sorted(no for no, count in numbers.items() if no in taken or count > 1)
    if clashes:
        raise IntegrationError(f"issue number collision: {clashes}")
    return slides


def insert_newest_first(rows: list[dict], row: dict) -> None:
    rows.insert(next((i for i, other in enumerate(rows) if other["date"] < row["date"]), len(rows)), row)


def updated_meta(meta: dict, slides: list[Slide]) -> dict:
    issues = list(meta["issues"])
    for slide in slides:
        insert_newest_first(issues, slide.issue())
    counts = Counter(issue["cat"] for issue in issues)
    order = [*meta["categories"], *(cat for cat in counts if cat not in meta["categories"])]
    return {
        **meta,
        "generated_from": max(issue["no"] for issue in issues),
        "latest": max(issue["date"] for issue in issues),
        "categories": {cat: counts[cat] for cat in order if counts[cat]},
        "issues": issues,
    }


def updated_list(entries: list[dict], slides: list[Slide]) -> list[dict]:
    entries = list(entries)
    listed = {entry["date"] for entry in entries}
    for slide in slides:
        if slide.date not in listed:
            label = f"{int(slide.date[5:7])}/{int(slide.date[8:10])} - {slide.short}"
            insert_newest_first(entries, {"date": slide.date, "url": f"day_slides/{slide.file}", "label": label})
    return entries


def prepend_card(page: str, slide: Slide) -> str:
    month = slide.date[:7]
    group = re.search(
        rf'(<details class="month-group"[^>]*data-month="{month}">.*?<div class="slides-grid">)(\s*)', page, re.S
    )
    if not group:
        raise IntegrationError(f"month group {month} not found in {INDEX.name}")
    sep = group.group(2)
    card = (
        f'{CARD} href="day_slides/{slide.file}"><span class="slide-date">{slide.date[5:].replace("-", "/")}</span>'
        f'<span class="slide-title">{html.escape(slide.short, quote=False)}</span></a>'
    )
    return page[: group.end(1)] + sep + card + (sep if "\n" in sep else "") + page[group.end() :]


def recount(group: re.Match) -> str:
    block = group.group(0)
    return re.sub(r'(<span class="month-count">)\d+( 件</span>)', rf"\g<1>{block.count(CARD)}\g<2>", block, count=1)


def replace_once(page: str, pattern: str, new: str, what: str) -> str:
    match = re.search(pattern, page)
    if not match:
        raise IntegrationError(f"{what} not found in {INDEX.name}")
    old = match.group(0)
    if page.count(old) != 1:
        raise IntegrationError(f"expected 1x {old[:70]!r}, found {page.count(old)}")
    return page.replace(old, new)


def with_featured(page: str, top: list[dict], titles: list[str]) -> str:
    grid = re.search(r'(<div class="featured-grid">\n)(.*?)(        </div>\n      </div>\n    </section>)', page, re.S)
    if not grid:
        raise IntegrationError(f"featured-grid not found in {INDEX.name}")
    cards = "".join(
        f'          <a class="feat-card" href="day_slides/{issue["file"]}">\n'
        f'            <div class="feat-tag"><span class="dot"></span>{"LATEST" if rank == 0 else "RECENT"}</div>\n'
        f'            <div class="feat-date">{issue["date"].replace("-", "/")}</div>\n'
        f'            <h3 class="feat-title">{html.escape(title, quote=False)}</h3>\n'
        '            <span class="feat-cta">スライドを見る <span class="arr" aria-hidden="true">&rarr;</span></span>\n'
        "          </a>\n"
        for rank, (issue, title) in enumerate(zip(top, titles))
    )
    return page[: grid.start(2)] + cards + page[grid.end(2) :]


def updated_index(
    page: str, issues: list[dict], slides: list[Slide], title_of: Callable[[str], str], topics: dict[str, str]
) -> tuple[str, int]:
    for slide in reversed(slides):
        if f'{CARD} href="day_slides/{slide.file}"' not in page:
            page = prepend_card(page, slide)
    page = re.sub(r'<details class="month-group"[^>]*data-month="\d{4}-\d{2}">.*?</details>', recount, page, flags=re.S)
    cards = page.count(CARD)
    newest, top = issues[0], issues[:3]
    page = replace_once(
        page,
        r'<a class="cta" href="day_slides/day_slide_\d{4}_\d{2}_\d{2}\.html">',
        f'<a class="cta" href="day_slides/{newest["file"]}">',
        "CTA link",
    )
    page = re.sub(
        r'(<div class="stat-num">)\d+(</div>\s*<span class="stat-label">Total Slides)',
        rf"\g<1>{cards}\g<2>",
        page,
        count=1,
    )
    page = re.sub(
        r'(<div class="stat-num">)\d{4}/\d{2}/\d{2}(</div>\s*<span class="stat-label">Latest Update)',
        rf"\g<1>{newest['date'].replace('-', '/')}\g<2>",
        page,
        count=1,
    )
    page = re.sub(
        r'(<strong id="filterCount">)\d+(</strong> / <span id="filterTotal">)\d+(</span>)',
        rf"\g<1>{cards}\g<2>{cards}\g<3>",
        page,
        count=1,
    )
    page = with_featured(page, top, [title_of(issue["file"]) for issue in top])
    names = [topics.get(issue["date"].replace("-", "_"), "") for issue in top]
    if all(names):
        joined = "、".join(html.escape(name, quote=False) for name in names)
        page = replace_once(
            page,
            r'<p class="section-sub">[^<]*最新3本を読む。</p>',
            f'<p class="section-sub">{joined}の最新3本を読む。</p>',
            "featured sub line",
        )
    return page, cards


def updated_llms(text: str, issues: list[dict], title_of: Callable[[str], str]) -> str:
    today = re.search(r"- \[Today's day slide\]\(([^)]*)\): ([^\n]*)\n", text)
    if not today:
        raise IntegrationError("Today's line not found in llms.txt")
    stamp = SLIDE_FILE.search(today.group(1))
    if not stamp:
        raise IntegrationError(f"Today's line in llms.txt links no day slide: {today.group(1)}")
    previous = "-".join(stamp.groups())
    by_date = {issue["date"]: issue for issue in issues}
    newest = max(by_date)
    if newest <= previous:
        return text
    listed = set(re.findall(r"- \[Recent day slide (\d{4}-\d{2}-\d{2})\]", text))
    lines = [f"- [Today's day slide]({BASE_URL}{by_date[newest]['file']}): {title_of(by_date[newest]['file'])}\n"]
    for date in sorted((d for d in by_date if previous <= d < newest), reverse=True):
        if date not in listed:
            note = today.group(2) if date == previous else title_of(by_date[date]["file"])
            lines.append(f"- [Recent day slide {date}]({BASE_URL}{by_date[date]['file']}): {note}\n")
    return text[: today.start()] + "".join(lines) + text[today.end() :]


def plan(root: Path, topics: dict[str, str]) -> Plan:
    meta = read_json(root / META)
    slides = discover(root, meta)
    title_of = partial(short_title_of, root)
    texts: dict[Path, str] = {}
    cards = None
    if slides:
        meta = updated_meta(meta, slides)
        texts[META] = dump_json(meta)
        texts[LIST] = dump_json(updated_list(read_json(root / LIST), slides))
        texts[INDEX], cards = updated_index(read_text(root / INDEX), meta["issues"], slides, title_of, topics)
    texts[LLMS] = updated_llms(read_text(root / LLMS), meta["issues"], title_of)
    changes = {
        rel: texts[rel]
        for rel in WRITE_ORDER
        if rel in texts and (root / rel).read_bytes() != texts[rel].encode("utf-8")
    }
    return Plan(slides, meta, cards, changes)


def write(root: Path, changes: dict[Path, str]) -> None:
    for rel, text in changes.items():
        (root / rel).write_text(text, encoding="utf-8", newline="\n")


def report(result: Plan, dry: bool) -> None:
    if result.slides:
        print(f"{len(result.slides)} slide(s) missing from meta_index.json:")
        for slide in result.slides:
            print(f"  {slide.date} No.{slide.no} {slide.cat} {slide.short}")
        meta = result.meta
        print(
            f"index cards {result.cards}; meta latest {meta['latest']}, "
            f"generated_from {meta['generated_from']}; categories {meta['categories']}"
        )
    else:
        print("nothing to integrate: meta_index.json lists every day slide")
    if LLMS not in result.changes:
        print("llms.txt already current")
    else:
        print("llms.txt needs an update" if dry else "llms.txt updated")
    for rel in result.changes:
        print(f"{'would write' if dry else 'wrote'} {rel.as_posix()}")


def parse_topics(spec: str) -> dict[str, str]:
    return dict(item.split("=", 1) for item in spec.split(",") if "=" in item)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT, help="checkout to update (default: this repository)")
    parser.add_argument(
        "--topics",
        default="",
        help="names for the featured sub line when slides are integrated, "
        "e.g. 2026_10_05=Copilot Computer Use,2026_10_04=Kolibri-1",
    )
    parser.add_argument("--dry", action="store_true", help="report the changes without writing them")
    args = parser.parse_args(argv)
    try:
        result = plan(args.root, parse_topics(args.topics))
    except IntegrationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not args.dry:
        write(args.root, result.changes)
    report(result, args.dry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
