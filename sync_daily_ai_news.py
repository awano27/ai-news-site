#!/usr/bin/env python3
"""
Daily AI News Sync
daily-ai-news-pagesサイトから最新ニュースを取得してアーカイブを同期
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import time

def fetch_daily_ai_news():
    """daily-ai-news-pagesサイトからニュースデータを取得"""
    url = "https://awano27.github.io/daily-ai-news-pages/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def parse_time_info(chip_text):
    """時間情報を解析して投稿日時を推定"""
    # "X時間前", "X日前", "X週間前" などのパターン
    time_patterns = [
        (r'(\d+)時間前', 'hours'),
        (r'(\d+)日前', 'days'), 
        (r'(\d+)週間前', 'weeks'),
        (r'(\d+)分前', 'minutes')
    ]
    
    for pattern, unit in time_patterns:
        match = re.search(pattern, chip_text)
        if match:
            value = int(match.group(1))
            now = datetime.now()
            
            if unit == 'minutes':
                return now - timedelta(minutes=value)
            elif unit == 'hours':
                return now - timedelta(hours=value)
            elif unit == 'days':
                return now - timedelta(days=value)
            elif unit == 'weeks':
                return now - timedelta(weeks=value)
    
    # デフォルトは今日
    return datetime.now()

def extract_news_items(html_content):
    """HTMLからニュース項目を抽出"""
    soup = BeautifulSoup(html_content, 'html.parser')
    news_items = []

    # news-cardクラスを持つ要素を検索
    cards = soup.find_all(class_='news-card')

    # news-cardが見つからない場合は従来の方法で検索
    if not cards:
        cards = soup.find_all('div', class_='card')
    
    if not cards:
        print("No cards found with class 'card'")
        # デバッグ: 他の可能な構造を探す
        all_divs = soup.find_all('div')
        print(f"Found {len(all_divs)} div elements")
        
        # 実際の構造をデバッグ出力
        print("\nDebugging HTML structure...")
        
        # ニュース関連のクラスを探す
        for class_name in ['news', 'article', 'item', 'post', 'entry']:
            elements = soup.find_all(class_=lambda x: x and class_name in str(x).lower())
            if elements:
                print(f"Found {len(elements)} elements with class containing '{class_name}'")
                if elements:
                    print(f"Sample class: {elements[0].get('class')}")
        
        # h1, h2, h3のタイトル要素を探す
        titles = soup.find_all(['h1', 'h2', 'h3'])
        print(f"Found {len(titles)} title elements (h1-h3)")
        if titles:
            for i, title in enumerate(titles[:5]):  # 最初の5つを表示
                title_text = title.get_text(strip=True)[:100]
                print(f"Title {i+1}: {title_text.encode('ascii', 'ignore').decode('ascii')}")
        
        # タブパネルを探す
        tab_panels = soup.find_all('div', class_=lambda x: x and 'tab' in str(x).lower())
        print(f"Found {len(tab_panels)} elements with 'tab' in class")
        
        return []
    
    print(f"Found {len(cards)} news cards")
    
    for i, card in enumerate(cards):
        try:
            # news-card構造の場合
            title_elem = (card.find(class_='news-card__title') or
                         card.find(class_='card-title'))

            if not title_elem:
                # タイトル要素が見つからない場合はスキップ
                continue

            title = title_elem.get_text(strip=True)

            # URLを取得
            url = ''
            if title_elem.name == 'a':
                url = title_elem.get('href', '')
            else:
                link_elem = title_elem.find('a') or card.find('a')
                if link_elem:
                    url = link_elem.get('href', '')

            # 要約
            summary_elem = (card.find(class_='news-card__summary') or
                           card.find(class_='card-text'))
            summary = summary_elem.get_text(strip=True) if summary_elem else ''

            # ソース情報
            source = ''
            source_elem = card.find(class_='news-card__source')
            if source_elem:
                source = source_elem.get_text(strip=True)

            # 時間情報
            time_info = ''
            time_elem = (card.find(class_='news-card__time') or
                        card.find('small', class_='text-muted'))
            if time_elem:
                time_info = time_elem.get_text(strip=True)
            
            # カテゴリを推定（data-category属性またはタグから）
            category = 'AI News'  # デフォルト

            # data-category属性から取得
            if card.has_attr('data-category'):
                category = card['data-category']
            else:
                # タグリストから推定
                tags_elem = card.find(class_='news-card__taglist')
                if tags_elem:
                    tags_text = tags_elem.get_text(strip=True).lower()
                    if 'ビジネス' in tags_text or 'business' in tags_text:
                        category = 'ビジネス'
                    elif 'ツール' in tags_text or 'tool' in tags_text:
                        category = 'ツール'
                    elif 'sns' in tags_text or '論文' in tags_text:
                        category = 'SNS/論文'
            
            # 投稿日時を推定
            estimated_date = parse_time_info(time_info)
            
            # スコア計算（タイトル長、要約長、ソースの有無に基づく）
            score = min(100, max(20, 
                len(title) // 2 + 
                len(summary) // 10 + 
                (20 if url.startswith('http') else 0) +
                (10 if source else 0)
            ))
            
            news_item = {
                'title': title,
                'url': url,
                'summary': summary,
                'source': source,
                'category': category,
                'time_info': time_info,
                'estimated_date': estimated_date.strftime('%Y-%m-%d'),
                'estimated_datetime': estimated_date.isoformat(),
                'score': score,
                'rank': len(news_items) + 1  # 順次ランク付け
            }
            
            news_items.append(news_item)
            print(f"Extracted: {title[:50]}...")
            
        except Exception as e:
            print(f"Error parsing card {i}: {e}")
            continue
    
    return news_items

def group_news_by_date(news_items):
    """ニュース項目を日付でグループ化"""
    date_groups = {}
    
    for item in news_items:
        date = item['estimated_date']
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(item)
    
    # 各日付内でスコア順にソート
    for date in date_groups:
        date_groups[date].sort(key=lambda x: x['score'], reverse=True)
        # ランクを再設定
        for i, item in enumerate(date_groups[date]):
            item['rank'] = i + 1
    
    return date_groups

def create_archive_format(date, items):
    """アーカイブ形式のJSONデータを作成"""
    # 代表的なニュース項目を選択（最高スコア）
    top_item = max(items, key=lambda x: x['score']) if items else None
    
    if not top_item:
        return None
    
    # ポイント形式に変換
    points = []
    for item in items[:5]:  # 上位5件
        point = f"[{item['category']}] {item['title']}"
        if item['source']:
            point += f" (出典: {item['source']})"
        points.append(point)
    
    # リンク形式に変換
    links = []
    for item in items[:10]:  # 上位10件
        if item['url']:
            links.append({
                "href": item['url'],
                "text": f"{item['title']} - {item['category']}"
            })
    
    # メインアイテムを作成
    main_item = {
        "title": f"AI News Digest {date}",
        "score": top_item['score'],
        "rank": 1,
        "url": top_item['url'],
        "date": date,
        "summary": f"本日の主要AI関連ニュース{len(items)}件を収集。{top_item['title']}をはじめ、{', '.join([item['category'] for item in items[:3]])}分野での動きが活発。",
        "points": points,
        "links": links,
        "category_breakdown": {
            "business": len([i for i in items if i['category'] == 'ビジネス']),
            "tools": len([i for i in items if i['category'] == 'ツール']),
            "posts": len([i for i in items if i['category'] == 'SNS/論文'])
        },
        "source_items": items  # 元データも保持
    }
    
    return {
        "date": date,
        "source": "https://awano27.github.io/daily-ai-news-pages/",
        "count": len(items),
        "items": [main_item]
    }

def sync_with_existing_archive():
    """既存のアーカイブと同期"""
    print("Fetching latest news from daily-ai-news-pages...")
    
    # データを取得
    html_content = fetch_daily_ai_news()
    if not html_content:
        print("Failed to fetch news data")
        return False
    
    # ニュース項目を抽出
    news_items = extract_news_items(html_content)
    if not news_items:
        print("No news items found")
        return False
    
    print(f"Extracted {len(news_items)} news items")
    
    # 日付でグループ化
    date_groups = group_news_by_date(news_items)
    print(f"Grouped into {len(date_groups)} dates")
    
    # アーカイブディレクトリの準備
    output_dir = Path("public-pages/news")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 既存のインデックスを読み込み
    index_file = output_dir / "archive_index.json"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            existing_index = json.load(f)
    else:
        existing_index = []
    
    existing_dates = {item['date'] for item in existing_index}
    new_entries = []
    updated_count = 0
    
    # 各日付のデータを処理
    for date, items in date_groups.items():
        json_file = output_dir / f"{date}.json"
        
        # 今日のデータまたは新しいデータのみ更新
        today = datetime.now().strftime('%Y-%m-%d')
        should_update = (date == today) or (date not in existing_dates)
        
        if not should_update:
            continue
        
        # アーカイブ形式のデータを作成
        archive_data = create_archive_format(date, items)
        if not archive_data:
            continue
        
        # JSONファイルに保存
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=2)
        
        # インデックスエントリ
        index_entry = {
            "date": date,
            "file": f"{date}.json",
            "count": len(items)
        }
        
        if date in existing_dates:
            # 既存エントリを更新
            for i, item in enumerate(existing_index):
                if item['date'] == date:
                    existing_index[i] = index_entry
                    break
        else:
            new_entries.append(index_entry)
        
        updated_count += 1
        print(f"Updated: {date} ({len(items)} items)")
    
    # インデックスを更新
    all_entries = existing_index + new_entries
    all_entries.sort(key=lambda x: x['date'], reverse=True)
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    # バージョンファイルを更新
    version_file = output_dir / "version.json"
    version_data = {
        "version": datetime.now().isoformat(),
        "sha": hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8],
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": len(all_entries),
        "source": "daily-ai-news-pages",
        "sync_time": datetime.now().isoformat()
    }
    
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nSync completed:")
    print(f"- Updated entries: {updated_count}")
    print(f"- Total entries: {len(all_entries)}")
    print(f"- Latest date: {all_entries[0]['date'] if all_entries else 'None'}")
    print(f"- Source: daily-ai-news-pages")
    
    return updated_count > 0

if __name__ == "__main__":
    success = sync_with_existing_archive()
    if success:
        print("\nDaily AI News sync completed successfully!")
    else:
        print("\nNo updates needed.")