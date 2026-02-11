#!/usr/bin/env python3
"""
Daily AI News Sync
daily-ai-news-pagesサイトから最新ニュースを取得してアーカイブを同期
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import hashlib
import json
import re

import requests
from bs4 import BeautifulSoup, Tag


SOURCE_URL = "https://awano27.github.io/daily-ai-news-pages/"
OUTPUT_DIR = Path("public-pages/news")
INDEX_FILE_NAME = "archive_index.json"
VERSION_FILE_NAME = "version.json"
DEFAULT_CATEGORY = "AI News"

TIME_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(\d+)分前"), "minutes"),
    (re.compile(r"(\d+)時間前"), "hours"),
    (re.compile(r"(\d+)日前"), "days"),
    (re.compile(r"(\d+)週間前"), "weeks"),
)

CATEGORY_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("ビジネス", "business"), "ビジネス"),
    (("ツール", "tool"), "ツール"),
    (("sns", "論文"), "SNS/論文"),
)


@dataclass
class NewsItem:
    """抽出済みニュース項目"""

    title: str
    url: str
    summary: str
    source: str
    category: str
    time_info: str
    estimated_datetime: datetime
    score: int
    rank: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "source": self.source,
            "category": self.category,
            "time_info": self.time_info,
            "estimated_date": self.estimated_datetime.strftime("%Y-%m-%d"),
            "estimated_datetime": self.estimated_datetime.isoformat(),
            "score": self.score,
            "rank": self.rank,
        }


def fetch_daily_ai_news(url: str = SOURCE_URL, timeout: int = 30) -> str | None:
    """daily-ai-news-pagesサイトからニュースデータを取得"""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        print(f"Error fetching data from {url}: {exc}")
        return None


def parse_time_info(chip_text: str, *, now: datetime | None = None) -> datetime:
    """時間情報を解析して投稿日時を推定"""
    reference_now = now or datetime.now()
    if not chip_text:
        return reference_now

    for pattern, unit in TIME_PATTERNS:
        match = pattern.search(chip_text)
        if match:
            value = int(match.group(1))

            if unit == "minutes":
                return reference_now - timedelta(minutes=value)
            if unit == "hours":
                return reference_now - timedelta(hours=value)
            if unit == "days":
                return reference_now - timedelta(days=value)
            if unit == "weeks":
                return reference_now - timedelta(weeks=value)

    return reference_now


def _find_cards(soup: BeautifulSoup) -> list[Tag]:
    cards = list(soup.select(".news-card"))
    if cards:
        return cards
    return list(soup.select("div.card"))


def _extract_text(element: Tag | None) -> str:
    return element.get_text(strip=True) if element else ""


def _extract_url(card: Tag, title_elem: Tag, base_url: str) -> str:
    link_elem = title_elem if title_elem.name == "a" else title_elem.find("a") or card.find("a")
    if not link_elem:
        return ""

    href = link_elem.get("href", "").strip()
    if not href:
        return ""
    return urljoin(base_url, href)


def _detect_category(card: Tag) -> str:
    category = str(card.get("data-category", "")).strip()
    if category:
        return category

    tags_text = _extract_text(card.select_one(".news-card__taglist")).lower()
    for keywords, mapped_category in CATEGORY_RULES:
        if any(keyword in tags_text for keyword in keywords):
            return mapped_category
    return DEFAULT_CATEGORY


def _calculate_score(title: str, summary: str, url: str, source: str) -> int:
    return min(
        100,
        max(
            20,
            len(title) // 2
            + len(summary) // 10
            + (20 if url.startswith("http") else 0)
            + (10 if source else 0),
        ),
    )


def extract_news_items(
    html_content: str,
    *,
    now: datetime | None = None,
    base_url: str = SOURCE_URL,
) -> list[dict[str, Any]]:
    """HTMLからニュース項目を抽出"""
    soup = BeautifulSoup(html_content, "html.parser")
    cards = _find_cards(soup)
    if not cards:
        print("No news cards found in source HTML.")
        return []

    reference_now = now or datetime.now()
    news_items: list[NewsItem] = []
    print(f"Found {len(cards)} news cards")

    for idx, card in enumerate(cards):
        try:
            title_elem = card.select_one(".news-card__title, .card-title")

            if title_elem is None:
                continue

            title = title_elem.get_text(" ", strip=True)
            if not title:
                continue

            url = _extract_url(card, title_elem, base_url)
            summary = _extract_text(card.select_one(".news-card__summary, .card-text"))
            source = _extract_text(card.select_one(".news-card__source"))
            time_info = _extract_text(card.select_one(".news-card__time, small.text-muted"))
            category = _detect_category(card)
            estimated_datetime = parse_time_info(time_info, now=reference_now)
            score = _calculate_score(title, summary, url, source)

            news_items.append(
                NewsItem(
                    title=title,
                    url=url,
                    summary=summary,
                    source=source,
                    category=category,
                    time_info=time_info,
                    estimated_datetime=estimated_datetime,
                    score=score,
                    rank=len(news_items) + 1,
                )
            )
            print(f"Extracted: {title[:50]}...")

        except Exception as exc:
            print(f"Warning: error parsing card {idx}: {exc}")
            continue

    return [item.to_dict() for item in news_items]


def group_news_by_date(news_items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """ニュース項目を日付でグループ化"""
    date_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in news_items:
        date = str(item.get("estimated_date", datetime.now().strftime("%Y-%m-%d")))
        date_groups[date].append(dict(item))

    # 各日付内でスコア順にソート
    for date, items in date_groups.items():
        items.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
        # ランクを再設定
        for i, item in enumerate(items):
            item["rank"] = i + 1

    return {date: date_groups[date] for date in sorted(date_groups.keys(), reverse=True)}


def create_archive_format(date: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
    """アーカイブ形式のJSONデータを作成"""
    # 代表的なニュース項目を選択（最高スコア）
    top_item = max(items, key=lambda x: int(x.get("score", 0))) if items else None

    if not top_item:
        return None

    # ポイント形式に変換
    points: list[str] = []
    for item in items[:5]:  # 上位5件
        point = f"[{item.get('category', DEFAULT_CATEGORY)}] {item.get('title', '')}"
        source = item.get("source", "")
        if source:
            point += f" (出典: {source})"
        points.append(point)

    # リンク形式に変換
    links: list[dict[str, str]] = []
    for item in items[:10]:  # 上位10件
        url = item.get("url", "")
        if url:
            links.append(
                {
                    "href": url,
                    "text": f"{item.get('title', '')} - {item.get('category', DEFAULT_CATEGORY)}",
                }
            )

    category_counts = Counter(item.get("category", "") for item in items)
    top_categories = [item.get("category", DEFAULT_CATEGORY) for item in items[:3]]
    top_categories_str = ", ".join(filter(None, top_categories)) or DEFAULT_CATEGORY

    # メインアイテムを作成
    main_item = {
        "title": f"AI News Digest {date}",
        "score": int(top_item.get("score", 0)),
        "rank": 1,
        "url": top_item.get("url", ""),
        "date": date,
        "summary": (
            f"本日の主要AI関連ニュース{len(items)}件を収集。"
            f"{top_item.get('title', '')}をはじめ、{top_categories_str}分野での動きが活発。"
        ),
        "points": points,
        "links": links,
        "category_breakdown": {
            "business": category_counts.get("ビジネス", 0),
            "tools": category_counts.get("ツール", 0),
            "posts": category_counts.get("SNS/論文", 0),
        },
        "source_items": items,  # 元データも保持
    }

    return {
        "date": date,
        "source": SOURCE_URL,
        "count": len(items),
        "items": [main_item],
    }


def _load_archive_index(index_file: Path) -> list[dict[str, Any]]:
    if not index_file.exists():
        return []

    try:
        loaded = json.loads(index_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Warning: failed to parse {index_file}: {exc}")
        return []

    if not isinstance(loaded, list):
        return []

    return [item for item in loaded if isinstance(item, dict) and "date" in item]


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _upsert_index_entry(
    existing_index: list[dict[str, Any]],
    index_entry: dict[str, Any],
) -> None:
    date = index_entry["date"]
    for idx, item in enumerate(existing_index):
        if item.get("date") == date:
            existing_index[idx] = index_entry
            return
    existing_index.append(index_entry)


def _build_version_data(now: datetime, total_entries: int) -> dict[str, Any]:
    now_iso = now.isoformat()
    return {
        "version": now_iso,
        "sha": hashlib.md5(now_iso.encode()).hexdigest()[:8],
        "updated": now.strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": total_entries,
        "source": "daily-ai-news-pages",
        "sync_time": now_iso,
    }


def sync_with_existing_archive(
    source_url: str = SOURCE_URL,
    output_dir: Path = OUTPUT_DIR,
) -> bool:
    """既存のアーカイブと同期"""
    print("Fetching latest news from daily-ai-news-pages...")

    html_content = fetch_daily_ai_news(source_url)
    if not html_content:
        print("Failed to fetch news data")
        return False

    run_time = datetime.now()
    news_items = extract_news_items(html_content, now=run_time, base_url=source_url)
    if not news_items:
        print("No news items found")
        return False

    print(f"Extracted {len(news_items)} news items")

    date_groups = group_news_by_date(news_items)
    print(f"Grouped into {len(date_groups)} dates")

    output_dir.mkdir(parents=True, exist_ok=True)

    index_file = output_dir / INDEX_FILE_NAME
    existing_index = _load_archive_index(index_file)
    existing_dates = {str(item.get("date")) for item in existing_index if item.get("date")}

    updated_count = 0
    today = run_time.strftime("%Y-%m-%d")

    # 各日付のデータを処理
    for date, items in date_groups.items():
        json_file = output_dir / f"{date}.json"
        should_update = (date == today) or (date not in existing_dates)
        if not should_update:
            continue

        archive_data = create_archive_format(date, items)
        if not archive_data:
            continue

        _write_json(json_file, archive_data)

        index_entry = {
            "date": date,
            "file": f"{date}.json",
            "count": len(items),
        }

        _upsert_index_entry(existing_index, index_entry)
        existing_dates.add(date)
        updated_count += 1
        print(f"Updated: {date} ({len(items)} items)")

    existing_index.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    _write_json(index_file, existing_index)

    version_file = output_dir / VERSION_FILE_NAME
    _write_json(version_file, _build_version_data(run_time, total_entries=len(existing_index)))

    print("\nSync completed:")
    print(f"- Updated entries: {updated_count}")
    print(f"- Total entries: {len(existing_index)}")
    print(f"- Latest date: {existing_index[0]['date'] if existing_index else 'None'}")
    print("- Source: daily-ai-news-pages")

    return updated_count > 0


if __name__ == "__main__":
    success = sync_with_existing_archive()
    if success:
        print("\nDaily AI News sync completed successfully!")
    else:
        print("\nNo updates needed.")
