import json
import os
import re
import shutil
from pathlib import Path

import pytest

from scripts import integrate_day_slides as subject

REPO = Path(__file__).resolve().parents[1]
SLIDES = Path("presentations/day_slides")
META = "presentations/day_slides/meta_index.json"
LIST = "presentations/day_slides/list.json"
INDEX = "presentations/day_slides_index.html"
LLMS = "llms.txt"
HUB = (META, LIST, INDEX, LLMS)
PAST_NS = 1_600_000_000_000_000_000
ISSUE_KEYS = ["date", "no", "file", "url", "title", "description", "section", "cat", "cat_label", "cover"]

PAGES = {
    "2026-09-28": ("九月二十八日号 | 2026-09-28", 30, "AI Agent Operations"),
    "2026-09-29": ("九月二十九日号 | 2026-09-29", 31, "Frontier Model Release"),
    "2026-09-30": ("主権AIを自社で回す | 2026-09-30", 32, "Sovereign AI"),
    "2026-10-01": ("十月一日号 | 2026-10-01", 33, "Agent Workforce"),
    "2026-10-02": ("R&amp;Dを<b>画面</b>から回す | 2026-10-02", 34, "Desktop Automation"),
}
LISTED = ("2026-10-01", "2026-09-29", "2026-09-28")
CURATED_CATS = {
    "AI Agent Operations": ("agent", "エージェント"),
    "Frontier Model Release": ("model", "モデル"),
    "Sovereign AI": ("gov", "ガバナンス"),
    "Agent Workforce": ("agent", "エージェント"),
    "Desktop Automation": ("prod", "プロダクト"),
}


def slide_page(title: str | None, no: int | None, section: str) -> str:
    head = "" if title is None else f"<title>{title}</title>"
    number = "" if no is None else f'<p class="issue">No.{no}</p>'
    return (
        f'<!doctype html><html lang="ja"><head><meta charset="utf-8">{head}'
        f'<meta name="description" content="{section}の説明">'
        f'<script type="application/ld+json">{{"@type": "NewsArticle", "articleSection": "{section}"}}</script>'
        f"</head><body><main>{number}</main></body></html>\n"
    )


def listed_issue(date: str, pages=PAGES) -> dict:
    title, no, section = pages[date]
    cat, cat_label = CURATED_CATS[section]
    stamp = date.replace("-", "_")
    issue = {
        "date": date,
        "file": f"day_slide_{stamp}.html",
        "url": f"https://visionhub.jp/presentations/day_slides/day_slide_{stamp}.html",
        "title": title.split(" | ")[0],
        "description": f"{section}の説明",
        "section": section,
        "cat": cat,
        "cat_label": cat_label,
        "cover": None,
        "no": no,
    }
    if date == "2026-09-29":
        issue["primary_url"] = "https://example.com/release"
    return issue


NEW_1002 = {
    "date": "2026-10-02",
    "no": 34,
    "file": "day_slide_2026_10_02.html",
    "url": "https://visionhub.jp/presentations/day_slides/day_slide_2026_10_02.html",
    "title": "R&Dを画面から回す",
    "description": "Desktop Automationの説明",
    "section": "Desktop Automation",
    "cat": "prod",
    "cat_label": "プロダクト",
    "cover": "day_slides/images/1002/cover.jpg",
}
NEW_0930 = {
    "date": "2026-09-30",
    "no": 32,
    "file": "day_slide_2026_09_30.html",
    "url": "https://visionhub.jp/presentations/day_slides/day_slide_2026_09_30.html",
    "title": "主権AIを自社で回す",
    "description": "Sovereign AIの説明",
    "section": "Sovereign AI",
    "cat": "gov",
    "cat_label": "ガバナンス",
    "cover": None,
}

LIST_BEFORE = [
    {"date": "2026-10-01", "url": "day_slides/day_slide_2026_10_01.html", "label": "10/1 - 十月一日号"},
    {"date": "2026-09-29", "url": "day_slides/day_slide_2026_09_29.html", "label": "9/29 - 九月二十九日号"},
    {"date": "2026-09-28", "url": "day_slides/day_slide_2026_09_28.html", "label": "9/28 - 九月二十八日号"},
]


def card(date: str, title: str) -> str:
    return (
        f'<a class="slide-card" href="day_slides/day_slide_{date.replace("-", "_")}.html">'
        f'<span class="slide-date">{date[5:].replace("-", "/")}</span><span class="slide-title">{title}</span></a>'
    )


def feat(date: str, tag: str, title: str) -> str:
    return (
        f'          <a class="feat-card" href="day_slides/day_slide_{date.replace("-", "_")}.html">\n'
        f'            <div class="feat-tag"><span class="dot"></span>{tag}</div>\n'
        f'            <div class="feat-date">{date.replace("-", "/")}</div>\n'
        f'            <h3 class="feat-title">{title}</h3>\n'
        '            <span class="feat-cta">スライドを見る <span class="arr" aria-hidden="true">&rarr;</span></span>\n'
        "          </a>\n"
    )


INDEX_PAGE = """\
<!doctype html>
<html lang="ja">
<body>
  <header class="site-header">
      <div class="header-actions">
        <a class="cta" href="day_slides/{cta}">最新スライド <span aria-hidden="true">→</span></a>
      </div>
  </header>
  <main id="main">
    <section class="hero">
      <div class="container">
        <div class="stat-row">
          <div class="stat-card">
            <div class="stat-num">{total}</div>
            <span class="stat-label">Total Slides</span>
          </div>
          <div class="stat-card">
            <div class="stat-num">2</div>
            <span class="stat-label">Months Covered</span>
          </div>
          <div class="stat-card">
            <div class="stat-num">{latest}</div>
            <span class="stat-label">Latest Update</span>
          </div>
        </div>
      </div>
    </section>

    <section class="section section-darker">
      <div class="container">
        <div class="section-head">
          <div>
            <div class="section-eyebrow">FEATURED</div>
            <h2 class="section-title">最新の3本</h2>
          </div>
          <p class="section-sub">{sub}の最新3本を読む。</p>
        </div>
        <div class="featured-grid">
{featured}        </div>
      </div>
    </section>

    <section class="section section-dark" id="archive">
      <div class="container">
        <div class="filter-bar">
          <div class="filter-status"><strong id="filterCount">{total}</strong> / <span id="filterTotal">{total}</span> 件</div>
        </div>

        <div id="archiveList">
          <details class="month-group" open data-month="2026-10">
            <summary class="month-header"><div class="month-label"><svg class="month-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5 3l6 5-6 5V3z"/></svg><span class="month-title">2026年 10月</span></div><span class="month-count">{oct_count} 件</span></summary>
            <div class="slides-grid">{oct_cards}</div>
          </details>
          <details class="month-group" open data-month="2026-09">
            <summary class="month-header">
              <div class="month-label">
                <svg class="month-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5 3l6 5-6 5V3z"/></svg>
                <span class="month-title">2026年 9月</span>
              </div>
              <span class="month-count">{sep_count} 件</span>
            </summary>
            <div class="slides-grid">
              {sep_cards}
            </div>
          </details>
        </div>
      </div>
    </section>
  </main>
</body>
</html>
"""
SEP = "\n              "
OLD_SUB = "十月一日、九月二十九日、九月二十八日"
FEATURED_BEFORE = (
    feat("2026-10-01", "LATEST", "十月一日号")
    + '          <a class="feat-card" href="day_slides/day_slide_2026_09_29.html">\n'
    '            <div class="feat-date">2026/09/29</div>\n'
    '            <h3 class="feat-title">九月二十九日号</h3>\n'
    '            <span class="feat-cta">スライドを見る <span class="arr" aria-hidden="true">&rarr;</span></span>\n'
    "          </a>\n"
    '          <a class="feat-card" href="day_slides/day_slide_2026_09_28.html"><div class="feat-tag">'
    '<span class="dot"></span>RECENT</div><div class="feat-date">2026/09/28</div><h3 class="feat-title">'
    '九月二十八日号</h3><span class="feat-cta">スライドを見る <span class="arr">→</span></span></a>\n'
)
INDEX_BEFORE = {
    "cta": "day_slide_2026_10_01.html",
    "total": 99,
    "latest": "2026/10/01",
    "sub": OLD_SUB,
    "featured": FEATURED_BEFORE,
    "oct_count": 1,
    "oct_cards": card("2026-10-01", "十月一日号"),
    "sep_count": 2,
    "sep_cards": card("2026-09-29", "九月二十九日号") + SEP + card("2026-09-28", "九月二十八日号"),
}
INDEX_AFTER = {
    **INDEX_BEFORE,
    "cta": "day_slide_2026_10_02.html",
    "total": 5,
    "latest": "2026/10/02",
    "featured": (
        feat("2026-10-02", "LATEST", "R&amp;Dを画面から回す")
        + feat("2026-10-01", "RECENT", "十月一日号")
        + feat("2026-09-30", "RECENT", "主権AIを自社で回す")
    ),
    "oct_count": 2,
    "oct_cards": card("2026-10-02", "R&amp;Dを画面から回す") + card("2026-10-01", "十月一日号"),
    "sep_count": 3,
    "sep_cards": card("2026-09-30", "主権AIを自社で回す") + SEP + INDEX_BEFORE["sep_cards"],
}


def llms_line(label: str, date: str, text: str) -> str:
    return f"- [{label}](https://visionhub.jp/presentations/day_slides/day_slide_{date.replace('-', '_')}.html): {text}\n"


def today(date: str, text: str) -> str:
    return llms_line("Today's day slide", date, text)


def recent(date: str, text: str) -> str:
    return llms_line(f"Recent day slide {date}", date, text)


LLMS_HEAD = "# AI Intelligence Hub\n\n## Docs\n\n- [Home](https://visionhub.jp/): トップページ\n"
LLMS_TAIL = "- [Day slides index](https://visionhub.jp/presentations/day_slides_index.html): 日次スライド一覧\n"
LLMS_BEFORE = (
    LLMS_HEAD + today("2026-09-29", "九月二十九日の旧テキスト") + recent("2026-09-28", "九月二十八日号") + LLMS_TAIL
)
LLMS_AFTER = (
    LLMS_HEAD
    + today("2026-10-02", "R&Dを画面から回す")
    + recent("2026-10-01", "十月一日号")
    + recent("2026-09-30", "主権AIを自社で回す")
    + recent("2026-09-29", "九月二十九日の旧テキスト")
    + recent("2026-09-28", "九月二十八日号")
    + LLMS_TAIL
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def make_repo(root: Path, listed=LISTED, pages=PAGES, llms=LLMS_BEFORE, index=INDEX_BEFORE) -> Path:
    (root / "script").mkdir(parents=True)
    shutil.copyfile(REPO / "script" / "build_day_slides_index.py", root / "script" / "build_day_slides_index.py")
    for date, (title, no, section) in pages.items():
        write(root / SLIDES / f"day_slide_{date.replace('-', '_')}.html", slide_page(title, no, section))
    write(root / SLIDES / "day_slide_2026_10_xx.html", slide_page("下書き | 2026-10-xx", 99, "Draft"))
    write(root / SLIDES / "images" / "1002" / "cover.jpg", "")
    meta = {
        "generated_from": 33,
        "since": "2026-09-28",
        "latest": "2026-10-01",
        "categories": {"model": 1, "agent": 5, "infra": 1},
        "issues": [listed_issue(date, pages) for date in listed],
    }
    write(root / META, json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    write(root / LIST, json.dumps(LIST_BEFORE, ensure_ascii=False, indent=2) + "\n")
    write(root / INDEX, INDEX_PAGE.format(**index))
    write(root / LLMS, llms)
    return root


def tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def changed(after: dict[str, bytes], before: dict[str, bytes]) -> list[str]:
    return sorted(rel for rel in after.keys() | before.keys() if after.get(rel) != before.get(rel))


def age_hub_files(root: Path) -> None:
    for rel in HUB:
        os.utime(root / rel, ns=(PAST_NS, PAST_NS))


def rewritten(root: Path) -> list[str]:
    return [rel for rel in HUB if (root / rel).stat().st_mtime_ns != PAST_NS]


def slide_cards(root: Path) -> list[str]:
    return re.findall(r'<a class="slide-card" href="day_slides/([^"]+)"', (root / INDEX).read_text(encoding="utf-8"))


def month_cards(root: Path, month: str) -> list[str]:
    page = (root / INDEX).read_text(encoding="utf-8")
    group = re.search(rf'data-month="{month}">.*?</details>', page, re.S).group(0)
    return re.findall(r'<a class="slide-card" href="day_slides/day_slide_(\d{4}_\d{2}_\d{2})\.html"', group)


@pytest.fixture
def integrated(tmp_path: Path, capsys) -> tuple[Path, list[str]]:
    root = make_repo(tmp_path)
    assert subject.main(["--root", str(root)]) == 0
    return root, capsys.readouterr().out.splitlines()


def test_meta_gains_new_issues_in_date_order_with_recounted_categories(integrated) -> None:
    root, _ = integrated
    text = (root / META).read_text(encoding="utf-8")
    meta = json.loads(text)

    assert text == json.dumps(meta, ensure_ascii=False, indent=2) + "\n"
    old = [listed_issue(date) for date in ("2026-10-01", "2026-09-29", "2026-09-28")]
    assert meta["issues"] == [NEW_1002, old[0], NEW_0930, old[1], old[2]]
    assert [list(issue) for issue in meta["issues"]] == [ISSUE_KEYS, list(old[0]), ISSUE_KEYS, list(old[1]), list(old[2])]
    assert {key: meta[key] for key in ("generated_from", "since", "latest")} == {
        "generated_from": 34,
        "since": "2026-09-28",
        "latest": "2026-10-02",
    }
    assert list(meta["categories"].items()) == [("model", 1), ("agent", 2), ("prod", 1), ("gov", 1)]


def test_list_gains_month_day_labels_newest_first(integrated) -> None:
    root, _ = integrated

    assert json.loads((root / LIST).read_text(encoding="utf-8")) == [
        {"date": "2026-10-02", "url": "day_slides/day_slide_2026_10_02.html", "label": "10/2 - R&Dを画面から回す"},
        LIST_BEFORE[0],
        {"date": "2026-09-30", "url": "day_slides/day_slide_2026_09_30.html", "label": "9/30 - 主権AIを自社で回す"},
        LIST_BEFORE[1],
        LIST_BEFORE[2],
    ]


def test_index_gains_cards_in_both_month_formats_and_a_rebuilt_featured_trio(integrated) -> None:
    root, _ = integrated

    assert (root / INDEX).read_text(encoding="utf-8") == INDEX_PAGE.format(**INDEX_AFTER)


PAIR_PAGES = {
    "2026-09-27": ("九月二十七日号 | 2026-09-27", 29, "AI Agent Operations"),
    **PAGES,
    "2026-10-03": ("十月三日号 | 2026-10-03", 35, "Agent Workforce"),
    "2026-10-04": ("十月四日号 | 2026-10-04", 36, "Desktop Automation"),
}
PAIR_LISTED = ("2026-10-02", "2026-10-01", "2026-09-28", "2026-09-27")
PAIR_INDEX = {
    **INDEX_BEFORE,
    "oct_count": 2,
    "oct_cards": card("2026-10-02", "十月二日号") + card("2026-10-01", "十月一日号"),
    "sep_count": 2,
    "sep_cards": card("2026-09-28", "九月二十八日号") + SEP + card("2026-09-27", "九月二十七日号"),
}


@pytest.mark.parametrize("newest_first", [False, True], ids=["discovered-oldest-first", "discovered-newest-first"])
@pytest.mark.parametrize(
    ("month", "expected"),
    [
        pytest.param("2026-10", ["2026_10_04", "2026_10_03", "2026_10_02", "2026_10_01"], id="one-line"),
        pytest.param("2026-09", ["2026_09_30", "2026_09_29", "2026_09_28", "2026_09_27"], id="multi-line"),
    ],
)
def test_new_cards_read_newest_first_above_the_existing_ones(
    tmp_path: Path, monkeypatch, month: str, expected: list[str], newest_first: bool
) -> None:
    discover = subject.discover
    monkeypatch.setattr(
        subject,
        "discover",
        lambda root, meta: sorted(discover(root, meta), key=lambda slide: slide.date, reverse=newest_first),
    )
    root = make_repo(tmp_path, listed=PAIR_LISTED, pages=PAIR_PAGES, index=PAIR_INDEX)

    assert subject.main(["--root", str(root)]) == 0

    assert month_cards(root, month) == expected


def test_llms_names_the_newest_slide_and_demotes_the_previous_today_line(integrated) -> None:
    root, _ = integrated

    assert (root / LLMS).read_text(encoding="utf-8") == LLMS_AFTER


def test_hub_files_are_written_with_lf_newlines(integrated) -> None:
    root, _ = integrated

    assert [rel for rel in HUB if b"\r" in (root / rel).read_bytes()] == []


def test_summary_lists_each_slide_and_writes_meta_index_last(integrated) -> None:
    _, lines = integrated

    assert "  2026-09-30 No.32 gov 主権AIを自社で回す" in lines
    assert "  2026-10-02 No.34 prod R&Dを画面から回す" in lines
    assert "llms.txt updated" in lines
    assert [line for line in lines if line.startswith("wrote ")] == [f"wrote {rel}" for rel in (LIST, INDEX, LLMS, META)]


def test_second_run_changes_nothing(tmp_path: Path, capsys) -> None:
    root = make_repo(tmp_path)
    assert subject.main(["--root", str(root)]) == 0
    before = tree(root)
    age_hub_files(root)
    capsys.readouterr()

    assert subject.main(["--root", str(root)]) == 0

    assert changed(tree(root), before) == []
    assert rewritten(root) == []
    assert capsys.readouterr().out.splitlines() == [
        "nothing to integrate: meta_index.json lists every day slide",
        "llms.txt already current",
    ]


def test_complete_meta_leaves_hub_files_alone_but_refreshes_a_stale_llms(tmp_path: Path, capsys) -> None:
    root = make_repo(tmp_path, listed=tuple(sorted(PAGES, reverse=True)))
    before = tree(root)
    age_hub_files(root)

    assert subject.main(["--root", str(root)]) == 0

    assert changed(tree(root), before) == [LLMS]
    assert rewritten(root) == [LLMS]
    assert (root / LLMS).read_text(encoding="utf-8") == LLMS_AFTER
    assert capsys.readouterr().out.splitlines() == [
        "nothing to integrate: meta_index.json lists every day slide",
        "llms.txt updated",
        f"wrote {LLMS}",
    ]


def test_llms_keeps_a_recent_line_that_is_already_listed(tmp_path: Path) -> None:
    hand_written = recent("2026-10-01", "手で足した十月一日")
    root = make_repo(tmp_path, llms=LLMS_BEFORE.replace(LLMS_TAIL, hand_written + LLMS_TAIL))

    assert subject.main(["--root", str(root)]) == 0

    lines = (root / LLMS).read_text(encoding="utf-8").splitlines()
    assert [line for line in lines if "day_slide_2026_10_01" in line] == [hand_written.rstrip("\n")]


def test_dry_run_reports_and_writes_nothing(tmp_path: Path, capsys) -> None:
    root = make_repo(tmp_path)
    before = tree(root)
    age_hub_files(root)

    assert subject.main(["--root", str(root), "--dry"]) == 0

    assert changed(tree(root), before) == []
    assert rewritten(root) == []
    lines = capsys.readouterr().out.splitlines()
    assert "llms.txt needs an update" in lines
    assert [line for line in lines if line.startswith(("wrote ", "would write "))] == [
        f"would write {rel}" for rel in (LIST, INDEX, LLMS, META)
    ]


@pytest.mark.parametrize(
    ("topics", "sub"),
    [
        pytest.param(
            "2026_10_02=R&D Desk,2026_10_01=Agents,2026_09_30=Sovereign", "R&amp;D Desk、Agents、Sovereign", id="all-three"
        ),
        pytest.param("2026_10_02=R&D Desk,2026_10_01=Agents", OLD_SUB, id="one-missing"),
        pytest.param("", OLD_SUB, id="none"),
    ],
)
def test_topics_rewrite_the_featured_sub_line_only_when_all_three_are_named(tmp_path: Path, topics, sub) -> None:
    root = make_repo(tmp_path)

    assert subject.main(["--root", str(root), "--topics", topics]) == 0

    assert (root / INDEX).read_text(encoding="utf-8") == INDEX_PAGE.format(**{**INDEX_AFTER, "sub": sub})


@pytest.mark.parametrize(
    ("pages", "message"),
    [
        pytest.param(
            {"2026-10-02": ("題名 | 2026-10-02", None, "Desktop Automation")},
            "day_slide_2026_10_02.html: no 'No.NNN' on the page; cannot assign an issue number",
            id="page-without-number",
        ),
        pytest.param(
            {"2026-10-02": ("題名 | 2026-10-02", 33, "Desktop Automation")},
            "issue number collision: [33]",
            id="number-of-a-listed-issue",
        ),
        pytest.param(
            {"2026-09-30": ("題名 | 2026-09-30", 34, "Sovereign AI")},
            "issue number collision: [34]",
            id="two-new-slides-share-a-number",
        ),
        pytest.param(
            {"2026-10-02": (None, 34, "Desktop Automation")},
            "day_slide_2026_10_02.html: no <title> on the page",
            id="page-without-title",
        ),
        pytest.param(
            {"2026-11-01": ("十一月一日号 | 2026-11-01", 35, "AI Agent Operations")},
            "month group 2026-11 not found in day_slides_index.html",
            id="month-group-missing",
        ),
    ],
)
def test_data_error_exits_2_and_leaves_every_file_untouched(tmp_path: Path, capsys, pages, message) -> None:
    root = make_repo(tmp_path, pages={**PAGES, **pages})
    before = tree(root)

    assert subject.main(["--root", str(root)]) == 2

    assert f"error: {message}" in capsys.readouterr().err.splitlines()
    assert changed(tree(root), before) == []


@pytest.mark.parametrize("completed_writes", [0, 1, 2, 3])
def test_rerun_after_an_interrupted_write_converges(tmp_path: Path, monkeypatch, completed_writes) -> None:
    clean = make_repo(tmp_path / "clean")
    assert subject.main(["--root", str(clean)]) == 0
    root = make_repo(tmp_path / "interrupted")
    write_text = Path.write_text
    written = []

    def crash_after_completed_writes(path, *args, **kwargs):
        if len(written) == completed_writes:
            raise OSError("simulated crash")
        written.append(path)
        return write_text(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_text", crash_after_completed_writes)
        with pytest.raises(OSError, match="simulated crash"):
            subject.main(["--root", str(root)])

    assert subject.main(["--root", str(root)]) == 0
    assert slide_cards(root) == slide_cards(clean)
    assert changed(tree(root), tree(clean)) == []


@pytest.mark.parametrize(
    ("page", "expected"),
    [
        pytest.param("<title>APIがない社内ツールも | 2026-10-05</title>", "APIがない社内ツールも", id="cut-at-pipe"),
        pytest.param("<title>主題 | 副題 | 2026-10-05</title>", "主題", id="first-pipe-wins"),
        pytest.param("<title>Kolibri-1 2026-10-04</title>", "Kolibri-1", id="trailing-date"),
        pytest.param("<title>題名 |2026-10-04 </title>", "題名", id="trailing-pipe-date"),
        pytest.param('<title lang="ja">R&amp;D <b>を</b>\n  回す</title>', "R&D を 回す", id="entities-tags-whitespace"),
        pytest.param("<main>no title</main>", None, id="no-title"),
    ],
)
def test_short_title(page: str, expected: str | None) -> None:
    assert subject.short_title(page) == expected
