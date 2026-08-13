#!/usr/bin/env python3
"""
html_report.py — Orchestrator: parse → render → save daily HTML report.

Heavy lifting is delegated to:
  html_report_parser.py   — parse_daily_txt, build_report_data
  html_report_renderer.py — generate_html + all render helpers
  html_report_archive.py  — rebuild_archive_index, ARCHIVE_INDEX_PATH

Public symbols re-exported here so all existing callers keep working:
  generate_html_report  (src.auto_collect.main imports this)
  rebuild_archive_index (scripts/build_daily_reports_index.py imports this)
  ARCHIVE_INDEX_PATH    (scripts/build_daily_reports_index.py imports this)
"""

import json
import logging
from datetime import date
from pathlib import Path

from .config import PROJECT_ROOT, INPUT_DAY_DIR
from . import ogp_generator

# Re-export for backward-compatible imports
from .html_report_parser import parse_daily_txt, build_report_data  # noqa: F401
from .html_report_renderer import generate_html as _generate_html  # internal alias
from .html_report_archive import rebuild_archive_index, ARCHIVE_INDEX_PATH  # noqa: F401
from .html_report_archive import ARCHIVE_DIR

logger = logging.getLogger(__name__)

OUTPUT_PATH = PROJECT_ROOT / "presentations" / "auto_daily_report.html"
JSON_OUTPUT_PATH = PROJECT_ROOT / "presentations" / "auto_daily_report.json"
PUBLIC_API_DIR = PROJECT_ROOT / "public-pages" / "api" / "auto_daily_report"
DEFAULT_OG_IMAGE = "https://visionhub.jp/presentations/daily_reports/og/default.png"


def generate_html(data: dict, canonical_url: str | None = None):
    """Thin shim: delegates to html_report_renderer.generate_html."""
    return _generate_html(
        data,
        archive_dir=ARCHIVE_DIR,
        default_og_image=DEFAULT_OG_IMAGE,
        canonical_url=canonical_url,
    )


def generate_html_report(txt_path: Path = None):
    """Main entry: parse txt and generate HTML + JSON outputs.

    Saves:
      - presentations/auto_daily_report.html      (latest, always overwritten)
      - presentations/auto_daily_report.json      (machine-readable mirror)
      - presentations/daily_reports/auto_daily_report_YYYY_MM_DD.html  (archive)
      - presentations/daily_reports/index.json    (rebuilt from directory)
      - public-pages/api/auto_daily_report/latest.json (CDN-friendly API)
    """
    if txt_path is None:
        mmdd = date.today().strftime("%m%d")
        txt_path = INPUT_DAY_DIR / f"{mmdd}.txt"

    if not txt_path.exists():
        logger.warning(f"[HTML] {txt_path} not found")
        return None

    logger.info(f"[HTML] Generating report from {txt_path}")
    data = parse_daily_txt(txt_path)
    latest_canonical = "https://visionhub.jp/presentations/auto_daily_report.html"
    html, report_data = generate_html(data, canonical_url=latest_canonical)

    # Save latest HTML
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    logger.info(f"[HTML] Report saved: {OUTPUT_PATH}")

    # Save JSON mirror (full data, including headlines)
    json_payload = json.dumps(report_data, ensure_ascii=False, indent=2) + "\n"
    JSON_OUTPUT_PATH.write_text(json_payload, encoding="utf-8")
    logger.info(f"[HTML] JSON saved: {JSON_OUTPUT_PATH}")

    # Public API copy (served by GitHub Pages)
    PUBLIC_API_DIR.mkdir(parents=True, exist_ok=True)
    (PUBLIC_API_DIR / "latest.json").write_text(json_payload, encoding="utf-8")

    # Save dated archive
    report_date = data.get("date") or date.today().isoformat()
    archive_filename = f"auto_daily_report_{report_date.replace('-', '_')}.html"
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / archive_filename
    archive_canonical = f"https://visionhub.jp/presentations/daily_reports/{archive_filename}"
    archive_html = html.replace(latest_canonical, archive_canonical)
    archive_path.write_text(archive_html, encoding="utf-8")
    logger.info(f"[HTML] Archive saved: {archive_path}")

    # OGP image (best-effort — silently skipped if Pillow unavailable)
    try:
        top_titles = [
            h.get("title", "")
            for h in sorted(
                report_data.get("headlines", []),
                key=lambda h: h.get("score", 0),
                reverse=True,
            )[:3]
        ]
        ogp_generator.render(
            report_date=report_date,
            total=report_data.get("total", 0),
            high=len([h for h in report_data.get("headlines", []) if h.get("score", 0) >= 80]),
            top_titles=top_titles,
        )
    except Exception as e:
        logger.warning(f"[HTML] OGP generation failed (continuing): {e}")

    # Rebuild the archive index.json consumed by daily_reports_archive.html
    count = rebuild_archive_index()
    logger.info(f"[HTML] Archive index rebuilt: {ARCHIVE_INDEX_PATH} ({count} reports)")

    return OUTPUT_PATH


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    generate_html_report(path)
