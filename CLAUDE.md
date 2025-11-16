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

### Creating New Daily Slides (Manual Process)

The most common workflow for adding new AI news slides:

```bash
# 1. Create input file: input/day/MMDD.txt (e.g., 1113.txt for Nov 13)
#    - First line is the title
#    - Use bullet points (・) for key features
#    - Include URLs for sources

# 2. Create the HTML slide manually in presentations/day_slides/
#    - Use day_slide_2025_08_27.html as the reference template
#    - Use an earlier recent slide (e.g., previous day) as a practical starting point
#    - Keep the same HTML structure but customize:
#      * CSS gradient colors (--primary-color, --secondary-color, --accent-color)
#      * Breaking badge date and title
#      * Stats grid values
#      * Feature cards content
#      * Use cases, competition tables, risks, summary sections

# 3. Update all site index files to link to the new slide:
#    presentations/index.html (4 locations):
#      - Hero CTA button href
#      - Stats section (date + description)
#      - Quick links section
#      - JavaScript dynamic content (add new conditional at TOP of if-else chain)
#      - JavaScript fallback display (around line 765)
#    presentations/day_slides_index.html:
#      - Add new <li> entry at the top of the slides list
#    presentations/day_slides_list.html:
#      - Update date range in note section
#      - Add new slide card at the top of slides-grid

# 4. Commit and push
git add presentations/day_slides/day_slide_2025_MM_DD.html presentations/index.html presentations/day_slides_index.html presentations/day_slides_list.html
git commit -m "add: [topic] slide (MM/DD) with full site integration"
git push origin main
```

### Processing News Archives (Automated)

```bash
# Update JSON archives from input/day/*.txt files
python update_news_archive.py

# Verify output in public-pages/news/
# - YYYY-MM-DD.json created
# - archive_index.json updated
# - version.json updated with new timestamp
```

### Bulk Slide Operations

```bash
# Recreate multiple slides from input files
python recreate_all_slides.py

# Apply consistent styling to existing slides
python update_all_day_slides.py

# Fix link clickability issues
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

### Daily Slide Creation Workflow

**Manual HTML Slide Creation** (Most Common):
1. **Input file**: Create `input/day/MMDD.txt` with news content
2. **HTML slide**: Manually create `presentations/day_slides/day_slide_2025_MM_DD.html`
   - Copy structure from a recent slide (e.g., previous day)
   - Customize CSS color variables for each topic/brand
   - Maintain consistent section structure: header → stats → features → use cases → competition → risks → summary
3. **Site integration**: Update 3 files to link the new slide:
   - `presentations/index.html` (5 update points: hero CTA, stats section, quick links, JS dynamic content, JS fallback)
   - `presentations/day_slides_index.html` (add entry at top of list)
   - `presentations/day_slides_list.html` (update date range + add card at top)
4. **Git workflow**: Commit all 4 files together with descriptive message

**Critical**: When updating `presentations/index.html` JavaScript dynamic content, always add new conditionals at the **TOP** of the if-else chain to ensure newest slides are checked first.

### Template System

Slides use `templates/day_news_slide.html` as base template with:
- Reveal.js 4.4.0 for presentations
- Inter font family
- Custom CSS variables for theming (--primary-color, --secondary-color, --accent-color)
- Animated gradient backgrounds
- Standardized layout based on day_slide_2025_08_27.html
- Self-contained HTML files (no external dependencies except fonts)

**Recent slides serve as better templates** than the base template because they have the latest styling patterns and section structures.

### Archive Indexing

- `archive_index.json` - Array of all daily entries with date/file/count
- `version.json` - Contains version hash, last update timestamp, total entry count
- `latest.json` - Symlink/copy to most recent day's data

### Update Logic

- Today's data is always force-updated
- Past data only updates if source file is newer than JSON (via mtime comparison)
- Version hash uses MD5 of current timestamp
- Site integration requires updating multiple index files atomically (commit together)

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

## Slide Content Enhancement Workflow

When users provide additional information sources (e.g., `1113-2.txt` supplementing `1113.txt`):

1. **Read both source files** to understand all available information
2. **Identify high-value additions** that make users want to use the technology:
   - Concrete performance metrics (accuracy %, speed improvements, cost savings)
   - Practical implementation examples (code samples, API usage patterns)
   - Real-world use cases with specific outcomes
   - Cost optimization strategies
   - Risk/limitation awareness
3. **Strategic section additions**:
   - Enhance stats grid with quantitative improvements
   - Add "how-to" sections (e.g., custom instructions, API integration)
   - Include competitive advantages with numbers
   - Provide implementation code examples when available
4. **Maintain slide structure** while adding depth - don't break existing sections
5. **Commit with detailed message** explaining what value was added

**Example enhancements**:
- Adding "Custom Instructions" section with copy-pasteable templates
- Including "API & Rollout" section with implementation examples
- Expanding stats with specific benchmarks (accuracy, cost, speed)
- Adding practical use case sections (medical, coding, business)

## Important Notes

- The system handles Japanese (日本語) content - be careful with character encoding
- Dates in filenames are MM-DD format without year prefix (MMDD.txt)
- The working slide template is `day_slide_2025_08_27.html` - use as reference for styling
- **Recent slides are better templates** than base templates - they have latest patterns
- URL extraction uses regex: `https?://[^\s<>"{}|\\^`\[\]]+`
- Slides disable Reveal.js controls by default (see CSS customizations)
- There are some legacy/temp files (tmp_*.py, tmp_*.html) that can be ignored
- Multiple input files for same date (e.g., `1113.txt` + `1113-2.txt`) should be merged into comprehensive slides

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
