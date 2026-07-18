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
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import List, Dict

from .config import PROJECT_ROOT, INPUT_DAY_DIR, LOG_DIR
from .collectors import RSSAutoCollector, HNAutoCollector, JPCollector, XBookmarksCollector
from .collectors.github_trending import GitHubTrendingCollector
from .collectors.benchmark_collector import BenchmarkCollector
from .collectors.funding_collector import FundingCollector
from .collectors.arxiv_collector import ArxivCollector
from .llm_provider import make_provider
from .processor import LLMProcessor
from .formatter import DayFileFormatter
from .html_report import generate_html_report
from .daily_news_page import generate_daily_news
from . import dedup as dedup_mod


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
            "[Main] %s provider unavailable; using deterministic heuristic fallback",
            provider_name,
        )
    return LLMProcessor(provider=provider)


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

    # X bookmarks (read from Obsidian vault — pre-curated by the user, no LLM)
    x_articles = []
    try:
        x_articles = XBookmarksCollector().collect(today)
    except Exception as e:
        logger.error(f"[Main] X bookmarks failed: {e}")

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

    if not articles and not github_raw:
        logger.error("[Main] No headline or GitHub articles collected; aborting report generation")
        raise SystemExit(1)

    # === Phase 2: Process with LLM + Evidence ===
    processor = build_processor(args.provider)

    processed = processor.process_batch(articles)
    logger.info(f"[Main] Processed {len(processed)} news articles")

    github_processed = processor.process_github_repos(github_raw)
    logger.info(f"[Main] Processed {len(github_processed)} GitHub repos")

    benchmark_processed = processor.process_benchmarks(benchmark_raw)
    logger.info(f"[Main] Processed {len(benchmark_processed)} trending models")

    funding_processed = processor.process_funding(funding_raw)
    logger.info(f"[Main] Processed {len(funding_processed)} funding articles")

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

    # === Phase 3: Write multi-section report ===
    formatter = DayFileFormatter()
    formatter.write(
        processed, output_path, today,
        github_articles=github_processed,
        benchmark_articles=benchmark_processed,
        funding_articles=funding_processed,
    )

    # === Phase 4: Update archive ===
    archive_script = PROJECT_ROOT / "update_news_archive.py"
    if archive_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(archive_script)],
                cwd=str(PROJECT_ROOT), timeout=60,
            )
            logger.info("[Main] Archive updated")
        except Exception as e:
            logger.warning(f"[Main] Archive update failed: {e}")

    # === Phase 5: Generate HTML report (auto_daily_report — Top15 curated) ===
    try:
        html_path = generate_html_report(output_path)
        if html_path:
            logger.info(f"[Main] HTML report: {html_path}")
    except Exception as e:
        logger.warning(f"[Main] HTML report generation failed: {e}")

    # === Phase 6: Generate daily-news/ page (full timeline incl. X bookmarks) ===
    try:
        dn_path = generate_daily_news(
            today,
            articles=processed,
            github_articles=github_processed,
            benchmark_articles=benchmark_processed,
            funding_articles=funding_processed,
            x_articles=x_articles,
        )
        if dn_path:
            logger.info(f"[Main] daily-news page: {dn_path}")
    except Exception as e:
        logger.warning(f"[Main] daily-news generation failed: {e}")

    total = len(processed) + len(github_processed) + len(benchmark_processed) + len(funding_processed) + len(x_articles)
    logger.info(f"[Main] Done: {total} total items -> {output_path}")


if __name__ == "__main__":
    main()
