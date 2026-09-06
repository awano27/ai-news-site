#!/usr/bin/env python3
"""Update marked homepage fallback dates to the newest existing slide.

Also refreshes the editorial sitrep strip (``<!-- fallback:sitrep -->``):
slide href is always pointed at the newest day_slide. Copy fields
(#sitrepUpdate / #sitrepDesk / #sitrepAction) stay as-is unless passed
on the CLI — they are human/editorial, not derived from a watchlist.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from html import escape, unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SLIDES = ROOT / "presentations" / "day_slides"
SLIDES_INDEX = ROOT / "presentations" / "day_slides_index.html"
MARKER_RE = re.compile(r"<!-- fallback:(?P<name>[\w-]+) -->(?P<body>.*?)<!-- fallback:end -->", re.S)
DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html")
FEAT_TITLE_RE = re.compile(
    r'href="(?:\.\./)?day_slides/day_slide_(\d{4})_(\d{2})_(\d{2})\.html"[^>]*>'
    r'.*?<h3 class="feat-title">(.*?)</h3>',
    re.S,
)
SLIDE_TITLE_RE = re.compile(
    r'href="(?:\.\./)?day_slides/day_slide_(\d{4})_(\d{2})_(\d{2})\.html"[^>]*>'
    r'.*?<span class="slide-title">(.*?)</span>',
    re.S,
)
MAX_TITLE_LENGTH = 120
WEEKDAYS_JP = "月火水木金土日"
MONTH_EN = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


def _plain_text(html_fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", html_fragment)
    return " ".join(unescape(text).split())


def extract_slide_title(slide_html: str) -> str | None:
    """Return a normalized slide title, preferring ``title`` over ``h1``."""
    for tag in ("title", "h1"):
        match = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", slide_html, re.I | re.S)
        if not match:
            continue
        text = re.sub(r"\s*(?:\|\s*)?\d{4}-\d{2}-\d{2}\s*$", "", _plain_text(match.group(1))).strip()
        if text and len(text) <= MAX_TITLE_LENGTH:
            return text
    return None


def extract_slide_twist(slide_html: str) -> str | None:
    """Canonical story sentence: slide ``h1`` only. Do not truncate."""
    match = re.search(r"<h1\b[^>]*>(.*?)</h1>", slide_html, re.I | re.S)
    if not match:
        return None
    heading = re.sub(r'<span\b[^>]*class=["\'][^"\']*hero-subtitle[^"\']*["\'][^>]*>.*?</span>', "", match.group(1), flags=re.I | re.S)
    heading = re.sub(r"<br\s*/?>", " ", heading, flags=re.I)
    text = re.sub(r"\s*(?:\|\s*)?\d{4}-\d{2}-\d{2}\s*$", "", _plain_text(heading)).strip()
    return text or None


def titles_from_index(html: str) -> dict[str, str]:
    """Map YYYY-MM-DD → official short title. feat-title wins over slide-title."""
    titles: dict[str, str] = {}
    for pattern in (SLIDE_TITLE_RE, FEAT_TITLE_RE):
        for year, month, day, raw in pattern.findall(html):
            text = _plain_text(raw)
            if text:
                titles[f"{year}-{month}-{day}"] = text
    return titles


def week_cards_html(newest: date, titles: dict[str, str]) -> str:
    cards: list[str] = []
    for offset in range(7):
        day = newest - timedelta(days=offset)
        iso = day.isoformat()
        stamp = day.strftime("%Y_%m_%d")
        title = titles.get(iso)
        weekday = WEEKDAYS_JP[day.weekday()]
        month = MONTH_EN[day.month - 1]
        is_today = offset == 0
        classes = "week-card" + (" is-today" if is_today else "") + ("" if title else " is-empty")
        flag = '<span class="today-flag">LATEST</span>' if is_today else ""
        if title:
            href = f'presentations/day_slides/day_slide_{stamp}.html'
            tag_open = f'<a class="{classes}" href="{href}">'
            tag_close = "</a>"
            go = "スライドを読む →"
            title_html = escape(title)
        else:
            tag_open = f'<div class="{classes}">'
            tag_close = "</div>"
            go = "更新なし"
            title_html = ""
        cards.append(
            f"{tag_open}{flag}"
            f'<span class="week-day">{month} · {weekday}曜</span>'
            f'<div class="week-date">{day.day:02d}</div>'
            f'<div class="week-title">{title_html}</div>'
            f'<span class="week-go">{go}</span>'
            f"{tag_close}"
        )
    return (
        '<div id="weekGrid" class="week-grid">\n          '
        + "\n          ".join(cards)
        + "\n        </div>"
    )


def extract_open_loop(slide_html: str) -> str | None:
    """Homepage one-liner from the slide meta description. Invent nothing."""
    match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
        slide_html,
        re.I,
    )
    if not match:
        return None
    text = " ".join(unescape(match.group(1)).split()).strip()
    return text or None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sitrep-update", default=None, help="Editorial 更新 line")
    parser.add_argument("--sitrep-desk", default=None, help="Editorial 日本デスク line")
    parser.add_argument("--sitrep-action", default=None, help="今日動かすのは line")
    parser.add_argument(
        "--sitrep-action-from-title",
        action="store_true",
        help="If --sitrep-action is omitted, fill #sitrepAction from the slide title",
    )
    return parser.parse_args([] if argv is None else argv)


def replace_marked_text(body: str, elem_id: str, text: str) -> str:
    display = escape(text)
    return re.sub(
        rf'(<(?:span|em|h1|h2|h3|p)\b[^>]*\bid="{elem_id}"[^>]*>).*?(</(?:span|em|h1|h2|h3|p)>)',
        lambda match: f"{match.group(1)}{display}{match.group(2)}",
        body,
        count=1,
        flags=re.S,
    )


def replace_element_text(body: str, elem_id: str, text: str) -> str:
    """Replace a dynamic element even when it is outside a fallback marker."""
    return replace_marked_text(body, elem_id, text)


def replace_href_by_id(body: str, elem_id: str, href: str) -> str:
    escaped_id = re.escape(elem_id)
    pattern = re.compile(
        rf'(<a\b(?=[^>]*\bid="{escaped_id}")[^>]*\bhref=")[^"]*(")',
        re.I,
    )
    return pattern.sub(rf'\g<1>{href}\g<2>', body, count=1)


def replace_anchor_label(body: str, elem_id: str, label: str) -> str:
    pattern = re.compile(
        rf'(<a\b(?=[^>]*\bid="{re.escape(elem_id)}")[^>]*>)(.*?)(</a>)', re.I | re.S)
    def replace(match):
        markers = "".join(re.findall(r"<!--[\s\S]*?-->", match.group(2)))
        return f"{match.group(1)}{markers}{escape(label)}{match.group(3)}"
    return pattern.sub(replace, body, count=1)


def empty_homepage_state(body: str) -> str:
    """Point every static slide entry at the list and expose an honest empty state."""
    if 'data-slides-unavailable="true"' not in body:
        body = body.replace('<html ', '<html data-slides-unavailable="true" ')
    list_url = "presentations/day_slides_index.html"
    body = replace_href_by_id(body, "latestSlideHeroBtn", list_url)
    body = replace_href_by_id(body, "heroSlideBtn", list_url)
    body = replace_href_by_id(body, "todaySlideCard", list_url)
    body = replace_href_by_id(body, "sitrepLink", list_url)
    body = re.sub(
        r'(\bhref=")presentations/day_slides/day_slide_\d{4}_\d{2}_\d{2}\.html(")',
        rf'\g<1>{list_url}\g<2>',
        body,
        flags=re.I,
    )
    body = replace_anchor_label(body, "latestSlideHeroBtn", "スライド一覧")
    body = replace_anchor_label(body, "heroSlideBtn", "スライド一覧")
    body = replace_element_text(body, "heroDate", "公開スライドなし")
    body = replace_element_text(body, "todaySlideDate", "公開スライドなし")
    body = replace_element_text(body, "heroTwist", "公開スライドはまだありません")
    body = replace_element_text(
        body,
        "heroWhy",
        "日次スライドが公開されると、ここに見出しと要点を表示します。",
    )
    body = re.sub(
        r'(<!-- fallback:this-week -->).*?(<!-- fallback:end -->)',
        r'\g<1><div id="weekGrid" class="week-grid"><div class="week-card is-empty">'
        r'<span class="week-day">公開スライドなし</span>'
        r'<div class="week-title">公開スライドはまだありません</div>'
        r'<span class="week-go">スライド一覧で確認</span></div></div>\g<2>',
        body,
        count=1,
        flags=re.I | re.S,
    )
    return body


def refresh_sitrep(body: str, stamp: str, slide_title: str | None, args: argparse.Namespace) -> str:
    body = body.replace("presentations/day_slides_index.html", f"presentations/day_slides/day_slide_{stamp}.html")
    body = re.sub(r"day_slide_\d{4}_\d{2}_\d{2}\.html", f"day_slide_{stamp}.html", body)
    if args.sitrep_update:
        body = replace_marked_text(body, "sitrepUpdate", args.sitrep_update)
    if args.sitrep_desk:
        body = replace_marked_text(body, "sitrepDesk", args.sitrep_desk)
    action = args.sitrep_action
    if action is None and args.sitrep_action_from_title and slide_title:
        action = slide_title
    if action:
        body = replace_marked_text(body, "sitrepAction", action)
    return body


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    slides = sorted(SLIDES.glob("day_slide_????_??_??.html"))
    if not slides:
        if INDEX.is_file():
            INDEX.write_text(empty_homepage_state(INDEX.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        print(f"[update_home_fallback] no day slides found at {SLIDES}; wrote honest homepage empty state", file=sys.stderr)
        return 0
    newest = slides[-1]
    match = DATE_RE.fullmatch(newest.name)
    assert match
    old = INDEX.read_text(encoding="utf-8")
    old_dates = sorted(set(re.findall(r"2026-07-06|day_slide_2026_07_06\.html", old)))
    iso, stamp = "-".join(match.groups()), "_".join(match.groups())
    slide_html = newest.read_text(encoding="utf-8")
    slide_title = extract_slide_title(slide_html)
    slide_twist = extract_slide_twist(slide_html)
    open_loop = extract_open_loop(slide_html)
    newest_day = date(*map(int, match.groups()))
    weekday = WEEKDAYS_JP[newest_day.weekday()]
    week_titles = titles_from_index(SLIDES_INDEX.read_text(encoding="utf-8")) if SLIDES_INDEX.is_file() else {}
    if slide_title:
        week_titles.setdefault(iso, slide_title)
    if "<!-- fallback:" not in old:
        lines=[]
        for line in old.splitlines(keepends=True):
            if "2026-07-06" in line or "day_slide_2026_07_06.html" in line:
                indent=re.match(r"\s*",line).group(0)
                line=indent+f"<!-- fallback:latest-slide -->"+line[len(indent):].rstrip("\r\n")+"<!-- fallback:end -->\n"
            lines.append(line)
        old="".join(lines)
    def refresh(marker):
        name = marker.group("name")
        if name == "sitrep":
            body = refresh_sitrep(marker.group("body"), stamp, slide_title, args)
            return f"<!-- fallback:{name} -->{body}<!-- fallback:end -->"
        if name == "this-week":
            return (
                f"<!-- fallback:this-week -->"
                f"{week_cards_html(newest_day, week_titles)}"
                f"<!-- fallback:end -->"
            )
        if name != "latest-slide":
            return marker.group(0)
        body = marker.group("body").replace(
            "presentations/day_slides_index.html",
            f"presentations/day_slides/day_slide_{stamp}.html",
        )
        body = re.sub(r"day_slide_\d{4}_\d{2}_\d{2}\.html", f"day_slide_{stamp}.html", body)
        body = re.sub(r"\d{4}-\d{2}-\d{2}", iso, body)
        if 'id="heroDate"' in body:
            body = re.sub(r"(?<= · )[月火水木金土日]", weekday, body)
        if slide_twist and 'id="heroTwist"' in body:
            body = replace_marked_text(body, "heroTwist", slide_twist)
        if open_loop and 'id="heroWhy"' in body:
            body = replace_marked_text(body, "heroWhy", open_loop)
        if slide_title:
            display_title = escape(slide_title)
            if 'id="heroNewsTitle"' in body:
                body = re.sub(
                    r'(<span\b[^>]*\bid="heroNewsTitle"[^>]*>).*?(</span>)',
                    lambda match: f"{match.group(1)}{display_title}{match.group(2)}",
                    body,
                    flags=re.S,
                )
            if 'class="rc-title"' in body:
                body = re.sub(
                    r'(<h3\b[^>]*\bclass="rc-title"[^>]*>).*?(</h3>)',
                    lambda match: f"{match.group(1)}{display_title}{match.group(2)}",
                    body,
                    flags=re.S,
                )
            if 'class="cat-title"' in body:
                body = re.sub(
                    r'(<div\b[^>]*\bclass="cat-title"[^>]*>).*?(</div>)',
                    lambda match: f"{match.group(1)}{display_title}{match.group(2)}",
                    body,
                    flags=re.S,
                )
            if 'class="ranking-card"' in body:
                aria_title = escape(f"1位: {slide_title}", quote=True)
                body = re.sub(r'aria-label="[^"]*"', f'aria-label="{aria_title}"', body, count=1)
            if "最新トピック:" in body:
                body = re.sub(
                    r"(最新トピック:\s*).*?(。\s*<a\b)",
                    lambda match: f"{match.group(1)}{display_title}{match.group(2)}",
                    body,
                    count=1,
                    flags=re.S,
                )
        return f'<!-- fallback:{marker.group("name")} -->{body}<!-- fallback:end -->'
    updated = MARKER_RE.sub(refresh, old)
    if 'data-slides-unavailable="true"' in updated:
        updated = updated.replace(' data-slides-unavailable="true"', '')
        updated = replace_anchor_label(updated, "latestSlideHeroBtn", "最新スライド →")
        updated = replace_anchor_label(updated, "heroSlideBtn", "最新スライドを読む →")
        for elem_id in ("latestSlideHeroBtn", "heroSlideBtn", "sitrepLink"):
            updated = replace_href_by_id(updated, elem_id, f"presentations/day_slides/{newest.name}")
        updated = replace_element_text(updated, "heroDate", f"{iso} · {weekday}")
        updated = replace_element_text(updated, "todaySlideDate", iso)
    # The new trends card keeps these IDs in its own markup. Update them by ID
    # as a narrow fallback even if the surrounding card is not marker-wrapped.
    if slide_twist:
        updated = replace_element_text(updated, "heroTwist", slide_twist)
    if open_loop:
        updated = replace_element_text(updated, "heroWhy", open_loop)
    INDEX.write_text(updated, encoding="utf-8", newline="\n")
    print(f"[update_home_fallback] latest={iso}, markers={len(MARKER_RE.findall(updated))}, legacy_tokens={old_dates}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
