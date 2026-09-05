"""Offline, one-record preview; never publishes or rewrites the real feed."""
import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.auto_collect import daily_news_page
from src.auto_collect.content_integrity import CRUSOE_2026_09_05_URL, apply_financial_integrity
from src.auto_collect.formatter import DayFileFormatter
from src.auto_collect.html_report_parser import parse_daily_txt
from src.auto_collect.html_report import generate_html

OUT = ROOT / "outputs" / "content-integrity-2026-09-05" / "fixture-preview"
OUT.mkdir(parents=True, exist_ok=True)
article = {
    "title": "Crusoe、企業価値$30億との報道",
    "url": CRUSOE_2026_09_05_URL, "date": "2026-09-05",
    "source": "TechCrunch", "score": 85, "category": "Business",
    "tldr": "$30Bの評価で$3B調達", "summary": "企業価値は$30億。",
    "points": ["企業価値$30億"], "evidence": {"metrics": ["企業価値$30億"]},
}
with patch.object(daily_news_page, "DAILY_NEWS_DIR", OUT / "daily-news"), \
     patch.object(daily_news_page, "ARCHIVE_DIR", OUT / "daily-news" / "archive"):
    for _ in range(2):
        daily_news_page.generate_daily_news(date(2026, 9, 5), [article])
        DayFileFormatter().write([apply_financial_integrity(article)], OUT / "0905.txt", date(2026, 9, 5))
        html, report = generate_html(parse_daily_txt(OUT / "0905.txt"))
        (OUT / "top15.html").write_text(html, encoding="utf-8")
        (OUT / "top15.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
for relative in ("daily-news/index.html", "daily-news/data.json", "daily-news/archive/2026-09-05.html",
                 "0905.txt", "top15.html", "top15.json"):
    content = (OUT / relative).read_text(encoding="utf-8")
    assert "$30億" not in content, relative
    assert "300億米ドル" in content, relative
    print("PASS", relative)
print("PREVIEW ONLY: a single fixed fixture, not the complete September 5 feed:", OUT)
