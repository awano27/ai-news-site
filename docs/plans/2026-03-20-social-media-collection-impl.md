# Social Media Collection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automate social media collection via IFTTT (X, $3.49/mo) + Bluesky (free API) + Reddit (existing RSS), integrated into the daily-ai-news build pipeline.

**Architecture:** New `bluesky_collector.py` fetches posts from Bluesky public API, outputs CSV in the same format as the existing X posts. `build.py` reads Bluesky CSV alongside the existing Google Sheets CSV. GitHub Actions runs the collector before each build.

**Tech Stack:** Python 3.11, atproto (Bluesky SDK), existing build.py/feedparser pipeline

---

### Task 1: Add atproto to requirements.txt

**Files:**
- Modify: `C:\develop\daily-ai-news\requirements.txt`

**Step 1: Add dependency**

Add to the end of `requirements.txt`:
```
atproto>=0.0.46
```

**Step 2: Install locally**

Run: `pip install atproto>=0.0.46`
Expected: Successfully installed atproto

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add atproto for Bluesky API integration"
```

---

### Task 2: Create bluesky_collector.py

**Files:**
- Create: `C:\develop\daily-ai-news\bluesky_collector.py`

**Step 1: Write the collector**

```python
#!/usr/bin/env python3
"""Collect posts from Bluesky public API and output as CSV.

Usage:
    python bluesky_collector.py

Environment variables:
    BLUESKY_ACCOUNTS  - Comma-separated list of Bluesky handles (e.g. "ylecun.bsky.social,karpathy.bsky.social")
    BLUESKY_KEYWORDS  - Comma-separated search keywords (e.g. "AI,LLM,GPT")
    BLUESKY_OUTPUT    - Output CSV path (default: _sources/bluesky_posts.csv)
    BLUESKY_HOURS     - How far back to look in hours (default: 36)
"""

import csv
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from atproto import Client
except ImportError:
    print("[WARN] atproto not installed. Run: pip install atproto>=0.0.46")
    sys.exit(0)

# --- Config ---
ACCOUNTS = [a.strip() for a in os.getenv("BLUESKY_ACCOUNTS", "").split(",") if a.strip()]
KEYWORDS = [k.strip() for k in os.getenv("BLUESKY_KEYWORDS", "AI,LLM,GPT,Claude,Gemini").split(",") if k.strip()]
OUTPUT_PATH = os.getenv("BLUESKY_OUTPUT", "_sources/bluesky_posts.csv")
HOURS_BACK = int(os.getenv("BLUESKY_HOURS", "36"))

# Default accounts if none specified
DEFAULT_ACCOUNTS = [
    "ylecun.bsky.social",
    "karpathy.bsky.social",
    "emollick.bsky.social",
    "simonw.bsky.social",
    "benparr.bsky.social",
]

JST = timezone(timedelta(hours=9))
CUTOFF = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)


def parse_bsky_time(ts: str) -> datetime:
    """Parse Bluesky timestamp to datetime."""
    try:
        # Bluesky uses ISO 8601 format
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.now(timezone.utc)


def collect_from_accounts(client: Client, accounts: list[str]) -> list[dict]:
    """Fetch recent posts from specified accounts."""
    posts = []
    for handle in accounts:
        try:
            response = client.app.bsky.feed.get_author_feed(
                {"actor": handle, "limit": 10}
            )
            for item in response.feed:
                post = item.post
                created = parse_bsky_time(post.record.created_at)
                if created < CUTOFF:
                    continue
                text = post.record.text or ""
                if len(text) < 20:
                    continue
                uri = post.uri  # at://did:plc:.../app.bsky.feed.post/...
                rkey = uri.split("/")[-1]
                did = post.author.did
                web_url = f"https://bsky.app/profile/{post.author.handle}/post/{rkey}"
                posts.append({
                    "date": created.astimezone(JST).strftime("%Y-%m-%d %H:%M"),
                    "user": f"@{post.author.handle}",
                    "text": text.replace("\n", " ").strip(),
                    "image": "",
                    "url": web_url,
                    "source": "Bluesky",
                })
            print(f"[OK] {handle}: {len([p for p in posts if handle in p.get('user','')])} posts")
        except Exception as e:
            print(f"[WARN] Failed to fetch {handle}: {e}")
    return posts


def collect_from_search(client: Client, keywords: list[str]) -> list[dict]:
    """Search Bluesky for keyword matches."""
    posts = []
    seen_urls = set()
    for kw in keywords:
        try:
            response = client.app.bsky.feed.search_posts(
                {"q": kw, "limit": 15}
            )
            for post_view in response.posts:
                created = parse_bsky_time(post_view.record.created_at)
                if created < CUTOFF:
                    continue
                text = post_view.record.text or ""
                if len(text) < 30:
                    continue
                rkey = post_view.uri.split("/")[-1]
                web_url = f"https://bsky.app/profile/{post_view.author.handle}/post/{rkey}"
                if web_url in seen_urls:
                    continue
                seen_urls.add(web_url)
                posts.append({
                    "date": created.astimezone(JST).strftime("%Y-%m-%d %H:%M"),
                    "user": f"@{post_view.author.handle}",
                    "text": text.replace("\n", " ").strip(),
                    "image": "",
                    "url": web_url,
                    "source": "Bluesky",
                })
            print(f"[OK] Search '{kw}': {len(response.posts)} results")
        except Exception as e:
            print(f"[WARN] Search '{kw}' failed: {e}")
    return posts


def deduplicate(posts: list[dict]) -> list[dict]:
    """Remove duplicates by URL."""
    seen = set()
    unique = []
    for p in posts:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique.append(p)
    return unique


def write_csv(posts: list[dict], path: str):
    """Write posts to CSV in the format expected by build.py gather_x_posts()."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header matching existing Google Sheets CSV format
        writer.writerow(["日付", "@ユーザー", "テキスト", "画像URL", "ツイートURL"])
        for p in posts:
            writer.writerow([p["date"], p["user"], p["text"], p["image"], p["url"]])
    print(f"[SUCCESS] Wrote {len(posts)} posts to {path}")


def main():
    print("=" * 50)
    print("Bluesky Collector")
    print("=" * 50)

    accounts = ACCOUNTS if ACCOUNTS else DEFAULT_ACCOUNTS
    print(f"Accounts: {len(accounts)}, Keywords: {len(KEYWORDS)}, Lookback: {HOURS_BACK}h")

    client = Client()
    # Public API - no login required for search and public feeds

    all_posts = []

    # 1. Collect from accounts
    print(f"\n--- Collecting from {len(accounts)} accounts ---")
    account_posts = collect_from_accounts(client, accounts)
    all_posts.extend(account_posts)
    print(f"Account posts: {len(account_posts)}")

    # 2. Collect from keyword search
    print(f"\n--- Searching {len(KEYWORDS)} keywords ---")
    search_posts = collect_from_search(client, KEYWORDS)
    all_posts.extend(search_posts)
    print(f"Search posts: {len(search_posts)}")

    # 3. Deduplicate and write
    unique = deduplicate(all_posts)
    print(f"\nTotal unique posts: {len(unique)}")

    write_csv(unique, OUTPUT_PATH)
    print("Done.")


if __name__ == "__main__":
    main()
```

**Step 2: Test locally**

Run: `cd C:\develop\daily-ai-news && python bluesky_collector.py`
Expected: CSV written to `_sources/bluesky_posts.csv` with posts

**Step 3: Verify CSV format**

Run: `head -3 _sources/bluesky_posts.csv`
Expected: Header `日付,@ユーザー,テキスト,画像URL,ツイートURL` followed by data rows

**Step 4: Commit**

```bash
git add bluesky_collector.py
git commit -m "feat: add Bluesky collector for automated post gathering"
```

---

### Task 3: Modify build.py to read Bluesky CSV

**Files:**
- Modify: `C:\develop\daily-ai-news\build.py:1812-1830` (X posts injection section)

**Step 1: Add Bluesky CSV config**

After line 159 (`X_POSTS_CSV = CONFIG['x_posts_csv']`), add:
```python
BLUESKY_CSV = os.getenv("BLUESKY_OUTPUT", "_sources/bluesky_posts.csv")
```

**Step 2: Add Bluesky posts injection after X posts**

After the X posts block (line ~1830, after `except Exception as e: print(f"[WARN] Failed to process X posts: {e}")`), add:

```python
    # Inject Bluesky posts
    if Path(BLUESKY_CSV).exists():
        try:
            bsky_posts = gather_x_posts(BLUESKY_CSV)
            if bsky_posts:
                print(f"[INFO] Adding {len(bsky_posts)} Bluesky posts")
                for bp in bsky_posts:
                    bp['_source'] = 'Bluesky'
                    b_link = bp.get('link', '')
                    b_title = bp.get('title', '').lower().strip()
                    if b_link not in seen_links and b_title not in seen_titles:
                        posts.append(bp)
                        seen_links.add(b_link)
                        seen_titles.add(b_title)
                posts = sorted(posts, key=lambda x: x.get('_dt', NOW), reverse=True)
        except Exception as e:
            print(f"[WARN] Failed to process Bluesky posts: {e}")
    else:
        print(f"[INFO] No Bluesky CSV found at {BLUESKY_CSV}, skipping")
```

**Step 3: Test build with Bluesky data**

Run: `cd C:\develop\daily-ai-news && PYTHONIOENCODING=utf-8 python build.py 2>&1 | grep -i bluesky`
Expected: `[INFO] Adding N Bluesky posts` or `[INFO] No Bluesky CSV found`

**Step 4: Commit**

```bash
git add build.py
git commit -m "feat: integrate Bluesky posts into build pipeline"
```

---

### Task 4: Update GitHub Actions workflow

**Files:**
- Modify: `C:\develop\daily-ai-news\.github\workflows\run-csv-deploy.yml`

**Step 1: Add Bluesky collection step**

Insert after the "Verify CSV accessibility" step (line ~71) and before the "Build AI News Site from CSV" step (line ~73):

```yaml
      - name: Collect Bluesky posts
        continue-on-error: true
        timeout-minutes: 3
        run: |
          echo "🦋 Collecting Bluesky posts..."
          python bluesky_collector.py || echo "⚠️ Bluesky collection failed, continuing with X + RSS only"
          if [ -f "_sources/bluesky_posts.csv" ]; then
            count=$(wc -l < _sources/bluesky_posts.csv)
            echo "✅ Bluesky: $((count - 1)) posts collected"
          fi
        env:
          BLUESKY_ACCOUNTS: "ylecun.bsky.social,karpathy.bsky.social,emollick.bsky.social,simonw.bsky.social,benparr.bsky.social"
          BLUESKY_KEYWORDS: "AI,LLM,GPT,Claude,Gemini,machine learning,neural network"
          BLUESKY_OUTPUT: "_sources/bluesky_posts.csv"
          BLUESKY_HOURS: "36"
```

**Step 2: Add BLUESKY_OUTPUT env to build step**

In the "Build AI News Site from CSV" step env section, add:
```yaml
          BLUESKY_OUTPUT: "_sources/bluesky_posts.csv"
```

**Step 3: Commit**

```bash
git add .github/workflows/run-csv-deploy.yml
git commit -m "ci: add Bluesky collection step to daily build workflow"
```

---

### Task 5: Create IFTTT setup guide

**Files:**
- Create: `C:\develop\daily-ai-news\docs\ifttt-setup-guide.md`

**Step 1: Write the guide**

```markdown
# IFTTT Setup Guide for X (Twitter) Auto-Collection

## Overview

IFTTTを使って、Xの公式アカウント投稿とキーワード検索を自動的にGoogle Sheetsに収集する設定ガイド。

## 前提条件

- IFTTTアカウント（Pro プラン $3.49/月、20 Applet まで）
- Google アカウント（Sheets用）
- 既存のGoogle Sheets: `https://docs.google.com/spreadsheets/d/1uuLKCLIJw--a1vCcO6UGxSpBiLTtN8uGl2cdMb6wcfg/`

## Applet の作成手順

### A. 公式アカウント監視（12 Applet）

1. https://ifttt.com/create にアクセス
2. **If This**: 「Twitter/X」→「New tweet by a specific user」を選択
3. **Username**: 例: `@OpenAI`
4. **Then That**: 「Google Sheets」→「Add row to spreadsheet」を選択
5. **Spreadsheet name**: `x_favorites`
6. **Formatted row**: `{{CreatedAt}} ||| @{{UserName}} ||| {{Text}} ||| {{FirstLinkUrl}} ||| {{LinkToTweet}}`

以下のアカウントで繰り返す:

| # | アカウント | 理由 |
|---|-----------|------|
| 1 | @OpenAI | GPTシリーズ公式 |
| 2 | @AnthropicAI | Claude公式 |
| 3 | @GoogleDeepMind | Gemini/研究発表 |
| 4 | @MetaAI | Llama/研究発表 |
| 5 | @nvidia | GPU/AI基盤 |
| 6 | @Microsoft | Copilot/Azure AI |
| 7 | @stability_ai | Stable Diffusion |
| 8 | @MistralAI | オープンモデル |
| 9 | @xaboratory | xAI/Grok |
| 10 | @huggingface | モデルハブ |
| 11 | @LangChainAI | AIツール |
| 12 | @awscloud | AWS AI サービス |

### B. キーワード検索（8 Applet）

1. **If This**: 「Twitter/X」→「New tweet from search」を選択
2. **Search for**: キーワードを入力
3. **Then That**: 同様にGoogle Sheetsへ追加

| # | 検索キーワード | 目的 |
|---|---------------|------|
| 1 | "AI launch" OR "AI release" | 新製品発表 |
| 2 | "LLM" min_faves:100 | バズったLLM投稿 |
| 3 | "GPT" min_faves:50 | GPT関連の注目投稿 |
| 4 | "Claude" min_faves:50 | Claude関連 |
| 5 | "Gemini AI" min_faves:50 | Gemini関連 |
| 6 | "AI funding" OR "AI投資" | 資金調達ニュース |
| 7 | "AI regulation" OR "AI規制" | 規制動向 |
| 8 | "AI agent" min_faves:100 | AIエージェント関連 |

## Google Sheets 列構成

build.py が読み込めるように、以下の列構成にする:

| 列 | 内容 | IFTTT変数 |
|----|------|-----------|
| A | 日付 | `{{CreatedAt}}` |
| B | @ユーザー | `@{{UserName}}` |
| C | テキスト | `{{Text}}` |
| D | 画像URL | `{{FirstLinkUrl}}` |
| E | ツイートURL | `{{LinkToTweet}}` |

## 注意事項

- IFTTTのポーリング間隔は約15分。リアルタイムではないが日次ビルドには十分
- `min_faves:N` フィルターでノイズを減らせる
- Sheets の行数上限は500万行。定期的な古い行の削除は不要（日次で数十行程度）
- IFTTT の X 連携が壊れた場合、Bluesky + Reddit RSS がフォールバックとして機能する
```

**Step 2: Commit**

```bash
git add docs/ifttt-setup-guide.md
git commit -m "docs: add IFTTT setup guide for X auto-collection"
```

---

### Task 6: End-to-end test

**Step 1: Run Bluesky collector**

Run: `cd C:\develop\daily-ai-news && python bluesky_collector.py`
Expected: `_sources/bluesky_posts.csv` created with posts

**Step 2: Run full build**

Run: `cd C:\develop\daily-ai-news && PYTHONIOENCODING=utf-8 python build.py 2>&1 | tail -30`
Expected: Output includes both X posts and Bluesky posts counts

**Step 3: Verify HTML output**

Run: `grep -c "Bluesky\|bsky" C:\develop\daily-ai-news\index.html`
Expected: Count > 0 (Bluesky posts appear in generated HTML)

**Step 4: Copy to ai-news-site and push**

```bash
cp C:\develop\daily-ai-news\index.html c:\develop\ai-news-site\daily-news\index.html
cd c:\develop\ai-news-site
git add daily-news/index.html
git commit -m "chore: update daily news with Bluesky integration"
git push origin main
```

**Step 5: Push daily-ai-news changes**

```bash
cd C:\develop\daily-ai-news
git push origin main
```
