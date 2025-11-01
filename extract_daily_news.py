#!/usr/bin/env python3
"""
daily-ai-news-pagesのHTMLからニュースデータを抽出してJSONに変換するスクリプト
"""
import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen, Request

class NewsCardParser(HTMLParser):
    """HTMLからニュースカード情報を抽出"""
    def __init__(self):
        super().__init__()
        self.articles = []
        self.current_article = None
        self.current_tag = None
        self.capture_text = False
        self.text_buffer = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # 新しい記事カードの開始
        if tag == 'article' and ('class', 'news-card') in attrs:
            self.current_article = {
                'category': attrs_dict.get('data-category', ''),
                'importance': attrs_dict.get('data-importance', ''),
                'score': float(attrs_dict.get('data-score', 0)),
                'freshness': int(attrs_dict.get('data-freshness', 0)),
                'freshness_bucket': attrs_dict.get('data-freshness-bucket', ''),
                'published_ms': int(attrs_dict.get('data-published-ms', 0)),
                'rank': int(attrs_dict.get('data-rank', 0)),
                'tags': attrs_dict.get('data-tags', '').split(','),
                'source': attrs_dict.get('data-source', ''),
                'title': '',
                'url': '',
                'summary': '',
                'published_at': '',
                'trust': ''
            }

        # タイトルリンク
        if self.current_article and tag == 'a' and ('class', 'news-card__title') in attrs:
            self.current_article['url'] = attrs_dict.get('href', '')
            self.current_tag = 'title'
            self.capture_text = True

        # 要約
        if self.current_article and tag == 'p' and ('class', 'news-card__summary') in attrs:
            self.current_tag = 'summary'
            self.capture_text = True

    def handle_data(self, data):
        if self.capture_text:
            self.text_buffer.append(data.strip())

    def handle_endtag(self, tag):
        # テキスト取り込み完了
        if self.capture_text and self.current_tag:
            text = ' '.join(self.text_buffer).strip()
            if self.current_tag == 'title':
                self.current_article['title'] = text
            elif self.current_tag == 'summary':
                self.current_article['summary'] = text

            self.text_buffer = []
            self.capture_text = False
            self.current_tag = None

        # 記事カード終了
        if tag == 'article' and self.current_article:
            # published_msをISO形式に変換
            if self.current_article['published_ms'] > 0:
                timestamp = self.current_article['published_ms'] / 1000
                self.current_article['published_at'] = datetime.fromtimestamp(timestamp).isoformat()

            self.articles.append(self.current_article)
            self.current_article = None

def fetch_and_parse(url):
    """URLからHTMLを取得してパース"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (AI News Archiver)'}
        request = Request(url, headers=headers)
        with urlopen(request, timeout=30) as response:
            html = response.read().decode('utf-8')

        parser = NewsCardParser()
        parser.feed(html)
        return parser.articles
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return []

def extract_metadata(html):
    """HTMLからメタデータを抽出"""
    meta = {
        'last_updated': '',
        'total_count': 0,
        'high_importance_count': 0,
        'source_count': 0
    }

    # 最終更新時刻
    match = re.search(r'最終更新.*?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', html)
    if match:
        meta['last_updated'] = match.group(1)

    # 記事件数
    match = re.search(r'(\d+)件.*?掲載記事数', html)
    if match:
        meta['total_count'] = int(match.group(1))

    # 重要度高
    match = re.search(r'(\d+)件.*?重要度\s+高', html)
    if match:
        meta['high_importance_count'] = int(match.group(1))

    # 情報源数
    match = re.search(r'(\d+)件.*?情報源', html)
    if match:
        meta['source_count'] = int(match.group(1))

    return meta

def main():
    """メイン処理"""
    url = 'https://awano27.github.io/daily-ai-news-pages/'

    print(f"Fetching data from {url}...")
    articles = fetch_and_parse(url)

    if not articles:
        print("No articles found!", file=sys.stderr)
        return 1

    # 日付ベースのファイル名
    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = Path('public-pages/news')
    output_path = output_dir / f'{today}_daily.json'

    # JSON出力
    output_data = {
        'metadata': {
            'source': 'daily-ai-news-pages',
            'url': url,
            'extracted_at': datetime.now().isoformat(),
            'total_articles': len(articles)
        },
        'articles': articles
    }

    # ファイル書き込み
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    update_daily_indexes(output_path, output_data)

    print(f"[OK] Extracted {len(articles)} articles to {output_path}")
    print(f"  Categories: {len(set(a['category'] for a in articles))}")
    print(f"  Sources: {len(set(a['source'] for a in articles))}")
    print(f"  High importance: {sum(1 for a in articles if a['importance'] == 'high')}")

    return 0


def update_daily_indexes(output_path: Path, data: dict) -> None:
    """Update helper index files for the daily news snapshots."""

    metadata = data.get('metadata', {})
    entry = {
        'date': output_path.stem.replace('_daily', ''),
        'file': output_path.name,
        'count': metadata.get('total_articles') or len(data.get('articles', []) or []),
        'extracted_at': metadata.get('extracted_at'),
        'source': metadata.get('source'),
    }

    index_path = output_path.parent / 'daily_index.json'
    entries = []

    if index_path.exists():
        try:
            entries = json.loads(index_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            entries = []

    entries = [e for e in entries if e.get('file') != entry['file']]
    entries.append(entry)

    def sort_key(item: dict) -> datetime:
        date_str = item.get('date', '')
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return datetime.min

    entries.sort(key=sort_key, reverse=True)

    index_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')

    latest_path = output_path.parent / 'daily_latest.json'
    latest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    print("  Updated daily_index.json and daily_latest.json")

if __name__ == '__main__':
    sys.exit(main())
