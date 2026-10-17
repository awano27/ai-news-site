#!/usr/bin/env python3
"""
Daily AI News Auto-Collector (Enhanced)
Collects from RSS, HN, JP news, GitHub Trending, HuggingFace, Funding/M&A.
Processes with an LLM (local Ollama by default; --provider nvidia for cloud)
for summarization + evidence extraction.
Outputs multi-section report to input/day/MMDD.txt.
"""

import argparse
import logging
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict

from .config import PROJECT_ROOT, INPUT_DAY_DIR, LOG_DIR
from .collectors import RSSAutoCollector, HNAutoCollector, JPCollector, XBookmarksCollector
from .collectors.github_trending import GitHubTrendingCollector
from .collectors.benchmark_collector import BenchmarkCollector
from .collectors.funding_collector import FundingCollector
from .collectors.arxiv_collector import ArxivCollector
from .collectors import model_watch
from .llm_provider import make_provider
from .processor import LLMProcessor
from .formatter import DayFileFormatter
from .html_report import generate_html_report
from .daily_news_page import generate_daily_news, log_publication_window_drops, within_publication_window
from . import dedup as dedup_mod
from .quality import filter_publishable, failure_reason


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().strftime("%Y%m%d")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / f"{today}.log", encoding="utf-8"),
            logging.StreamHandler(),
        ]
    )


def deduplicate(articles: List[Dict]) -> List[Dict]:
    """Delegate to the canonical-URL + fuzzy-title dedup module."""
    return dedup_mod.deduplicate(articles)


def parse_args():
    p = argparse.ArgumentParser(description="AI Daily News auto-collector")
    p.add_argument(
        "--provider",
        choices=["ollama", "nvidia"],
        default="ollama",
        help="LLM provider for summarization (default: ollama / local)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if today's output already exists",
    )
    return p.parse_args()


def build_processor(provider_name: str) -> LLMProcessor:
    provider = make_provider(provider_name)
    if not provider.available:
        logging.getLogger("auto_collect").warning(
            "[Main] %s provider unavailable; publication will be held",
            provider_name,
        )
    return LLMProcessor(provider=provider)


def _quality_log(today: date, payload: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / f"daily_quality_{today.isoformat()}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    args = parse_args()
    setup_logging()
    logger = logging.getLogger("auto_collect")

    today = date.today()
    mmdd = today.strftime("%m%d")
    output_path = INPUT_DAY_DIR / f"{mmdd}.txt"

    if output_path.exists() and not args.force:
        logger.info(f"[Main] {output_path} already exists, skipping (use --force to override)")
        return

    logger.info(f"[Main] Starting enhanced auto-collection for {today} (provider={args.provider})")

    # === Phase 1: Collect from all sources ===
    articles = []

    # RSS feeds
    try:
        rss = RSSAutoCollector().collect(today)
        articles.extend(rss)
    except Exception as e:
        logger.error(f"[Main] RSS failed: {e}")

    # Hacker News
    try:
        hn = HNAutoCollector().collect(today)
        articles.extend(hn)
    except Exception as e:
        logger.error(f"[Main] HN failed: {e}")

    # Japanese news
    try:
        jp = JPCollector().collect(today)
        articles.extend(jp)
    except Exception as e:
        logger.error(f"[Main] JP failed: {e}")

    # arXiv preprints (cs.AI / cs.CL / cs.LG, last 28h)
    try:
        ax = ArxivCollector().collect(today)
        articles.extend(ax)
    except Exception as e:
        logger.error(f"[Main] arXiv failed: {e}")

    # X bookmarks (Obsidian vault). Summarized and judged with the news provider below.
    # x_authoritative means this run read bookmarks and can filter them. A missing
    # vault or a collector error is not authoritative, so a same-day bundle that
    # already has X posts is kept. An empty window is also not authoritative.
    x_articles = []
    x_authoritative = False
    try:
        x_collector = XBookmarksCollector()
        x_articles = x_collector.collect(today)
        x_authoritative = bool(getattr(x_collector, "vault_available", bool(x_articles))) and bool(x_articles)
    except Exception as e:
        logger.error(f"[Main] X bookmarks failed: {e}")
        x_articles = []
        x_authoritative = False

    logger.info(f"[Main] Collected {len(articles)} raw articles + {len(x_articles)} X bookmarks")
    articles = deduplicate(articles)
    logger.info(f"[Main] {len(articles)} after dedup")

    # GitHub Trending AI repos
    github_raw = []
    try:
        github_raw = GitHubTrendingCollector().collect(today)
    except Exception as e:
        logger.error(f"[Main] GitHub Trending failed: {e}")

    # HuggingFace Trending Models
    benchmark_raw = []
    try:
        benchmark_raw = BenchmarkCollector().collect(today)
    except Exception as e:
        logger.error(f"[Main] Benchmark failed: {e}")

    # Funding / M&A
    funding_raw = []
    try:
        funding_raw = FundingCollector().collect(today)
    except Exception as e:
        logger.error(f"[Main] Funding failed: {e}")

    if not articles and not github_raw and not x_articles:
        _quality_log(today, {"date": today.isoformat(), "status": "failed",
                            "failure_reason": "collection_unavailable", "errors": ["No articles collected."]})
        logger.error("[Main] No headline, GitHub, or X bookmarks collected; aborting report generation")
        raise SystemExit(1)

    # Keep public-source observations available even when publication is held.
    # X bookmarks are deliberately omitted from diagnostic artifacts.
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / f"daily_candidate_{today.isoformat()}.json").write_text(
        json.dumps({"date": today.isoformat(), "articles": articles,
                    "github": github_raw, "models": benchmark_raw, "funding": funding_raw},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # === Phase 2: Process with LLM + Evidence ===
    processor = build_processor(args.provider)
    if not processor.available:
        reason = getattr(processor.provider, "last_error", "provider_unavailable")
        _quality_log(today, {"date": today.isoformat(), "status": "failed",
                            "provider": args.provider, "failure_reason": reason,
                            "errors": ["A production-authorized Japanese provider is unavailable."]})
        logger.error("[Main] Publication held: %s", reason)
        raise SystemExit(1)

    processed = processor.process_batch(articles)
    logger.info(f"[Main] Processed {len(processed)} news articles")

    github_processed = processor.process_github_repos(github_raw)
    logger.info(f"[Main] Processed {len(github_processed)} GitHub repos")

    benchmark_processed = processor.process_benchmarks(benchmark_raw)
    logger.info(f"[Main] Processed {len(benchmark_processed)} trending models")

    funding_processed = processor.process_funding(funding_raw)
    logger.info(f"[Main] Processed {len(funding_processed)} funding articles")

    x_processed = processor.process_x_posts(x_articles)
    logger.info(f"[Main] Processed {len(x_processed)} X bookmarks")

    # === Phase 2.5: Cross-section dedup (post-LLM) ===
    # Catches canonical-URL leakage across sections, HuggingFace base/quant
    # variants (Qwen/X + unsloth/X-GGUF), and same-story-multi-outlet
    # duplicates that survived the raw-stage dedup because the LLM rewrote
    # them into divergent Japanese headlines.
    before = (len(processed), len(funding_processed),
              len(benchmark_processed), len(github_processed))
    processed, funding_processed, benchmark_processed, github_processed = (
        dedup_mod.dedup_across_sections(
            headlines=processed,
            funding=funding_processed,
            models=benchmark_processed,
            github=github_processed,
        )
    )
    after = (len(processed), len(funding_processed),
             len(benchmark_processed), len(github_processed))
    if before != after:
        logger.info(
            f"[Main] Cross-section dedup: headlines {before[0]}->{after[0]}, "
            f"funding {before[1]}->{after[1]}, models {before[2]}->{after[2]}, "
            f"github {before[3]}->{after[3]}"
        )

    # News publishes today and yesterday only. Apply that window before the
    # gate so article_count and the 20% ratio match the page. X bookmarks are
    # already limited by X_LOOKBACK_HOURS at collection; applying this cutoff
    # again drops an entire overnight batch (for example every 10/13 bookmark
    # on a 10/15 02:49 run). Older news rows are not quality exclusions.
    def _in_window(rows):
        kept_rows = [row for row in rows if within_publication_window(row, today)]
        return kept_rows, len(rows) - len(kept_rows)

    processed, dropped_news = _in_window(processed)
    github_processed, dropped_github = _in_window(github_processed)
    benchmark_processed, dropped_models = _in_window(benchmark_processed)
    funding_processed, dropped_funding = _in_window(funding_processed)
    log_publication_window_drops(
        logger,
        news_dropped=dropped_news + dropped_github + dropped_models + dropped_funding,
        x_dropped=0,
        cutoff=today - timedelta(days=1),
    )

    # News and X share one gate. input_count, article_count, japanese_count,
    # sources, the minimum of 3 articles and 2 sources, and the 20% exclusion
    # ratio all use this combined list. A kept X post counts in those totals
    # and contributes its rss_source (typically "X (@author)"). A dropped post
    # is quality.excluded with a reason and is not published. There is no
    # separate X budget. Six unrelated posts among 64 combined items stay
    # under 20% and do not hold the day. excluded_item_count is the
    # normalizer's invalid-item counter and is not incremented here.
    all_news = processed + github_processed + benchmark_processed + funding_processed + x_processed
    kept, quality = filter_publishable(all_news, min_articles=3, min_sources=2)
    quality.update({"date": today.isoformat(), "provider": args.provider,
                    "model": getattr(getattr(processor.provider, "config", None), "model", "")})
    if quality["status"] != "passed":
        quality["failure_reason"] = failure_reason(all_news, quality)
        _quality_log(today, quality)
        logger.error("[Main] Publication held: %s", "; ".join(quality["errors"]))
        raise SystemExit(1)
    kept_ids = {id(article) for article in kept}
    processed = [article for article in processed if id(article) in kept_ids]
    github_processed = [article for article in github_processed if id(article) in kept_ids]
    benchmark_processed = [article for article in benchmark_processed if id(article) in kept_ids]
    funding_processed = [article for article in funding_processed if id(article) in kept_ids]
    x_processed = [article for article in x_processed if id(article) in kept_ids]
    if quality.get("excluded_count"):
        detail = "; ".join(
            f"article {row.get('index')}: {row.get('title') or ''} ({'; '.join(row.get('errors') or [])})"
            for row in quality.get("excluded") or []
        )
        logger.warning(
            "[Main] Excluded %d/%d articles: %s",
            quality["excluded_count"], quality["input_count"], detail,
        )
    _quality_log(today, quality)

    # === Phase 3: Write multi-section report ===
    formatter = DayFileFormatter()
    formatter.write(
        processed, output_path, today,
        github_articles=github_processed,
        benchmark_articles=benchmark_processed,
        funding_articles=funding_processed,
    )

    # Model watch is supplementary: a vendor outage must not block the report,
    # the dashboard simply omits the panel when no snapshot exists.
    try:
        model_watch.collect(today)
    except Exception as e:
        logger.warning(f"[Main] Model watch failed (continuing): {e}")

    # Rendering and indexing are required stages. Never log-and-continue a
    # failed stage or rewrite historical dates through legacy mtime guessing.
    try:
        html_path = generate_html_report(output_path)
        if not html_path:
            raise RuntimeError("HTML report not generated")
        dn_path = generate_daily_news(
            today, articles=processed, github_articles=github_processed,
            benchmark_articles=benchmark_processed, funding_articles=funding_processed,
            x_articles=x_processed, quality=quality, x_authoritative=x_authoritative,
        )
        if not dn_path:
            raise RuntimeError("Daily News not generated")
        for command in (
            [sys.executable, "scripts/sync_daily_search.py", "--root", str(PROJECT_ROOT)],
            ["node", "scripts/build-homepage-latest.js"],
            [sys.executable, "scripts/check_daily_publication.py", "--root", str(PROJECT_ROOT),
             "--date", today.isoformat(), "--require-quality"],
        ):
            subprocess.run(command, cwd=str(PROJECT_ROOT), check=True, timeout=120)
    except Exception as error:
        quality.update(status="failed", failure_reason="render_or_validation_failed",
                       errors=[f"Required publication stage failed: {type(error).__name__}"])
        _quality_log(today, quality)
        raise

    total = len(processed) + len(github_processed) + len(benchmark_processed) + len(funding_processed) + len(x_processed)
    logger.info(f"[Main] Done: {total} total items -> {output_path}")


if __name__ == "__main__":
    main()
