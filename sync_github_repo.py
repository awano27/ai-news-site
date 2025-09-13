#!/usr/bin/env python3
"""
GitHub Repository News Sync
awano27/daily-ai-newsリポジトリから最新ニュースデータを取得してアーカイブに統合
"""

import requests
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import time

# GitHub API設定
GITHUB_REPO = "awano27/daily-ai-news"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

def fetch_github_file_list():
    """GitHubリポジトリのファイル一覧を取得"""
    try:
        url = f"{GITHUB_API_BASE}/contents"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching file list: {e}")
        return []

def fetch_json_file(filename):
    """指定されたJSONファイルを取得"""
    try:
        url = f"{RAW_BASE}/{filename}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {filename}: {e}")
        return None

def parse_timestamp_from_filename(filename):
    """ファイル名からタイムスタンプを解析"""
    # comprehensive_analysis_20250818_101345.json のような形式
    match = re.search(r'(\d{8})_(\d{6})', filename)
    if match:
        date_str, time_str = match.groups()
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt
        except ValueError:
            pass
    
    # daily_report_20250819.html のような形式
    match = re.search(r'(\d{8})', filename)
    if match:
        date_str = match.group(1)
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            return dt
        except ValueError:
            pass
    
    return None

def extract_news_from_dashboard_data(data):
    """dashboard_data.jsonからニュース項目を抽出（改良版）"""
    news_items = []
    
    if not isinstance(data, dict):
        print("  Dashboard data is not a dict")
        return news_items
    
    print(f"  Dashboard data keys: {list(data.keys())[:10]}")  # デバッグ
    
    # 全ての構造を再帰的に探索
    def find_news_items(obj, path="", level=0):
        if level > 5:  # 深すぎる場合は停止
            return []
        
        items = []
        if isinstance(obj, dict):
            # featured_topics, items, news などのキーを探す
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                if key in ['featured_topics', 'items', 'news', 'articles', 'posts']:
                    if isinstance(value, list):
                        print(f"    Found {len(value)} items in {current_path}")
                        for item in value:
                            if isinstance(item, dict):
                                items.append((item, current_path))
                
                # 再帰的に探索
                items.extend(find_news_items(value, current_path, level + 1))
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                items.extend(find_news_items(item, f"{path}[{i}]", level + 1))
        
        return items
    
    # ニュース項目を探索
    found_items = find_news_items(data)
    print(f"  Found {len(found_items)} potential news items")
    
    for item_data, path in found_items:
        try:
            # タイトルを抽出（複数の可能性を試す）
            title = None
            for title_key in ['title', 'headline', 'name', 'summary']:
                if title_key in item_data:
                    title_val = item_data[title_key]
                    if isinstance(title_val, dict):
                        title = title_val.get('japanese', title_val.get('english', title_val.get('text', '')))
                    else:
                        title = str(title_val)
                    if title:
                        break
            
            if not title or len(title) < 10:
                continue
                
            # URLを抽出
            url = item_data.get('url', item_data.get('link', item_data.get('href', '')))
            
            # 要約を抽出
            summary = item_data.get('summary', item_data.get('description', item_data.get('content', '')))
            if isinstance(summary, dict):
                summary = summary.get('text', summary.get('japanese', summary.get('english', '')))
            
            # カテゴリを推定
            category = 'AI Technology'
            if 'business' in path.lower() or any(word in str(item_data).lower() for word in ['投資', '資金調達', 'investment', 'funding']):
                category = 'ビジネス・投資'
            elif 'tech' in path.lower() or any(word in str(item_data).lower() for word in ['ツール', 'tool', 'technology']):
                category = 'テクノロジー・ツール'
            elif 'social' in path.lower() or any(word in str(item_data).lower() for word in ['SNS', 'twitter', 'x.com']):
                category = 'SNS・論文'
            
            news_item = {
                'title': title,
                'url': url,
                'summary': str(summary)[:500] if summary else '',
                'source': item_data.get('source', 'GitHub Repository'),
                'category': category,
                'importance_score': item_data.get('importance_score', item_data.get('score', 50)),
                'time': item_data.get('time', item_data.get('timestamp', '')),
                'gemini_selected': item_data.get('gemini_selected', False),
                'extracted_from': f'dashboard_data.json:{path}'
            }
            
            news_items.append(news_item)
            print(f"    Extracted: {title[:50]}...")
            
        except Exception as e:
            print(f"    Error processing item from {path}: {e}")
            continue
    
    return news_items

def extract_news_from_comprehensive_analysis(data):
    """comprehensive_analysis.jsonからニュース項目を抽出（改良版）"""
    news_items = []
    
    if not isinstance(data, dict):
        print("  Comprehensive analysis data is not a dict")
        return news_items
    
    print(f"  Comprehensive analysis keys: {list(data.keys())[:10]}")  # デバッグ
    
    # 全ての構造を再帰的に探索
    def find_analysis_items(obj, path="", level=0):
        if level > 6:  # 深すぎる場合は停止
            return []
        
        items = []
        if isinstance(obj, dict):
            # URLが含まれているオブジェクトを探す
            if 'url' in obj and obj['url']:
                items.append((obj, path))
            
            # 一般的なニュース項目のキーを探す
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                if key in ['items', 'news', 'articles', 'breaking_news', 'research_labs']:
                    if isinstance(value, list):
                        print(f"    Found {len(value)} items in {current_path}")
                        for item in value:
                            if isinstance(item, dict):
                                items.append((item, current_path))
                    elif isinstance(value, dict):
                        items.append((value, current_path))
                
                # 再帰的に探索
                items.extend(find_analysis_items(value, current_path, level + 1))
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                items.extend(find_analysis_items(item, f"{path}[{i}]", level + 1))
        
        return items
    
    # ニュース項目を探索
    found_items = find_analysis_items(data)
    print(f"  Found {len(found_items)} potential analysis items")
    
    for item_data, path in found_items:
        try:
            # AI分析情報を取得
            ai_analysis = item_data.get('ai_analysis', item_data.get('analysis', {}))
            summary_data = ai_analysis.get('summary', {}) if ai_analysis else {}
            
            # タイトルを抽出（複数のソースから）
            title = None
            title_sources = [
                summary_data.get('title'),
                item_data.get('title'),
                item_data.get('headline'),
                ai_analysis.get('title') if ai_analysis else None,
                item_data.get('url', '')[:100] if item_data.get('url') else None
            ]
            
            for title_candidate in title_sources:
                if title_candidate and len(str(title_candidate).strip()) > 10:
                    title = str(title_candidate).strip()
                    break
            
            if not title:
                continue
                
            # URLを取得
            url = item_data.get('url', '')
            if not url:
                continue  # URLがない場合はスキップ
                
            # 要約を構築
            summary_text = ''
            if summary_data.get('text'):
                summary_text = summary_data['text']
            elif summary_data.get('key_points'):
                key_points = summary_data['key_points']
                if isinstance(key_points, list):
                    summary_text = ' '.join(key_points[:3])
                else:
                    summary_text = str(key_points)
            elif item_data.get('summary'):
                summary_text = item_data['summary']
            elif item_data.get('description'):
                summary_text = item_data['description']
            
            # カテゴリを判定
            category = summary_data.get('category', 'AI Technology')
            if not category or category == 'AI Technology':
                # pathからカテゴリを推定
                if 'business' in path.lower():
                    category = 'ビジネス・投資'
                elif 'research' in path.lower():
                    category = 'SNS・論文'
                elif 'breaking' in path.lower():
                    category = 'テクノロジー・ツール'
            
            # スコアを取得
            score = (ai_analysis.get('overall_score') or 
                    item_data.get('importance_score') or 
                    item_data.get('score') or 
                    50)
            
            news_item = {
                'title': title,
                'url': url,
                'summary': str(summary_text)[:500] if summary_text else '',
                'source': item_data.get('source', 'AI Analysis'),
                'category': category,
                'importance_score': score,
                'timestamp': item_data.get('timestamp', ''),
                'confidence': summary_data.get('confidence', 1.0),
                'language': summary_data.get('language', 'japanese'),
                'extracted_from': f'comprehensive_analysis.json:{path}'
            }
            
            news_items.append(news_item)
            print(f"    Extracted: {title[:50]}...")
            
        except Exception as e:
            print(f"    Error processing analysis item from {path}: {e}")
            continue
    
    return news_items

def consolidate_and_score_news(all_news_items):
    """ニュース項目を統合し、重複を除去してスコアを計算"""
    seen_urls = set()
    seen_titles = set()
    consolidated_items = []
    
    for item in all_news_items:
        # 重複チェック
        url = item.get('url', '')
        title = item.get('title', '')
        
        # URLまたはタイトルで重複チェック
        title_key = title.lower().strip()
        if url and url in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
            
        # スコアを正規化
        raw_score = item.get('importance_score', 50)
        confidence = item.get('confidence', 1.0)
        
        # 統合スコア計算
        final_score = min(100, max(10, 
            raw_score * confidence +
            (20 if url.startswith('http') else 0) +
            (10 if len(title) > 20 else 0) +
            (15 if item.get('gemini_selected') else 0)
        ))
        
        item['score'] = int(final_score)
        item['rank'] = len(consolidated_items) + 1
        
        consolidated_items.append(item)
        
        if url:
            seen_urls.add(url)
        if title_key:
            seen_titles.add(title_key)
    
    # スコア順にソート
    consolidated_items.sort(key=lambda x: x['score'], reverse=True)
    
    # ランクを再設定
    for i, item in enumerate(consolidated_items):
        item['rank'] = i + 1
    
    return consolidated_items

def create_archive_entry(date, news_items, source_files):
    """アーカイブエントリを作成"""
    if not news_items:
        return None
    
    # トップニュースを選択
    top_news = news_items[0]
    
    # ポイントを作成
    points = []
    for item in news_items[:8]:  # 上位8件
        point = f"[{item['category']}] {item['title']}"
        if item.get('source'):
            point += f" (出典: {item['source']})"
        points.append(point)
    
    # リンクを作成
    links = []
    for item in news_items[:12]:  # 上位12件
        if item.get('url'):
            links.append({
                "href": item['url'],
                "text": f"{item['title'][:50]}..." if len(item['title']) > 50 else item['title']
            })
    
    # メインアイテムを作成
    main_item = {
        "title": f"AI News Digest {date} (GitHub統合版)",
        "score": top_news['score'],
        "rank": 1,
        "url": top_news.get('url', ''),
        "date": date,
        "summary": f"GitHub daily-ai-newsから{len(news_items)}件のニュースを統合。{top_news['title']}がトップスコア({top_news['score']})。カテゴリ別では{', '.join(set([item['category'] for item in news_items[:5]]))}分野での動きが活発。",
        "points": points,
        "links": links,
        "github_integration": {
            "source_repository": GITHUB_REPO,
            "source_files": source_files,
            "total_items": len(news_items),
            "avg_score": sum(item['score'] for item in news_items) / len(news_items),
            "categories": list(set([item['category'] for item in news_items])),
            "sync_timestamp": datetime.now().isoformat()
        },
        "category_breakdown": {}
    }
    
    # カテゴリ別の統計を追加
    for category in set([item['category'] for item in news_items]):
        category_items = [item for item in news_items if item['category'] == category]
        main_item["category_breakdown"][category] = {
            "count": len(category_items),
            "avg_score": sum(item['score'] for item in category_items) / len(category_items),
            "top_score": max(item['score'] for item in category_items)
        }
    
    return {
        "date": date,
        "source": f"GitHub: {GITHUB_REPO}",
        "count": len(news_items),
        "items": [main_item],
        "raw_github_data": news_items  # デバッグ用
    }

def sync_github_data():
    """GitHubリポジトリからデータを同期"""
    print(f"Syncing data from GitHub repository: {GITHUB_REPO}")
    
    # ファイル一覧を取得
    files = fetch_github_file_list()
    if not files:
        print("Failed to fetch file list")
        return False
    
    # 関連ファイルを特定
    json_files = []
    for file_info in files:
        if file_info['name'].endswith('.json') and file_info['size'] > 1000:  # 1KB以上のJSONファイル
            json_files.append(file_info['name'])
    
    print(f"Found {len(json_files)} JSON files: {', '.join(json_files)}")
    
    # データを取得・統合
    all_news_items = []
    processed_files = []
    
    for filename in json_files:
        print(f"Processing {filename}...")
        
        data = fetch_json_file(filename)
        if not data:
            continue
            
        # ファイル種類に応じてデータを抽出
        news_items = []
        if 'dashboard_data' in filename:
            news_items = extract_news_from_dashboard_data(data)
        elif 'comprehensive_analysis' in filename:
            news_items = extract_news_from_comprehensive_analysis(data)
        elif 'analysis_summary' in filename:
            # 小さなサマリーファイルは今回はスキップ
            continue
        
        if news_items:
            all_news_items.extend(news_items)
            processed_files.append(filename)
            print(f"  Extracted {len(news_items)} items from {filename}")
    
    if not all_news_items:
        print("No news items found in GitHub repository")
        return False
    
    # ニュースを統合・重複除去
    consolidated_items = consolidate_and_score_news(all_news_items)
    print(f"Consolidated to {len(consolidated_items)} unique items")
    
    # 今日の日付でアーカイブエントリを作成
    today = datetime.now().strftime('%Y-%m-%d')
    archive_entry = create_archive_entry(today, consolidated_items, processed_files)
    
    if not archive_entry:
        print("Failed to create archive entry")
        return False
    
    # アーカイブディレクトリに保存
    output_dir = Path("public-pages/news")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # GitHub統合版として保存（既存ファイルとは別名）
    github_file = output_dir / f"{today}_github.json"
    with open(github_file, 'w', encoding='utf-8') as f:
        json.dump(archive_entry, f, ensure_ascii=False, indent=2)
    
    # インデックスを更新
    index_file = output_dir / "archive_index.json"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            existing_index = json.load(f)
    else:
        existing_index = []
    
    # GitHub統合エントリを追加
    github_entry = {
        "date": f"{today} (GitHub)",
        "file": f"{today}_github.json",
        "count": len(consolidated_items),
        "source": "GitHub Repository",
        "repository": GITHUB_REPO
    }
    
    # 既存のGitHub エントリを削除して新しいものを追加
    existing_index = [item for item in existing_index if not item.get('source') == 'GitHub Repository']
    existing_index.insert(0, github_entry)  # 最上位に追加
    
    # インデックスをソート（GitHub エントリを最上位に保つ）
    github_entries = [item for item in existing_index if item.get('source') == 'GitHub Repository']
    other_entries = [item for item in existing_index if not item.get('source') == 'GitHub Repository']
    other_entries.sort(key=lambda x: x['date'], reverse=True)
    
    final_index = github_entries + other_entries
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(final_index, f, ensure_ascii=False, indent=2)
    
    # バージョンファイルを更新
    version_file = output_dir / "version.json"
    version_data = {
        "version": datetime.now().isoformat(),
        "sha": hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8],
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": len(final_index),
        "github_integration": {
            "repository": GITHUB_REPO,
            "last_sync": datetime.now().isoformat(),
            "files_processed": processed_files,
            "items_synced": len(consolidated_items)
        }
    }
    
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nGitHub sync completed:")
    print(f"- Repository: {GITHUB_REPO}")
    print(f"- Files processed: {len(processed_files)}")
    print(f"- News items synced: {len(consolidated_items)}")
    print(f"- Archive file: {github_file}")
    print(f"- Total index entries: {len(final_index)}")
    
    return True

if __name__ == "__main__":
    success = sync_github_data()
    if success:
        print("\nGitHub repository sync completed successfully!")
    else:
        print("\nGitHub repository sync failed.")