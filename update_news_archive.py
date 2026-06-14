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

from src.utils import (
    mmdd_to_iso, filename_to_iso,
    INPUT_DAY_DIR, PUBLIC_NEWS_DIR, ARCHIVE_INDEX_FILE, VERSION_FILE,
    read_text, write_json,
)


def parse_date_from_filename(filename):
    """ファイル名から日付を解析 (例: 0913.txt -> 2026-09-13)

    Thin wrapper around src.utils.mmdd_to_iso / filename_to_iso so that
    other modules that import this symbol continue to work unchanged.
    """
    return filename_to_iso(filename)

def extract_news_content(text):
    """テキストからニュース内容を抽出（改良版）"""
    lines = text.strip().split('\n')
    if not lines:
        return None
        
    # 最初の行をタイトルとして使用
    title = lines[0].strip()
    
    # セクション分けを試行
    content_lines = [line.strip() for line in lines[1:] if line.strip()]
    
    # URLを抽出
    urls = []
    url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    for line in lines:
        urls.extend(url_pattern.findall(line))
    
    # 主要ポイントを抽出（より詳細な分析）
    points = []
    summary_parts = []
    
    for line in content_lines:
        # 箇条書きや重要なポイント
        if (line.startswith('・') or line.startswith('-') or 
            line.startswith('•') or line.startswith('★') or
            re.match(r'^\d+\.', line) or line.startswith('■')):
            points.append(line.strip())
        # キーワードを含む重要な行
        elif any(keyword in line for keyword in ['発表', '発表', '革命', 'リリース', 'ブレークスルー', '画期的', '革新', '新機能']):
            points.append(line.strip())
        else:
            summary_parts.append(line)
    
    # 要約を作成（キーワード優先）
    summary = ' '.join(summary_parts[:8])  # 最初の8行を要約として使用
    
    # 技術的キーワードに基づくカテゴリ分類
    category = "AI Technology"
    tech_keywords = {
        "AI Model": ["GPT", "LLM", "Transformer", "Neural", "Model", "モデル"],
        "Business": ["資金調達", "投資", "IPO", "買収", "ビジネス", "企業"],
        "Research": ["論文", "研究", "実験", "テスト", "分析", "study"],
        "Product": ["リリース", "発表", "ローンチ", "製品", "サービス", "App"],
        "Hardware": ["チップ", "GPU", "CPU", "ハードウェア", "デバイス"]
    }
    
    text_lower = text.lower()
    for cat, keywords in tech_keywords.items():
        if any(kw.lower() in text_lower for kw in keywords):
            category = cat
            break
    
    # より洗練されたスコア計算
    base_score = min(100, max(20, 
        len(title) // 2 + 
        len(summary) // 15 + 
        len(urls) * 8 + 
        len(points) * 6 +
        (15 if any(kw in text_lower for kw in ['突破', 'breakthrough', '革命', 'revolution', '画期的']) else 0)
    ))
    
    return {
        "title": title,
        "score": base_score,
        "rank": 1,
        "url": urls[0] if urls else "",
        "summary": summary[:600] + "..." if len(summary) > 600 else summary,
        "points": points[:8],  # 最大8ポイント
        "links": [{"href": url, "text": f"関連リンク {i+1}"} for i, url in enumerate(urls[:12])],
        "category": category,
        "extracted_urls_count": len(urls),
        "content_sections": len([line for line in content_lines if line])
    }

def update_archive():
    """アーカイブデータを更新"""
    input_dir = INPUT_DAY_DIR
    output_dir = PUBLIC_NEWS_DIR

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # 既存のアーカイブインデックスを読み込み
    index_file = ARCHIVE_INDEX_FILE
    if index_file.exists():
        existing_index = json.loads(read_text(index_file))
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

        # ファイルの更新時間をチェック（今日のデータは強制更新）
        today = datetime.now().strftime('%Y-%m-%d')
        should_update = True
        if json_file.exists() and file_date in existing_dates and file_date != today:
            # テキストファイルがJSONファイルより新しい場合のみ更新（今日以外）
            txt_mtime = txt_file.stat().st_mtime
            json_mtime = json_file.stat().st_mtime
            should_update = txt_mtime > json_mtime

        if not should_update:
            continue

        try:
            content = read_text(txt_file)

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
            write_json(json_file, archive_data)

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
    write_json(index_file, all_entries)

    # バージョンファイルを更新
    version_data = {
        "version": datetime.now().isoformat(),
        "sha": hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8],
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": len(all_entries)
    }
    write_json(VERSION_FILE, version_data)

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
