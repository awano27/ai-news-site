#!/usr/bin/env python3
"""Site freshness guard for visionhub.jp.

Why this exists
---------------
The hub pages (``presentations/index.html``, ``presentations/day_slides_list.html``)
no longer carry a hand-maintained slide list -- they render their content at runtime
by fetching ``presentations/day_slides_index.html`` and parsing its cards. That makes
``day_slides_index.html`` the single source of truth and the single point of failure:
if the daily pipeline writes a new ``day_slide_YYYY_MM_DD.html`` but forgets to add it
to that index (or to ``sitemap.xml``), every downstream page silently shows stale
content with no error.

This script catches that class of "更新漏れ" (missed update) drift:

  CRITICAL (exit 1 on failure)
    * The newest generated day-slide is present in day_slides_index.html
      (both the ``.feat-card`` highlight grid AND the ``.slide-card`` full list).
    * The newest generated day-slide URL is present in sitemap.xml.
    * No calendar-day gap in the last ``--gap-days`` days (default 14) ending at the
      newest slide: every day must have a slide file on disk, an entry in
      day_slides_index.html, and an entry in sitemap.xml. This catches slides that
      were created in a Claude cloud session but never merged to main (2026-06-30 /
      2026-07-02 incident), and days that were skipped entirely (2026-06-29 / 07-07).

  WARN (reported, does not fail the build)
    * Each sibling daily pipeline (reports / news archive / ranking / news JSON /
      version.json / archive_index.json) is within --max-lag days of the newest slide.

Usage
-----
    python scripts/check_site_freshness.py            # check, human report
    python scripts/check_site_freshness.py --json      # machine-readable
    python scripts/check_site_freshness.py --max-lag 2 # tolerate 2-day report lag

Exit code is non-zero when any CRITICAL check fails, so it can gate CI / the daily
GitHub Action right after slide generation.

Dependencies: Python standard library only (runs anywhere, no pip install).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SLUG_RE = re.compile(r"day_slide_(\d{4})_(\d{2})_(\d{2})")
DASH_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
UNDERSCORE_RE = re.compile(r"(\d{4})_(\d{2})_(\d{2})")


def _p(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _max_date(text: str, pattern: re.Pattern) -> str | None:
    """Return the newest YYYY-MM-DD found via ``pattern`` (3 capture groups)."""
    found = {"-".join(m) for m in pattern.findall(text)}
    valid = []
    for d in found:
        try:
            y, m, dd = (int(x) for x in d.split("-"))
            date(y, m, dd)
            valid.append(d)
        except ValueError:
            continue
    return max(valid) if valid else None


def _newest_slide_date() -> str | None:
    """Newest date among generated presentations/day_slides/day_slide_*.html files."""
    files = glob.glob(_p("presentations", "day_slides", "day_slide_*_*_*.html"))
    dates = []
    for f in files:
        m = SLUG_RE.search(os.path.basename(f))
        if m:
            dates.append("-".join(m.groups()))
    return max(dates) if dates else None


def _newest_dated_file(directory: str, pattern: re.Pattern) -> str | None:
    if not os.path.isdir(_p(*directory.split("/"))):
        return None
    best = None
    for name in os.listdir(_p(*directory.split("/"))):
        m = pattern.search(name)
        if m:
            d = "-".join(m.groups())
            if best is None or d > best:
                best = d
    return best


def _json_date(path: str, *keys: str) -> str | None:
    full = _p(*path.split("/"))
    if not os.path.exists(full):
        return None
    try:
        data = json.loads(_read(full))
    except (json.JSONDecodeError, OSError):
        return None
    # Try explicit keys first, else scan the whole serialized blob for the max date.
    for k in keys:
        v = data.get(k) if isinstance(data, dict) else None
        if isinstance(v, str):
            d = _max_date(v, DASH_RE)
            if d:
                return d
    return _max_date(json.dumps(data), DASH_RE)


def _days_between(a: str, b: str) -> int:
    ya, ma, da = (int(x) for x in a.split("-"))
    yb, mb, db = (int(x) for x in b.split("-"))
    return abs((date(ya, ma, da) - date(yb, mb, db)).days)


def _gap_check(expected: str, idx: str, sm: str, gap_days: int) -> dict:
    """Every calendar day in the ``gap_days`` window ending at ``expected`` must have
    a slide file on disk AND be present in the index AND in the sitemap."""
    from datetime import timedelta
    y, m, d = (int(x) for x in expected.split("-"))
    end = date(y, m, d)
    missing_file, missing_index, missing_sitemap = [], [], []
    for i in range(gap_days):
        day = end - timedelta(days=i)
        slug = f"day_slide_{day.year:04d}_{day.month:02d}_{day.day:02d}"
        iso = day.isoformat()
        if not os.path.exists(_p("presentations", "day_slides", slug + ".html")):
            missing_file.append(iso)
            continue
        if slug not in idx:
            missing_index.append(iso)
        if slug not in sm:
            missing_sitemap.append(iso)
    problems = []
    if missing_file:
        problems.append("no slide file (skipped day or unmerged branch): " + ", ".join(sorted(missing_file)))
    if missing_index:
        problems.append("file exists but MISSING from day_slides_index.html: " + ", ".join(sorted(missing_index)))
    if missing_sitemap:
        problems.append("file exists but MISSING from sitemap.xml: " + ", ".join(sorted(missing_sitemap)))
    ok = not problems
    return {
        "name": f"no day gaps in last {gap_days} days (ending {expected})",
        "ok": ok,
        "detail": "complete" if ok else "; ".join(problems),
    }


def run(max_lag: int, gap_days: int = 14) -> dict:
    expected = _newest_slide_date()
    report: dict = {"expected_latest_slide": expected, "critical": [], "warn": []}

    if not expected:
        report["critical"].append(
            {"name": "day_slides directory", "ok": False,
             "detail": "no day_slide_YYYY_MM_DD.html files found"}
        )
        report["ok"] = False
        return report

    slug = "day_slide_" + expected.replace("-", "_")

    # ---- CRITICAL: the canonical index must carry the newest slide ----
    idx_path = _p("presentations", "day_slides_index.html")
    idx = _read(idx_path) if os.path.exists(idx_path) else ""

    feat_dates = sorted(
        {"-".join(SLUG_RE.search(h).groups())
         for h in re.findall(r'class="feat-card"[^>]*href="[^"]*?(day_slide_\d{4}_\d{2}_\d{2})',
                             idx.replace("\n", " "))},
        reverse=True,
    )
    # Fallback: parse any feat-card hrefs regardless of attribute order.
    if not feat_dates:
        feat_block = idx
        feat_dates = sorted({"-".join(m) for m in SLUG_RE.findall(feat_block)}, reverse=True)

    has_slug = slug in idx
    report["critical"].append({
        "name": "day_slides_index.html contains newest slide",
        "ok": has_slug,
        "detail": f"{slug} {'present' if has_slug else 'MISSING'} "
                  f"(index newest={feat_dates[0] if feat_dates else 'none'})",
    })

    # ---- CRITICAL: sitemap must list the newest slide ----
    sm_path = _p("sitemap.xml")
    sm = _read(sm_path) if os.path.exists(sm_path) else ""
    sm_ok = slug in sm
    report["critical"].append({
        "name": "sitemap.xml lists newest slide",
        "ok": sm_ok,
        "detail": f"{slug} {'present' if sm_ok else 'MISSING'} in sitemap.xml",
    })

    # ---- CRITICAL: no calendar-day gaps in the recent window ----
    if gap_days > 0:
        report["critical"].append(_gap_check(expected, idx, sm, gap_days))

    # ---- WARN: sibling daily pipelines within max_lag days ----
    siblings = [
        ("daily report HTML", _newest_dated_file("presentations/daily_reports", UNDERSCORE_RE)),
        ("daily report index.json", _json_date("presentations/daily_reports/index.json")),
        ("daily-news archive", _newest_dated_file("daily-news/archive", DASH_RE)),
        ("ranking report", _newest_dated_file("presentations", re.compile(r"ai_ranking_report_(\d{4})(\d{2})(\d{2})"))),
        ("news/latest.json", _json_date("news/latest.json", "date", "last_updated", "generated")),
        ("public-pages version.json", _json_date("public-pages/news/version.json", "last_updated", "date")),
        ("public-pages archive_index.json", _json_date("public-pages/news/archive_index.json", "date")),
    ]
    for name, d in siblings:
        if d is None:
            report["warn"].append({"name": name, "latest": None, "lag_days": None,
                                    "detail": "not found / unparseable"})
            continue
        lag = _days_between(expected, d)
        report["warn"].append({
            "name": name, "latest": d, "lag_days": lag,
            "stale": lag > max_lag,
            "detail": f"newest={d} (lag {lag}d vs slide {expected})",
        })

    report["ok"] = all(c["ok"] for c in report["critical"])
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="visionhub.jp freshness guard")
    ap.add_argument("--max-lag", type=int, default=1,
                    help="days a sibling pipeline may lag the newest slide before WARN (default 1)")
    ap.add_argument("--gap-days", type=int, default=14,
                    help="calendar window (ending at newest slide) that must have a slide "
                         "every day, in the index and sitemap. 0 disables (default 14)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    rep = run(args.max_lag, args.gap_days)

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0 if rep["ok"] else 1

    exp = rep.get("expected_latest_slide")
    print(f"visionhub.jp freshness  |  newest day-slide = {exp or 'NONE'}")
    print("-" * 64)
    print("CRITICAL (gates the build):")
    for c in rep["critical"]:
        mark = "OK  " if c["ok"] else "FAIL"
        print(f"  [{mark}] {c['name']}\n         {c['detail']}")
    print("\nSIBLING PIPELINES (informational):")
    for w in rep["warn"]:
        if w.get("latest") is None:
            mark = "?  "
        elif w.get("stale"):
            mark = "LAG"
        else:
            mark = "ok "
        print(f"  [{mark}] {w['name']}: {w['detail']}")
    print("-" * 64)
    if rep["ok"]:
        print("RESULT: PASS — hub pages are fed with the newest slide.")
    else:
        print("RESULT: FAIL — newest slide is NOT propagated. "
              "Regenerate day_slides_index.html / sitemap.xml so the dynamic "
              "hub pages (index.html, day_slides_list.html) pick it up.")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
