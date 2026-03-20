# Social Media Collection Redesign

**Date**: 2026-03-20
**Status**: Approved
**Cost**: $3.49/month (IFTTT Pro)

## Problem

X (Twitter) posts are currently added to Daily News via manual Google Sheets curation. This is time-consuming and limits coverage. We want to automate collection while keeping costs minimal.

## Solution: IFTTT + Bluesky + Reddit Hybrid

### Architecture

```
[IFTTT $3.49/mo]
  X official accounts (12) + keyword search (8)
  → Google Sheets (existing CSV)

[Bluesky API - Free]
  AI researchers (15-30) + keyword search
  → bluesky_collector.py → _sources/bluesky_posts.csv

[Reddit RSS - Free]
  r/MachineLearning, r/LocalLLaMA, etc.
  → feeds.yml (existing, no changes)

All sources → build.py → gather_x_posts() + gather_bluesky_posts() → index.html
```

### Component 1: IFTTT Configuration

**Plan**: IFTTT Pro ($3.49/month, 20 Applets)

**Applet allocation (20 total)**:

| Type | Count | Targets |
|------|-------|---------|
| Official accounts | 12 | OpenAI, Anthropic, Google DeepMind, Meta AI, Nvidia, Microsoft, Stability AI, Mistral, xAI, Hugging Face, LangChain, AWS AI |
| Keyword search | 8 | "AI launch", "LLM release", "GPT", "Claude", "Gemini", "AI funding", "AI規制", "AI新機能" |

**Each Applet**:
- Trigger: "New tweet by specific user" or "New tweet from search"
- Action: "Add row to Google Sheets"
- Output columns: `日付, @ユーザー, テキスト, 画像URL, ツイートURL` (matches existing CSV format)
- Polling interval: ~15 minutes (IFTTT default)

### Component 2: Bluesky Collector

**New file**: `bluesky_collector.py` in daily-ai-news repo

**Behavior**:
1. Connect to Bluesky public API via `atproto` library (no auth required for public search)
2. Collect posts from:
   - Author feeds: `app.bsky.feed.getAuthorFeed` for specified accounts
   - Keyword search: `app.bsky.feed.searchPosts` for AI-related terms
3. Convert to existing CSV format (日付, @ユーザー, テキスト, 画像URL, URL)
4. Output to `_sources/bluesky_posts.csv`

**Target accounts (Bluesky)**:
- AI researchers: @ylecun.bsky.social, @karpathy.bsky.social, etc.
- AI media: @theverge.bsky.social, etc.
- 15-30 accounts (no limit, free API)

**Keywords**: AI, LLM, GPT, Claude, Gemini, neural network, machine learning

**Configuration via environment variables**:
```
BLUESKY_ACCOUNTS=ylecun.bsky.social,karpathy.bsky.social,...
BLUESKY_KEYWORDS=AI,LLM,GPT,Claude,Gemini
BLUESKY_OUTPUT=_sources/bluesky_posts.csv
BLUESKY_HOURS=36
```

### Component 3: build.py Modifications

**Minimal changes** (~10 lines):
- After `gather_x_posts(X_POSTS_CSV)`, also call `gather_x_posts("_sources/bluesky_posts.csv")`
- Bluesky posts merge into the same Posts category
- Source field set to "Bluesky" instead of "X / SNS"

### Component 4: GitHub Actions Workflow

**Change**: Add Bluesky collection step before build in `run-csv-deploy.yml`

```yaml
- name: Collect Bluesky posts
  continue-on-error: true
  run: python bluesky_collector.py
  env:
    BLUESKY_ACCOUNTS: "ylecun.bsky.social,karpathy.bsky.social,..."
    BLUESKY_KEYWORDS: "AI,LLM,GPT,Claude,Gemini"
    BLUESKY_OUTPUT: "_sources/bluesky_posts.csv"
    BLUESKY_HOURS: "36"
```

**Fallback**: `continue-on-error: true` ensures build proceeds with X + RSS even if Bluesky fails.

### Component 5: Dependencies

Add to `requirements.txt`:
```
atproto>=0.0.46
```

## Deliverables

| # | File | Action | Scope |
|---|------|--------|-------|
| 1 | `bluesky_collector.py` | New | Bluesky API → CSV collector |
| 2 | `build.py` | Modify | Add Bluesky CSV reading (~10 lines) |
| 3 | `requirements.txt` | Modify | Add `atproto` |
| 4 | `.github/workflows/run-csv-deploy.yml` | Modify | Add Bluesky step |
| 5 | `docs/ifttt-setup-guide.md` | New | IFTTT configuration instructions |

## Cost Summary

| Source | Monthly Cost | Posts/day estimate |
|--------|-------------|-------------------|
| IFTTT (X) | $3.49 | 20-40 |
| Bluesky API | $0 | 15-30 |
| Reddit RSS | $0 | 8-15 (existing) |
| **Total** | **$3.49** | **43-85** |

## Risks

- IFTTT's X integration could break if X changes API terms (mitigated by Bluesky/Reddit fallback)
- Bluesky public search API could add rate limits in future (currently very generous)
- Google Sheets row limit (10M cells) — not a concern at this volume
