#!/usr/bin/env python3
"""
Daily AI News Auto-Collector (Enhanced)
Collects from RSS, HN, JP news, GitHub Trending, HuggingFace, Funding/M&A.
Processes with an LLM (local Ollama by default; --provider nvidia for cloud)
for summarization + evidence extraction.
Outputs multi-section report to input/day/MMDD.txt.
"""

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, List, Dict

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
from .output_validation import validate_output_artifact
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
    p.add_argument(
        "--run-id",
        help="Identifier shared with the publication step (generated when omitted)",
    )
    return p.parse_args()


def _safe_run_id(value: str | None) -> str:
    run_id = value or uuid.uuid4().hex
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", run_id):
        raise SystemExit("--run-id must contain only letters, digits, dot, underscore, or hyphen")
    return run_id


def _artifact_specs(project_root: Path, output_path: Path, today: date) -> tuple[tuple[str, bool, Path], ...]:
    return (
        ("report_text", True, output_path),
        ("archive", True, project_root / "public-pages" / "news" / f"{today}.json"),
        ("archive", True, project_root / "public-pages" / "news" / "archive_index.json"),
        ("archive", True, project_root / "public-pages" / "news" / "version.json"),
        ("html_report", True, project_root / "presentations" / "auto_daily_report.html"),
        ("html_report", True, project_root / "presentations" / "auto_daily_report.json"),
        (
            "html_report",
            True,
            project_root
            / "presentations"
            / "daily_reports"
            / f"auto_daily_report_{today:%Y_%m_%d}.html",
        ),
        ("html_report", True, project_root / "presentations" / "daily_reports" / "index.json"),
        ("html_report", True, project_root / "presentations" / "daily_reports" / "searchable.json"),
        (
            "html_report",
            True,
            project_root / "public-pages" / "api" / "auto_daily_report" / "latest.json",
        ),
        ("daily_news", True, project_root / "daily-news" / "data.json"),
        ("daily_news", True, project_root / "daily-news" / "index.html"),
        ("daily_news", True, project_root / "daily-news" / "archive" / f"{today}.html"),
        (
            "og_image",
            False,
            project_root
            / "presentations"
            / "daily_reports"
            / "og"
            / f"{today:%Y_%m_%d}.png",
        ),
    )


def _file_state(path: Path) -> tuple[int, int, str] | None:
    if not path.is_file():
        return None
    content = path.read_bytes()
    stat = path.stat()
    return len(content), stat.st_mtime_ns, hashlib.sha256(content).hexdigest()


def _artifact_record(
    project_root: Path,
    phase: str,
    required: bool,
    path: Path,
    before: tuple[int, int, str] | None,
) -> dict[str, Any]:
    after = _file_state(path)
    try:
        relative_path = path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as error:
        raise RuntimeError(f"artifact is outside the project root: {path}") from error
    return {
        "path": relative_path,
        "phase": phase,
        "required": required,
        "exists": after is not None,
        "fresh": after is not None and after != before,
        "size": after[0] if after else None,
        "mtime_ns": after[1] if after else None,
        "sha256": after[2] if after else None,
    }


def _write_run_result(
    project_root: Path,
    today: date,
    run_id: str,
    started_at: datetime,
    phases: dict[str, dict[str, bool]],
    artifacts: list[dict[str, Any]],
) -> Path:
    failure_count = sum(not phase["success"] for phase in phases.values())
    required_failure_count = sum(
        phase["required"] and not phase["success"] for phase in phases.values()
    )
    publication_ready = all(
        phase["success"] for phase in phases.values() if phase["required"]
    )
    payload = {
        "schema_version": 1,
        "date": today.isoformat(),
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "phases": phases,
        "artifacts": artifacts,
        "failure_count": failure_count,
        "required_failure_count": required_failure_count,
        "publication_ready": publication_ready,
    }
    path = (
        project_root
        / "public-pages"
        / "api"
        / "auto_daily_report"
        / "run"
        / f"{today}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary_path.replace(path)
    return path


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
    run_id = _safe_run_id(getattr(args, "run_id", None))
    started_at = datetime.now(timezone.utc)
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

    artifact_specs = _artifact_specs(PROJECT_ROOT, output_path, today)
    before_states = {path: _file_state(path) for _phase, _required, path in artifact_specs}
    phase_operation_success = {
        "report_text": False,
        "archive": False,
        "html_report": False,
        "daily_news": False,
    }

    # === Phase 3: Write multi-section report ===
    try:
        formatter = DayFileFormatter()
        formatter.write(
            processed, output_path, today,
            github_articles=github_processed,
            benchmark_articles=benchmark_processed,
            funding_articles=funding_processed,
        )
        phase_operation_success["report_text"] = True
    except Exception as error:
        logger.error(f"[Main] report text generation failed: {error}")

    # === Phase 4: Update archive ===
    archive_script = PROJECT_ROOT / "update_news_archive.py"
    if phase_operation_success["report_text"] and archive_script.exists():
        try:
            archive_result = subprocess.run(
                [sys.executable, str(archive_script)],
                cwd=str(PROJECT_ROOT), timeout=60,
            )
            if archive_result.returncode != 0:
                logger.error(
                    f"[Main] Archive update failed with exit code {archive_result.returncode}"
                )
            else:
                phase_operation_success["archive"] = True
                logger.info("[Main] Archive updated")
        except Exception as error:
            logger.error(f"[Main] Archive update failed: {error}")
    elif phase_operation_success["report_text"]:
        logger.error(f"[Main] Archive update script is missing: {archive_script}")

    # === Phase 5: Generate HTML report (auto_daily_report — Top15 curated) ===
    if phase_operation_success["report_text"]:
        try:
            html_path = generate_html_report(output_path)
            expected_html_path = PROJECT_ROOT / "presentations" / "auto_daily_report.html"
            if html_path and Path(html_path).resolve() == expected_html_path.resolve():
                phase_operation_success["html_report"] = True
            else:
                logger.error("[Main] HTML report generation returned no expected output")
            if html_path:
                logger.info(f"[Main] HTML report: {html_path}")
        except Exception as error:
            logger.error(f"[Main] HTML report generation failed: {error}")

    # === Phase 6: Generate daily-news/ page (full timeline incl. X bookmarks) ===
    if phase_operation_success["report_text"]:
        try:
            dn_path = generate_daily_news(
                today,
                articles=processed,
                github_articles=github_processed,
                benchmark_articles=benchmark_processed,
                funding_articles=funding_processed,
                x_articles=x_articles,
            )
            expected_dn_path = PROJECT_ROOT / "daily-news" / "index.html"
            if dn_path and Path(dn_path).resolve() == expected_dn_path.resolve():
                phase_operation_success["daily_news"] = True
            else:
                logger.error("[Main] daily-news generation returned no expected output")
            if dn_path:
                logger.info(f"[Main] daily-news page: {dn_path}")
        except Exception as error:
            logger.error(f"[Main] daily-news generation failed: {error}")

    artifacts = [
        _artifact_record(
            PROJECT_ROOT,
            phase,
            required,
            path,
            before_states[path],
        )
        for phase, required, path in artifact_specs
    ]
    for artifact in artifacts:
        validation_errors = (
            validate_output_artifact(PROJECT_ROOT, artifact["path"], today)
            if artifact["required"] and artifact["exists"]
            else []
        )
        artifact["valid"] = artifact["exists"] and not validation_errors
        for error in validation_errors:
            logger.error(f"[Main] {error}")
    phases: dict[str, dict[str, bool]] = {}
    for phase in ("report_text", "archive", "html_report", "daily_news"):
        phase_artifacts = [artifact for artifact in artifacts if artifact["phase"] == phase]
        phases[phase] = {
            "required": True,
            "success": phase_operation_success[phase]
            and all(
                artifact["exists"] and artifact["fresh"] and artifact["valid"]
                for artifact in phase_artifacts
            ),
        }
    optional_artifacts = [artifact for artifact in artifacts if artifact["phase"] == "og_image"]
    phases["og_image"] = {
        "required": False,
        "success": all(
            artifact["exists"] and artifact["fresh"] for artifact in optional_artifacts
        ),
    }
    result_path = _write_run_result(
        PROJECT_ROOT, today, run_id, started_at, phases, artifacts
    )
    publication_ready = all(
        phase["success"] for phase in phases.values() if phase["required"]
    )
    if not publication_ready:
        logger.error(f"[Main] Required generation failed; run result: {result_path}")
        raise SystemExit(1)

    total = len(processed) + len(github_processed) + len(benchmark_processed) + len(funding_processed) + len(x_articles)
    logger.info(f"[Main] Done: {total} total items -> {output_path} (run_id={run_id})")


if __name__ == "__main__":
    main()
