#!/usr/bin/env python3
"""
daily-ai-news-pagesのHTMLからニュースデータを抽出してJSONに変換するスクリプト
"""
import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
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
    output_file = f'public-pages/news/{today}_daily.json'

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

    # ディレクトリ作成
    import os
    os.makedirs('public-pages/news', exist_ok=True)

    # ファイル書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Extracted {len(articles)} articles to {output_file}")
    print(f"  Categories: {len(set(a['category'] for a in articles))}")
    print(f"  Sources: {len(set(a['source'] for a in articles))}")
    print(f"  High importance: {sum(1 for a in articles if a['importance'] == 'high')}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
