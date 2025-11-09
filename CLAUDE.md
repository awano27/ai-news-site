# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI News Archive system that automatically extracts, processes, and presents daily AI-related news. The system generates JSON archives from text inputs and creates Reveal.js presentation slides for daily news summaries. The site is hosted on GitHub Pages at https://awano27.github.io/ai-news-site/

## Core Architecture

### Data Flow Pipeline

1. **Input**: Raw text files in `input/day/MMDD.txt` (e.g., `0913.txt` for September 13)
2. **Processing**: Python scripts extract content, categorize, score, and structure data
3. **Storage**: JSON files generated in `news/` (dated archives) and `public-pages/news/` (versioned archives)
4. **Presentation**: HTML slides in `presentations/day_slides/` using Reveal.js
5. **Publishing**: GitHub Pages serves the static site

### Key Directories

- `input/day/` - Daily news text files (MMDD.txt format)
- `presentations/day_slides/` - Generated Reveal.js HTML slides for each day
- `news/` - JSON archives of processed news (YYYY-MM-DD.json format)
- `public-pages/news/` - Versioned archive with archive_index.json and version.json
- `templates/` - Jinja2-style HTML templates for slide generation
- `prompts/` - Master prompt and guidelines for AI news analysis
- `script/` and `scripts/` - Utility scripts for building and fixing content

### Primary Scripts

**Archive Management:**
- `update_news_archive.py` - Main script to process input/day/*.txt files and update JSON archives
- `extract_daily_news.py` - Fetches news from external daily-ai-news-pages site and converts to JSON
- `sync_daily_ai_news.py` - Syncs with external daily-ai-news-pages site using BeautifulSoup

**Slide Generation:**
- `recreate_all_slides.py` - Recreates all day slides from template
- `update_all_day_slides.py` - Applies consistent styling to all day slides
- `fix_slide_links.py` - Fixes link clickability issues in slides

**Build Scripts:**
- `build.py` - Main build script
- `script/build_news.py` - Processes news data
- `script/build_day_slides_json.py` - Builds day slides JSON index

## Common Development Commands

### Processing New Daily News

```bash
# 1. Add new text file to input/day/ (e.g., input/day/1110.txt for Nov 10)
# 2. Update the archive
python update_news_archive.py

# 3. Verify output in public-pages/news/
# - YYYY-MM-DD.json created
# - archive_index.json updated
# - version.json updated with new timestamp
```

### Working with Slides

```bash
# Generate slides from input files
python recreate_all_slides.py

# Apply consistent styling to existing slides
python update_all_day_slides.py

# Fix link issues in slides
python fix_slide_links.py
```

### Syncing External Sources

```bash
# Fetch latest from daily-ai-news-pages
python sync_daily_ai_news.py

# Extract from external HTML source
python extract_daily_news.py
```

## Data Format Specifications

### Input Text Format (input/day/MMDD.txt)

```
ニュースタイトル（1行目 = title）
主な内容の説明...

主要発表: 詳細情報...
・ポイント1
・ポイント2

URL関連情報:
公式サイト: https://example.com
```

### Generated JSON Format (news/YYYY-MM-DD.json)

```json
{
  "date": "2025-09-13",
  "source": "input/day/0913.txt",
  "count": 1,
  "items": [{
    "title": "...",
    "score": 85,
    "rank": 1,
    "url": "https://...",
    "summary": "...",
    "points": ["・ポイント1", "・ポイント2"],
    "links": [{"href": "URL", "text": "リンク名"}],
    "category": "AI Model",
    "date": "2025-09-13"
  }]
}
```

### Categories

Auto-classified based on keywords:
- **AI Model**: GPT, LLM, Transformer, Neural
- **Business**: 資金調達, 投資, IPO, 買収
- **Research**: 論文, 研究, 実験, テスト
- **Product**: リリース, 発表, ローンチ
- **Hardware**: チップ, GPU, CPU

### Scoring System

Score range: 20-100, calculated from:
- Title length
- Summary quality and length
- Number of URLs
- Presence of important keywords
- Points extracted

## Architecture Patterns

### Date Parsing

Files use MMDD.txt format (no year prefix). Scripts assume current year (2025 as of this writing). The `parse_date_from_filename()` function converts `0913.txt` → `2025-09-13`.

### Template System

Slides use `templates/day_news_slide.html` as base template with:
- Reveal.js 4.4.0 for presentations
- Inter font family
- Custom CSS variables for theming
- Animated gradient backgrounds
- Standardized layout based on day_slide_2025_08_27.html

### Archive Indexing

- `archive_index.json` - Array of all daily entries with date/file/count
- `version.json` - Contains version hash, last update timestamp, total entry count
- `latest.json` - Symlink/copy to most recent day's data

### Update Logic

- Today's data is always force-updated
- Past data only updates if source file is newer than JSON (via mtime comparison)
- Version hash uses MD5 of current timestamp

## Character Encoding

- All files MUST use UTF-8 encoding (BOM-free on Windows)
- Watch for mojibake issues - there are dedicated fix scripts
- PowerShell scripts may have encoding helpers (e.g., `fix_encoding.ps1`)

## Git Workflow

This is a GitHub Pages site. The main branch serves the site:
- Commit generated files (JSON, HTML slides) to track history
- Push to main triggers GitHub Pages rebuild
- Use descriptive commit messages (see git log for examples)

### Common Commit Pattern

```bash
git add public-pages/news/ presentations/day_slides/
git commit -m "add: latest AI news archive YYYY-MM-DD"
git push origin main
```

## Dependencies

Python packages (see `requirements.txt`):
- `beautifulsoup4` - HTML parsing for external scraping
- `requests` - HTTP requests for fetching external data
- `feedparser` - RSS/Atom feed parsing
- `trafilatura` - Web content extraction
- `PyYAML` - YAML config parsing (sources.yaml)
- `ftfy` - Text encoding fixes

Install with:
```bash
pip install -r requirements.txt
```

## Important Notes

- The system handles Japanese (日本語) content - be careful with character encoding
- Dates in filenames are MM-DD format without year prefix
- The working slide template is `day_slide_2025_08_27.html` - use as reference for styling
- URL extraction uses regex: `https?://[^\s<>"{}|\\^`\[\]]+`
- Slides disable Reveal.js controls by default (see CSS customizations)
- There are some legacy/temp files (tmp_*.py, tmp_*.html) that can be ignored

## Testing & Verification

After updates:
1. Check JSON validity in public-pages/news/
2. Verify archive_index.json is sorted by date (newest first)
3. Open slides in browser to test rendering
4. Check for character encoding issues (mojibake)
5. Verify links are clickable in slides

## Site Structure

Main pages:
- `index.html` - Main site landing page
- `presentations/index.html` - Presentations hub
- `presentations/day_slides_index.html` - Index of all daily slides
- `presentations/day_slides_list.html` - Detailed list view
- `presentations/news_archive.html` - Searchable news archive viewer
- `presentations/ai_external_resources.html` - External resources compilation

## Content Guidelines

Based on `prompts/master_prompt_ja.md`, the system follows journalistic principles:
- Primary sources first (公式発表、法定開示、原論文)
- Strict timestamp tracking (UTC + JST)
- Fact/interpretation/speculation separation
- Evidence labeling (Fact-A/B/C, Claim, Rumor, Opinion, Forecast)
- Impact assessment (technical/economic/regulatory)
