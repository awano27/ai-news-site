#!/usr/bin/env python3
"""Update marked homepage fallback dates to the newest existing slide."""
from __future__ import annotations

import re
from datetime import date
from html import escape, unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SLIDES = ROOT / "presentations" / "day_slides"
MARKER_RE = re.compile(r"<!-- fallback:(?P<name>[\w-]+) -->(?P<body>.*?)<!-- fallback:end -->", re.S)
DATE_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})\.html")
MAX_TITLE_LENGTH = 120
WEEKDAYS_JP = "月火水木金土日"


def extract_slide_title(slide_html: str) -> str | None:
    """Return a normalized slide title, preferring ``title`` over ``h1``."""
    for tag in ("title", "h1"):
        match = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", slide_html, re.I | re.S)
        if not match:
            continue
        text = re.sub(r"<[^>]+>", " ", match.group(1))
        text = " ".join(unescape(text).split())
        text = re.sub(r"\s*(?:\|\s*)?\d{4}-\d{2}-\d{2}\s*$", "", text).strip()
        if text and len(text) <= MAX_TITLE_LENGTH:
            return text
    return None


def main() -> int:
    newest = max(SLIDES.glob("day_slide_????_??_??.html"))
    match = DATE_RE.fullmatch(newest.name)
    assert match
    old = INDEX.read_text(encoding="utf-8")
    old_dates = sorted(set(re.findall(r"2026-07-06|day_slide_2026_07_06\.html", old)))
    iso, stamp = "-".join(match.groups()), "_".join(match.groups())
    slide_title = extract_slide_title(newest.read_text(encoding="utf-8"))
    weekday = WEEKDAYS_JP[date(*map(int, match.groups())).weekday()]
    if "<!-- fallback:" not in old:
        lines=[]
        for line in old.splitlines(keepends=True):
            if "2026-07-06" in line or "day_slide_2026_07_06.html" in line:
                indent=re.match(r"\s*",line).group(0)
                line=indent+f"<!-- fallback:latest-slide -->"+line[len(indent):].rstrip("\r\n")+"<!-- fallback:end -->\n"
            lines.append(line)
        old="".join(lines)
    def refresh(marker):
        if marker.group("name") != "latest-slide":
            return marker.group(0)
        body = re.sub(r"day_slide_\d{4}_\d{2}_\d{2}\.html", f"day_slide_{stamp}.html", marker.group("body"))
        body = re.sub(r"\d{4}-\d{2}-\d{2}", iso, body)
        if 'id="heroDate"' in body:
            body = re.sub(r"(?<= · )[月火水木金土日]", weekday, body)
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
    INDEX.write_text(updated, encoding="utf-8", newline="\n")
    print(f"[update_home_fallback] latest={iso}, markers={len(MARKER_RE.findall(updated))}, legacy_tokens={old_dates}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
