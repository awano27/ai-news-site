#!/usr/bin/env python3
"""Finish a day slide: SEO / JSON-LD / analytics / nav / home / feed / sitemap.

    py -3 scripts/finalize_day_slide.py 0913
    py -3 scripts/finalize_day_slide.py 0913 --year 2026 --dry-run
    py -3 scripts/finalize_day_slide.py 0913 --indexnow
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _mmdd_year(mmdd: str, year: int) -> tuple[str, Path]:
    if not (len(mmdd) == 4 and mmdd.isdigit()):
        raise SystemExit("MMDD must be four digits, for example 0913")
    month, day = int(mmdd[:2]), int(mmdd[2:])
    stamp = f"{year}_{month:02d}_{day:02d}"
    slide = ROOT / "presentations" / "day_slides" / f"day_slide_{stamp}.html"
    return stamp, slide


def _log(step: int, total: int, name: str, result: str) -> None:
    print(f"[{step}/{total}] {name}: {result}")


def run_injectors(slide: Path, dry_run: bool) -> None:
    from inject_analytics import AnalyticsInjector
    from inject_newsarticle_jsonld import JsonLdInjector
    from inject_seo_meta import SeoMetaInjector

    _log(1, 8, "inject_seo_meta", SeoMetaInjector().process_file(slide, False, dry_run))
    _log(2, 8, "inject_newsarticle_jsonld", JsonLdInjector().process_file(slide, False, dry_run))
    _log(3, 8, "inject_analytics", AnalyticsInjector().process_file(slide, False, dry_run))


def run_nav_home_feed_sitemap(dry_run: bool) -> int:
    import build_feed
    import build_sitemap
    import inject_slide_nav
    import update_home_fallback

    nav_argv = ["--dry-run"] if dry_run else []
    rc_nav = inject_slide_nav.main(nav_argv)
    _log(4, 8, "inject_slide_nav", "dry-run" if dry_run else f"exit {rc_nav}")

    home_argv = ["--dry-run"] if dry_run else []
    rc_home = update_home_fallback.main(home_argv)
    _log(5, 8, "update_home_fallback", "dry-run" if dry_run else f"exit {rc_home}")

    feed_argv = ["--dry-run"] if dry_run else []
    rc_feed = build_feed.main(feed_argv)
    _log(6, 8, "build_feed", f"exit {rc_feed}")

    sm_argv = ["--dry-run"] if dry_run else []
    rc_sm = build_sitemap.main(sm_argv)
    _log(7, 8, "build_sitemap", f"exit {rc_sm}")
    return rc_nav or rc_home or rc_feed or rc_sm


def run_checks(slide: Path) -> int:
    import check_analytics_coverage
    import check_slide_seo

    rc_seo = check_slide_seo.main([str(slide)])
    rc_cov = check_analytics_coverage.main()
    cov_rc = 1 if rc_cov else 0
    _log(8, 8, "check_slide_seo+check_analytics_coverage", f"seo={rc_seo} coverage={cov_rc}")
    return rc_seo or cov_rc


def run_indexnow(slide: Path, dry_run: bool) -> int:
    import indexnow_ping

    url = f"https://visionhub.jp/presentations/day_slides/{slide.name}"
    argv = ["--urls", url]
    if dry_run:
        argv.append("--dry-run")
    else:
        argv.append("--send")
    rc = indexnow_ping.main(argv)
    print(f"[indexnow] exit {rc}")
    return rc


def finalize(
    mmdd: str,
    year: int,
    dry_run: bool = False,
    indexnow: bool = False,
    checks: bool = True,
) -> int:
    stamp, slide = _mmdd_year(mmdd, year)
    if not slide.is_file():
        print(f"[finalize_day_slide] missing {slide.relative_to(ROOT).as_posix()}", file=sys.stderr)
        return 1
    print(f"[finalize_day_slide] {stamp} dry_run={dry_run}")
    run_injectors(slide, dry_run)
    rc = run_nav_home_feed_sitemap(dry_run)
    if checks:
        rc = rc or run_checks(slide)
    else:
        print("[8/8] checks: skipped")
    if indexnow:
        rc = rc or run_indexnow(slide, dry_run)
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mmdd", help="Target date as MMDD, for example 0913")
    ap.add_argument("--year", type=int, default=date.today().year)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--indexnow", action="store_true", help="POST IndexNow (off by default)")
    args = ap.parse_args(argv)
    return finalize(args.mmdd, args.year, dry_run=args.dry_run, indexnow=args.indexnow, checks=True)


if __name__ == "__main__":
    raise SystemExit(main())
