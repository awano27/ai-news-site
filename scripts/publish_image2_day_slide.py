#!/usr/bin/env python3
r"""Publish an image2-generated daily slide deck.

This script turns a completed workspace/MMDD-image2-brand-slides run into the
static files served by visionhub.jp:

* presentations/day_slides/day_slide_YYYY_MM_DD.html
* presentations/day_slides/images/MMDD/cover.jpg, p01.jpg, ...
* presentations/day_slides/downloads/day_slide_YYYY_MM_DD_<slug>.pptx
* presentations/day_slides_index.html
* presentations/day_slides_list.html
* sitemap.xml

Typical use from a clean worktree:

    python scripts/publish_image2_day_slide.py 0624 ^
      --workspace C:\develop\ai-news-site\workspace\0624-image2-brand-slides ^
      --input-text C:\develop\ai-news-site\input\day\0624slide.txt ^
      --title "Readable public title" ^
      --stage --commit --push
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import date
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - exercised only on bad local envs
    raise SystemExit(
        "Pillow is required. Install the repo requirements before publishing."
    ) from exc


BASE_URL = "https://visionhub.jp"


@dataclass(frozen=True)
class PublishPlan:
    mmdd: str
    day: date
    title: str
    summary: str
    section: str
    slug: str
    workspace: Path
    image_sources: list[Path]
    pptx_source: Path
    page_path: Path
    pptx_path: Path
    image_dir: Path
    image_paths: list[Path]
    index_path: Path
    list_path: Path
    sitemap_path: Path

    @property
    def date_slug(self) -> str:
        return self.day.strftime("%Y_%m_%d")

    @property
    def date_dash(self) -> str:
        return self.day.isoformat()

    @property
    def date_slash(self) -> str:
        return self.day.strftime("%Y/%m/%d")

    @property
    def rel_page_href(self) -> str:
        return f"day_slides/day_slide_{self.date_slug}.html"

    @property
    def abs_page_url(self) -> str:
        return f"{BASE_URL}/presentations/day_slides/day_slide_{self.date_slug}.html"


class RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []
        self.figure_count = 0
        self.image_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k: v for k, v in attrs if v is not None}
        if tag == "figure":
            self.figure_count += 1
        if tag == "img":
            self.image_count += 1
            if values.get("src"):
                self.refs.append(("src", values["src"]))
        if tag == "a" and values.get("href"):
            self.refs.append(("href", values["href"]))


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mmdd", help="Target date in MMDD form, for example 0624")
    ap.add_argument("--year", type=int, default=date.today().year)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--workspace", type=Path)
    ap.add_argument("--images-dir", type=Path)
    ap.add_argument("--pptx", type=Path)
    ap.add_argument("--input-text", type=Path)
    ap.add_argument("--title")
    ap.add_argument("--summary")
    ap.add_argument("--section", default="AI Architecture")
    ap.add_argument("--slug")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stage", action="store_true", help="git add only the published files")
    ap.add_argument("--commit", action="store_true", help="commit the staged published files")
    ap.add_argument("--push", action="store_true", help="push HEAD:main after committing")
    ap.add_argument("--message", help="commit message override")
    return ap.parse_args()


def require_mmdd(mmdd: str) -> tuple[int, int]:
    if not re.fullmatch(r"\d{4}", mmdd):
        raise SystemExit("MMDD must be four digits, for example 0624")
    month = int(mmdd[:2])
    day_num = int(mmdd[2:])
    if not (1 <= month <= 12 and 1 <= day_num <= 31):
        raise SystemExit(f"Invalid MMDD: {mmdd}")
    return month, day_num


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", unescape(value)).strip()


def compact(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "..."


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"^\d{4}[-_]", "", value)
    value = re.sub(r"_?image2_?rebuilt$", "", value)
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "daily_slide"


def sort_image_key(path: Path) -> tuple[int, str]:
    match = re.match(r"(\d+)", path.stem)
    return (int(match.group(1)) if match else 9999, path.name)


def find_single_pptx(workspace: Path) -> Path:
    matches = sorted(workspace.glob("*_image2_rebuilt.pptx"))
    if len(matches) != 1:
        raise SystemExit(
            f"Expected one *_image2_rebuilt.pptx in {workspace}, found {len(matches)}"
        )
    return matches[0]


def read_title_summary(input_text: Path | None, title: str | None, summary: str | None) -> tuple[str, str]:
    if title and summary:
        return title, summary
    lines: list[str] = []
    if input_text and input_text.exists():
        lines = [line.strip() for line in input_text.read_text(encoding="utf-8").splitlines()]
    nonempty = [line for line in lines if line]
    inferred_title = title or (nonempty[0] if nonempty else "Daily AI Slide")
    inferred_summary = summary
    if not inferred_summary:
        for line in nonempty[1:]:
            if "サマリー" in line or line.lower().startswith("executive"):
                continue
            if re.fullmatch(r"\d+\. .*", line):
                continue
            inferred_summary = compact(line, 180)
            break
    return compact(inferred_title, 90), inferred_summary or f"{inferred_title}."


def read_slide_titles(workspace: Path, image_sources: list[Path], cover_title: str) -> list[str]:
    titles_path = workspace / "titles.json"
    title_by_file: dict[str, str] = {}
    if titles_path.exists():
        try:
            data = json.loads(titles_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("file") and item.get("title"):
                        title_by_file[str(item["file"])] = str(item["title"])
        except json.JSONDecodeError:
            pass
    titles: list[str] = []
    for i, source in enumerate(image_sources):
        if i == 0:
            titles.append(cover_title)
        else:
            titles.append(title_by_file.get(source.name, f"Slide {i:02d}"))
    return titles


def make_plan(args: argparse.Namespace) -> PublishPlan:
    month, day_num = require_mmdd(args.mmdd)
    target_day = date(args.year, month, day_num)
    repo = args.repo_root.resolve()
    workspace = (args.workspace or repo / "workspace" / f"{args.mmdd}-image2-brand-slides").resolve()
    images_dir = (args.images_dir or workspace / "image2-fixed").resolve()
    if not images_dir.exists():
        raise SystemExit(f"Image directory not found: {images_dir}")
    image_sources = sorted(
        [p for p in images_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"}],
        key=sort_image_key,
    )
    if not image_sources:
        raise SystemExit(f"No slide images found in {images_dir}")
    pptx_source = (args.pptx.resolve() if args.pptx else find_single_pptx(workspace))
    input_text = args.input_text
    if input_text is None:
        candidates = [
            repo / "input" / "day" / f"{args.mmdd}slide.txt",
            repo / "input" / "day" / f"{args.mmdd}.txt",
        ]
        input_text = next((p for p in candidates if p.exists()), None)
    title, summary = read_title_summary(input_text, args.title, args.summary)
    slug = args.slug or slugify(pptx_source.stem)

    date_slug = target_day.strftime("%Y_%m_%d")
    image_dir = repo / "presentations" / "day_slides" / "images" / args.mmdd
    image_paths = [
        image_dir / ("cover.jpg" if i == 0 else f"p{i:02d}.jpg")
        for i in range(len(image_sources))
    ]
    return PublishPlan(
        mmdd=args.mmdd,
        day=target_day,
        title=title,
        summary=summary,
        section=args.section,
        slug=slug,
        workspace=workspace,
        image_sources=image_sources,
        pptx_source=pptx_source,
        page_path=repo / "presentations" / "day_slides" / f"day_slide_{date_slug}.html",
        pptx_path=repo / "presentations" / "day_slides" / "downloads" / f"day_slide_{date_slug}_{slug}.pptx",
        image_dir=image_dir,
        image_paths=image_paths,
        index_path=repo / "presentations" / "day_slides_index.html",
        list_path=repo / "presentations" / "day_slides_list.html",
        sitemap_path=repo / "sitemap.xml",
    )


def render_html(plan: PublishPlan, slide_titles: list[str]) -> str:
    title = escape(plan.title)
    summary = escape(plan.summary)
    json_headline = json.dumps(plan.title, ensure_ascii=False)
    json_summary = json.dumps(plan.summary, ensure_ascii=False)
    image_url = f"{BASE_URL}/presentations/day_slides/images/{plan.mmdd}/cover.jpg"
    figures = []
    for out_path, caption in zip(plan.image_paths, slide_titles, strict=True):
        rel_img = f"images/{plan.mmdd}/{out_path.name}"
        escaped_caption = escape(caption)
        figures.append(
            f"""      <figure>
        <img src="{rel_img}" alt="{escaped_caption}" loading="lazy" width="1672" height="941">
        <figcaption>{escaped_caption}</figcaption>
      </figure>"""
        )
    figures_html = "\n".join(figures)
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | {plan.date_dash}</title>
  <meta name="description" content="{summary}">
  <link rel="canonical" href="{plan.abs_page_url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="AI Intelligence Hub">
  <meta property="og:title" content="{title} | {plan.date_dash}">
  <meta property="og:description" content="{summary}">
  <meta property="og:url" content="{plan.abs_page_url}">
  <meta property="og:image" content="{image_url}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{summary}">
  <meta name="twitter:image" content="{image_url}">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "PresentationDigitalDocument",
    "headline": {json_headline},
    "description": {json_summary},
    "datePublished": "{plan.date_dash}",
    "dateModified": "{plan.date_dash}",
    "image": ["{image_url}"],
    "mainEntityOfPage": "{plan.abs_page_url}",
    "articleSection": "{escape(plan.section)}"
  }}
  </script>
  <style>
    :root {{ --bg:#f4f0e8; --paper:#fffaf0; --ink:#18212d; --muted:#65717f; --line:#dfd6c7; --accent:#2f8ea3; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:"Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif; }}
    .shell {{ max-width: 1696px; margin:0 auto; padding:28px 20px 56px; }}
    .topbar {{ display:flex; justify-content:space-between; gap:18px; align-items:center; margin-bottom:24px; color:var(--muted); font-size:13px; }}
    .topbar a {{ color:var(--accent); text-decoration:none; }}
    .hero {{ border:1px solid var(--line); background:rgba(255,250,240,.82); padding:26px; margin-bottom:22px; }}
    .kicker {{ color:var(--accent); font-size:13px; letter-spacing:.08em; text-transform:uppercase; margin-bottom:10px; }}
    h1 {{ font-size:clamp(30px,4vw,54px); line-height:1.2; margin:0 0 14px; font-weight:700; letter-spacing:0; }}
    .lead {{ max-width:80ch; color:var(--muted); font-size:16px; margin:0; line-height:1.75; }}
    .actions {{ margin-top:20px; display:flex; flex-wrap:wrap; gap:12px; }}
    .download {{ display:inline-flex; justify-content:center; align-items:center; min-height:44px; padding:0 18px; border:1px solid var(--accent); color:white; background:var(--accent); text-decoration:none; font-weight:700; }}
    .slides {{ display:grid; gap:22px; }}
    figure {{ margin:0; border:1px solid var(--line); background:var(--paper); padding:14px; }}
    img {{ width:100%; height:auto; display:block; }}
    figcaption {{ color:var(--muted); font-size:13px; margin-top:10px; }}
    @media (max-width:860px) {{ .shell {{ padding:18px 10px 40px; }} .hero {{ padding:18px; }} figure {{ padding:8px; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <nav class="topbar">
      <a href="../day_slides_index.html">All day slides</a>
      <span>{plan.date_dash} / {escape(plan.section)}</span>
    </nav>
    <section class="hero">
      <div class="kicker">Daily AI Architecture Slide</div>
      <h1>{title}</h1>
      <p class="lead">{summary}</p>
      <div class="actions">
        <a class="download" href="downloads/{plan.pptx_path.name}" download>Download PPTX</a>
      </div>
    </section>
    <section class="slides" aria-label="Slide images">
{figures_html}
    </section>
  </main>
</body>
</html>
"""


def convert_images(plan: PublishPlan) -> None:
    plan.image_dir.mkdir(parents=True, exist_ok=True)
    for source, dest in zip(plan.image_sources, plan.image_paths, strict=True):
        with Image.open(source) as im:
            rgb = im.convert("RGB")
            rgb.save(dest, "JPEG", quality=92, optimize=True)


def copy_pptx(plan: PublishPlan) -> None:
    plan.pptx_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan.pptx_source, plan.pptx_path)


def feature_card(plan: PublishPlan, latest: bool = True) -> str:
    latest_html = '            <div class="feat-tag"><span class="dot"></span>LATEST</div>\n' if latest else ""
    return f"""          <a class="feat-card" href="{plan.rel_page_href}">
{latest_html}            <div class="feat-date">{plan.date_slash}</div>
            <h3 class="feat-title">{escape(plan.title)}</h3>
            <span class="feat-cta">View slide <span class="arr" aria-hidden="true">&rarr;</span></span>
          </a>
"""


def slide_card(plan: PublishPlan) -> str:
    title = escape(compact(f"{plan.title} / {plan.summary}", 260))
    return (
        f'              <a class="slide-card" href="{plan.rel_page_href}">'
        f'<span class="slide-date">{plan.day.strftime("%m/%d")}</span>'
        f'<span class="slide-title">{title}</span></a>\n'
    )


def increment_stat(text: str, label: str, amount: int) -> str:
    if amount == 0:
        return text
    pattern = re.compile(
        rf'(<div class="stat-card">\s*<div class="stat-num">)(\d+)(</div>\s*<span class="stat-label">{re.escape(label)}</span>)',
        re.S,
    )
    return pattern.sub(lambda m: f"{m.group(1)}{int(m.group(2)) + amount}{m.group(3)}", text, count=1)


def set_latest_update(text: str, plan: PublishPlan) -> str:
    pattern = re.compile(
        r'(<div class="stat-card">\s*<div class="stat-num">)\d{4}/\d{2}/\d{2}(</div>\s*<span class="stat-label">Latest Update</span>)',
        re.S,
    )
    return pattern.sub(rf"\g<1>{plan.date_slash}\2", text, count=1)


def set_filter_count(text: str, amount: int) -> str:
    if amount == 0:
        return text
    pattern = re.compile(r'(<strong id="filterCount">)(\d+)(</strong> / )(\d+)( 件)')
    return pattern.sub(
        lambda m: f"{m.group(1)}{int(m.group(2)) + amount}{m.group(3)}{int(m.group(4)) + amount}{m.group(5)}",
        text,
        count=1,
    )


def update_featured(text: str, plan: PublishPlan) -> str:
    existing_titles = [
        strip_tags(title)
        for href, title in re.findall(
            r'<a class="feat-card" href="([^"]+)">.*?<h3 class="feat-title">(.*?)</h3>.*?</a>',
            text,
            flags=re.S,
        )
        if href != plan.rel_page_href
    ]
    sub_titles = [compact(plan.title.split(" / ")[0], 28)]
    sub_titles.extend(compact(t.split(" / ")[0], 28) for t in existing_titles[:2])
    section_sub = "直近のスライドをハイライト。" + "、".join(sub_titles[:3]) + "など。"
    text = re.sub(
        r'<p class="section-sub">.*?</p>',
        f'<p class="section-sub">{escape(section_sub)}</p>',
        text,
        count=1,
        flags=re.S,
    )
    current_card = re.compile(
        rf'\n\s*<a class="feat-card" href="{re.escape(plan.rel_page_href)}">.*?</a>\s*',
        re.S,
    )
    text = current_card.sub("\n", text)
    text = re.sub(
        r'\n\s*<div class="feat-tag"><span class="dot"></span>LATEST</div>',
        "",
        text,
        count=1,
    )
    marker = '        <div class="featured-grid">\n'
    if marker not in text:
        raise SystemExit("Could not find featured-grid in day_slides_index.html")
    return text.replace(marker, marker + feature_card(plan), 1)


def update_month_archive(text: str, plan: PublishPlan, was_present: bool) -> str:
    text = re.sub(
        rf'\n\s*<a class="slide-card" href="{re.escape(plan.rel_page_href)}">.*?</a>\s*',
        "\n",
        text,
        flags=re.S,
    )
    month_key = plan.day.strftime("%Y-%m")
    group_pattern = re.compile(
        rf'(?P<head><details class="month-group"[^>]*data-month="{month_key}"[^>]*>.*?'
        rf'<span class="month-count">)(?P<count>\d+)(?P<count_tail> 件</span>.*?'
        rf'<div class="slides-grid">\n)(?P<body>.*?)(?P<tail>\s+</div>\n\s+</details>)',
        re.S,
    )
    match = group_pattern.search(text)
    if match:
        new_count = int(match.group("count")) + (0 if was_present else 1)
        replacement = (
            f"{match.group('head')}{new_count}{match.group('count_tail')}"
            f"{slide_card(plan)}{match.group('body')}{match.group('tail')}"
        )
        return text[: match.start()] + replacement + text[match.end() :]

    month_title = f"{plan.day.year}年 {plan.day.month}月"
    new_group = f"""          <details class="month-group" open data-month="{month_key}">
            <summary class="month-header">
              <div class="month-label">
                <svg class="month-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5 3l6 5-6 5V3z"/></svg>
                <span class="month-title">{month_title}</span>
              </div>
              <span class="month-count">1 件</span>
            </summary>
            <div class="slides-grid">
{slide_card(plan)}            </div>
          </details>
"""
    marker = '        <div id="archiveList">\n'
    if marker not in text:
        raise SystemExit("Could not find archiveList in day_slides_index.html")
    return increment_stat(text.replace(marker, marker + new_group, 1), "Months Covered", 1)


def update_index(plan: PublishPlan) -> None:
    text = plan.index_path.read_text(encoding="utf-8")
    was_present = plan.rel_page_href in text
    text = increment_stat(text, "Total Slides", 0 if was_present else 1)
    text = set_latest_update(text, plan)
    text = set_filter_count(text, 0 if was_present else 1)
    text = update_featured(text, plan)
    text = update_month_archive(text, plan, was_present)
    plan.index_path.write_text(text, encoding="utf-8")


def update_list(plan: PublishPlan) -> None:
    """Regenerate day_slides_list.html (AI NEWSSTAND page) from on-disk decks.

    The list page is a full static rebuild driven by each deck's own metadata
    (og:title / description / articleSection / og:image), so publishing a new
    deck only requires re-running the two builders; no in-place regex edits.
    """
    repo_root = plan.list_path.parent.parent
    for builder in ("build_day_slides_index.py", "build_day_slides_list.py"):
        subprocess.run(
            [sys.executable, str(repo_root / "script" / builder)],
            check=True,
        )


def update_sitemap(plan: PublishPlan) -> None:
    text = plan.sitemap_path.read_text(encoding="utf-8")
    loc = plan.abs_page_url
    block_pattern = re.compile(
        rf'\n  <url>\n    <loc>{re.escape(loc)}</loc>\n    <lastmod>.*?</lastmod>\n'
        rf'    <changefreq>.*?</changefreq>\n    <priority>.*?</priority>\n  </url>',
        re.S,
    )
    text = block_pattern.sub("", text)
    block = f"""
  <url>
    <loc>{loc}</loc>
    <lastmod>{plan.date_dash}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>"""
    day_slide_blocks = list(
        re.finditer(
            r'\n  <url>\n    <loc>https://visionhub\.jp/presentations/day_slides/day_slide_\d{4}_\d{2}_\d{2}\.html</loc>.*?\n  </url>',
            text,
            flags=re.S,
        )
    )
    if day_slide_blocks:
        pos = day_slide_blocks[-1].end()
        text = text[:pos] + block + text[pos:]
    elif "</urlset>" in text:
        text = text.replace("\n</urlset>", block + "\n</urlset>", 1)
    else:
        raise SystemExit("Could not find sitemap insertion point")
    plan.sitemap_path.write_text(text, encoding="utf-8")


def write_outputs(plan: PublishPlan) -> None:
    slide_titles = read_slide_titles(plan.workspace, plan.image_sources, plan.title)
    convert_images(plan)
    copy_pptx(plan)
    plan.page_path.parent.mkdir(parents=True, exist_ok=True)
    plan.page_path.write_text(render_html(plan, slide_titles), encoding="utf-8")
    update_index(plan)
    update_list(plan)
    update_sitemap(plan)


def validate(plan: PublishPlan) -> list[str]:
    errors: list[str] = []
    if not plan.page_path.exists():
        errors.append(f"missing HTML: {plan.page_path}")
        return errors
    text = plan.page_path.read_text(encoding="utf-8")
    parser = RefParser()
    parser.feed(text)
    for kind, ref in parser.refs:
        if ref.startswith(("http://", "https://", "#", "mailto:", "tel:")):
            continue
        target = (plan.page_path.parent / ref).resolve()
        if not target.exists():
            errors.append(f"missing {kind} reference: {ref}")
    if parser.figure_count != len(plan.image_paths):
        errors.append(f"figure count {parser.figure_count} != image count {len(plan.image_paths)}")
    if parser.image_count != len(plan.image_paths):
        errors.append(f"img count {parser.image_count} != image count {len(plan.image_paths)}")
    for image_path in plan.image_paths:
        if not image_path.exists():
            errors.append(f"missing image: {image_path}")
            continue
        with Image.open(image_path) as im:
            if im.format != "JPEG":
                errors.append(f"{image_path} is {im.format}, not JPEG")
    if not plan.pptx_path.exists():
        errors.append(f"missing PPTX: {plan.pptx_path}")
    else:
        with zipfile.ZipFile(plan.pptx_path) as zf:
            slide_count = len(
                [n for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
            )
        if slide_count != len(plan.image_paths):
            errors.append(f"PPTX slide count {slide_count} != image count {len(plan.image_paths)}")
    index_text = plan.index_path.read_text(encoding="utf-8")
    if plan.rel_page_href not in index_text:
        errors.append("day_slides_index.html does not contain the new slide")
    list_text = plan.list_path.read_text(encoding="utf-8")
    if plan.abs_page_url not in list_text:
        errors.append("day_slides_list.html does not contain the new slide")
    sitemap_text = plan.sitemap_path.read_text(encoding="utf-8")
    if plan.abs_page_url not in sitemap_text:
        errors.append("sitemap.xml does not contain the new slide")
    if any(marker in text for marker in ("???", "譁", "\ufffd")):
        errors.append("HTML contains mojibake markers")
    if "max-width: 1696px" not in text:
        errors.append("HTML does not use the wide 1696px viewer")
    return errors


def run_git(repo: Path, args: Iterable[str]) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True)


def git_files(plan: PublishPlan) -> list[Path]:
    return [
        plan.page_path,
        plan.pptx_path,
        *plan.image_paths,
        plan.index_path,
        plan.list_path,
        plan.sitemap_path,
    ]


def maybe_git(args: argparse.Namespace, plan: PublishPlan) -> None:
    if not (args.stage or args.commit or args.push):
        return
    repo = args.repo_root.resolve()
    rel_files = [str(p.resolve().relative_to(repo)) for p in git_files(plan)]
    run_git(repo, ["add", "-f", *rel_files])
    if args.commit or args.push:
        run_git(repo, ["diff", "--cached", "--check"])
        message = args.message or f"feat: publish {plan.date_dash} daily slide"
        run_git(repo, ["commit", "-m", message])
    if args.push:
        run_git(repo, ["push", "origin", "HEAD:main"])


def main() -> int:
    args = parse_args()
    args.repo_root = args.repo_root.resolve()
    plan = make_plan(args)
    print(f"[publish] date={plan.date_dash} title={plan.title}")
    print(f"[publish] workspace={plan.workspace}")
    print(f"[publish] images={len(plan.image_sources)} pptx={plan.pptx_source}")
    if args.dry_run:
        for path in git_files(plan):
            print(f"[dry-run] would write {path}")
        return 0
    write_outputs(plan)
    errors = validate(plan)
    if errors:
        print("[publish] validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("[publish] validation passed")
    maybe_git(args, plan)
    print("[publish] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
