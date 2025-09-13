#!/usr/bin/env python3
"""
News Archive Updater
inputディレクトリから最新ニュースデータを読み込んでアーカイブを更新
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
import hashlib

def parse_date_from_filename(filename):
    """ファイル名から日付を解析 (例: 0913.txt -> 2025-09-13)"""
    match = re.match(r'(\d{2})(\d{2})\.txt', filename)
    if match:
        month, day = match.groups()
        # 2025年を仮定
        return f"2025-{month}-{day}"
    return None

def extract_news_content(text):
    """テキストからニュース内容を抽出"""
    lines = text.strip().split('\n')
    if not lines:
        return None
        
    # 最初の行をタイトルとして使用
    title = lines[0].strip()
    
    # 内容を要約として結合
    content_lines = [line.strip() for line in lines[1:] if line.strip()]
    summary = ' '.join(content_lines[:10])  # 最初の10行を要約として使用
    
    # URLを抽出
    urls = []
    url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    for line in lines:
        urls.extend(url_pattern.findall(line))
    
    # 主要ポイントを抽出 (箇条書きや番号付きリスト)
    points = []
    for line in content_lines:
        if (line.startswith('・') or line.startswith('-') or 
            line.startswith('1.') or line.startswith('2.') or 
            line.startswith('•')):
            points.append(line.strip())
    
    # 品質スコアを計算 (文字数、URL数、ポイント数に基づく)
    score = min(100, max(10, len(title) + len(summary)//10 + len(urls)*10 + len(points)*5))
    
    return {
        "title": title,
        "score": score,
        "rank": 1,  # 単一ニュースの場合は1
        "url": urls[0] if urls else "",
        "summary": summary[:500] + "..." if len(summary) > 500 else summary,
        "points": points[:5],  # 最大5ポイント
        "links": [{"href": url, "text": ""} for url in urls[:10]]  # 最大10リンク
    }

def update_archive():
    """アーカイブデータを更新"""
    input_dir = Path("input/day")
    output_dir = Path("public-pages/news")
    
    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 既存のアーカイブインデックスを読み込み
    index_file = output_dir / "archive_index.json"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            existing_index = json.load(f)
    else:
        existing_index = []
    
    # 既存の日付を取得
    existing_dates = {item['date'] for item in existing_index}
    
    # 新しいエントリを処理
    new_entries = []
    updated_count = 0
    
    for txt_file in input_dir.glob("*.txt"):
        file_date = parse_date_from_filename(txt_file.name)
        if not file_date:
            continue
            
        # 既存のデータをチェック
        json_file = output_dir / f"{file_date}.json"
        
        # ファイルの更新時間をチェック
        should_update = True
        if json_file.exists() and file_date in existing_dates:
            # テキストファイルがJSONファイルより新しい場合のみ更新
            txt_mtime = txt_file.stat().st_mtime
            json_mtime = json_file.stat().st_mtime
            should_update = txt_mtime > json_mtime
        
        if not should_update:
            continue
            
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            news_item = extract_news_content(content)
            if not news_item:
                continue
                
            # 日付を追加
            news_item["date"] = file_date
            
            # JSONデータを作成
            archive_data = {
                "date": file_date,
                "source": str(txt_file.absolute()),
                "count": 1,
                "items": [news_item]
            }
            
            # JSONファイルに保存
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2)
            
            # インデックスエントリを準備
            index_entry = {
                "date": file_date,
                "file": f"{file_date}.json",
                "count": 1
            }
            
            # 既存エントリを更新または新規追加
            if file_date in existing_dates:
                for i, item in enumerate(existing_index):
                    if item['date'] == file_date:
                        existing_index[i] = index_entry
                        break
            else:
                new_entries.append(index_entry)
            
            updated_count += 1
            print(f"Updated: {file_date} ({txt_file.name})")
            
        except Exception as e:
            print(f"Error processing {txt_file.name}: {e}")
            continue
    
    # 新しいエントリを追加してソート
    all_entries = existing_index + new_entries
    all_entries.sort(key=lambda x: x['date'], reverse=True)  # 新しい順
    
    # インデックスファイルを更新
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    # バージョンファイルを更新
    version_file = output_dir / "version.json"
    version_data = {
        "version": datetime.now().isoformat(),
        "sha": hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8],
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": len(all_entries)
    }
    
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nUpdate completed:")
    print(f"- Processed files: {updated_count}")
    print(f"- Total entries: {len(all_entries)}")
    print(f"- Latest date: {all_entries[0]['date'] if all_entries else 'None'}")
    
    return updated_count > 0

if __name__ == "__main__":
    success = update_archive()
    if success:
        print("\nArchive updated successfully!")
    else:
        print("\nNo data to update.")