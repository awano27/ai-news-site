#!/usr/bin/env python3
"""
Daily AI News Auto-Collector (Enhanced)
Collects from RSS, HN, JP news, GitHub Trending, HuggingFace, Funding/M&A.
Processes with Ollama for summarization + evidence extraction.
Outputs multi-section report to input/day/MMDD.txt.
"""

import logging
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import List, Dict

from .config import PROJECT_ROOT, INPUT_DAY_DIR, LOG_DIR
from .collectors import RSSAutoCollector, HNAutoCollector, JPCollector
from .collectors.github_trending import GitHubTrendingCollector
from .collectors.benchmark_collector import BenchmarkCollector
from .collectors.funding_collector import FundingCollector
from .processor import OllamaProcessor
from .formatter import DayFileFormatter
from .html_report import generate_html_report


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
    seen_urls = set()
    unique = []
    for article in articles:
        url = article.get("links", {}).get("official", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)
        elif not url:
            unique.append(article)
    return unique


def main():
    setup_logging()
    logger = logging.getLogger("auto_collect")

    today = date.today()
    mmdd = today.strftime("%m%d")
    output_path = INPUT_DAY_DIR / f"{mmdd}.txt"

    if output_path.exists():
        logger.info(f"[Main] {output_path} already exists, skipping")
        return

    logger.info(f"[Main] Starting enhanced auto-collection for {today}")

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

    logger.info(f"[Main] Collected {len(articles)} raw articles")
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
        logger.warning("[Main] No articles collected")
        return

    # === Phase 2: Process with Ollama + Evidence ===
    processor = OllamaProcessor()

    processed = processor.process_batch(articles)
    logger.info(f"[Main] Processed {len(processed)} news articles")

    github_processed = processor.process_github_repos(github_raw)
    logger.info(f"[Main] Processed {len(github_processed)} GitHub repos")

    benchmark_processed = processor.process_benchmarks(benchmark_raw)
    logger.info(f"[Main] Processed {len(benchmark_processed)} trending models")

    funding_processed = processor.process_funding(funding_raw)
    logger.info(f"[Main] Processed {len(funding_processed)} funding articles")

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

    # === Phase 5: Generate HTML report ===
    try:
        html_path = generate_html_report(output_path)
        if html_path:
            logger.info(f"[Main] HTML report: {html_path}")
    except Exception as e:
        logger.warning(f"[Main] HTML report generation failed: {e}")

    total = len(processed) + len(github_processed) + len(benchmark_processed) + len(funding_processed)
    logger.info(f"[Main] Done: {total} total items -> {output_path}")


if __name__ == "__main__":
    main()
