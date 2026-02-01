#!/usr/bin/env python3
"""
Test script for RSS collector.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.collectors.rss import RSSCollector
from datetime import date
import json

def main():
    print("Testing RSS Collector...")
    collector = RSSCollector()
    
    # Collect today's news
    items = collector.collect(date.today())
    
    print(f"\n✅ Collected {len(items)} items from RSS feeds\n")
    
    # Group by source
    by_source = {}
    for item in items:
        source = item.get("rss_source", "unknown")
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(item)
    
    # Print summary
    print("📊 By source:")
    for source, source_items in sorted(by_source.items()):
        print(f"  - {source}: {len(source_items)} items")
    
    print("\n📰 Latest headlines:")
    for item in items[:10]:
        source = item.get("rss_source", "?")
        name = item.get("name", "?")[:60]
        pub = item.get("published_at", "?")[:10] if item.get("published_at") else "?"
        print(f"  [{source}] {name}... ({pub})")
    
    # Save sample output
    sample_file = Path(__file__).parent.parent / "data" / "rss_sample.json"
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump({
            "collected_at": date.today().isoformat(),
            "count": len(items),
            "items": items[:20]  # Save first 20
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Sample saved to {sample_file}")

if __name__ == "__main__":
    main()
