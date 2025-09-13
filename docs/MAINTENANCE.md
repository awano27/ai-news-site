Daily AI News maintenance notes

- Archive builder: `tools/archive_daily_ai_news.py`
  - Cleans titles/summaries with ftfy and strips HTML.
  - Normalizes item dates to YYYY-MM-DD when possible.
  - Outputs: `public-pages/news/YYYY-MM-DD.{html,json}` and updates `archive_index.json`.

- Normalizer: `tools/normalize_archive_json.py`
  - Repairs existing JSON (titles, summaries, points, dates).

- Validator: `tools/validate_archive_data.py`
  - Verifies date formats, missing files, and flags mojibake-like tokens.

- Cache busting:
  - `public-pages/version.json` is written by CI with the latest commit SHA.
  - `presentations/news_archive.html`, `ai_news_list.html`, and `ai_news_item.html` append `?v=<sha>` to fetches.

- CI: `.github/workflows/daily-archive.yml`
  - Runs daily at 00:05 JST; archives, normalizes, builds, validates, link-checks, and commits.

