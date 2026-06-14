"""src/utils — shared low-level utilities."""

from .encoding import read_text, write_text, read_json, write_json, open_utf8
from .dates import mmdd_to_iso, filename_to_iso, today_mmdd, today_iso, now_jst_str, iso_to_japanese
from .paths import (
    PROJECT_ROOT,
    INPUT_DAY_DIR,
    NEWS_DIR,
    PUBLIC_NEWS_DIR,
    DAY_SLIDES_DIR,
    DAILY_NEWS_DIR,
    DAILY_REPORTS_DIR,
    PUBLIC_AUTO_REPORT_DIR,
    TEMPLATES_DIR,
    LOG_DIR,
    ARCHIVE_INDEX_FILE,
    VERSION_FILE,
    news_json_path,
    public_news_json_path,
    slide_html_path,
    slide_images_dir,
    input_day_txt,
    daily_report_html_path,
    ensure_dirs,
)

__all__ = [
    # encoding
    "read_text", "write_text", "read_json", "write_json", "open_utf8",
    # dates
    "mmdd_to_iso", "filename_to_iso", "today_mmdd", "today_iso",
    "now_jst_str", "iso_to_japanese",
    # paths — constants
    "PROJECT_ROOT", "INPUT_DAY_DIR", "NEWS_DIR", "PUBLIC_NEWS_DIR",
    "DAY_SLIDES_DIR", "DAILY_NEWS_DIR", "DAILY_REPORTS_DIR",
    "PUBLIC_AUTO_REPORT_DIR", "TEMPLATES_DIR", "LOG_DIR",
    "ARCHIVE_INDEX_FILE", "VERSION_FILE",
    # paths — builders
    "news_json_path", "public_news_json_path", "slide_html_path",
    "slide_images_dir", "input_day_txt", "daily_report_html_path",
    "ensure_dirs",
]
