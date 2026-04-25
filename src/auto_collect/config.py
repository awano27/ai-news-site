"""Auto-collect configuration."""

import os
from pathlib import Path

# Repo root resolution. Order:
#   1. PROJECT_ROOT env override (lets workflows pin a specific path)
#   2. Two levels above this file (src/auto_collect/config.py → repo root)
# Works for Windows, WSL (/mnt/c/...), and GitHub Actions runners.
_env_root = os.environ.get("PROJECT_ROOT")
if _env_root:
    PROJECT_ROOT = Path(_env_root).resolve()
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DAY_DIR = PROJECT_ROOT / "input" / "day"
LOG_DIR = PROJECT_ROOT / "logs" / "auto_collect"

# Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_MODEL = "gemma3:4b"
OLLAMA_TIMEOUT = 120

# RSS feeds (English)
EN_RSS_FEEDS = [
    {"name": "OpenAI", "url": "https://openai.com/news/rss.xml", "category": "AI Research", "priority": 1},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/", "category": "AI Research", "priority": 1},
    {"name": "Anthropic", "url": "https://www.anthropic.com/news/rss.xml", "category": "AI Research", "priority": 1},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "category": "Open Source", "priority": 2},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "AI News", "priority": 2},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "category": "AI News", "priority": 2},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/", "category": "AI Research", "priority": 2},
]

# Japanese RSS feeds
JP_RSS_FEEDS = [
    {"name": "ITmedia AI+", "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml", "category": "AI News", "priority": 2},
    {"name": "GIGAZINE", "url": "https://gigazine.net/news/rss_2.0/", "category": "Tech News", "priority": 3},
]

# Japanese AI keywords for filtering GIGAZINE
JP_AI_KEYWORDS = [
    "AI", "人工知能", "機械学習", "LLM", "ChatGPT", "OpenAI", "Google AI",
    "GPU", "ディープラーニング", "Claude", "Gemini", "GPT", "生成AI",
    "大規模言語モデル", "ニューラル", "自動運転", "画像生成", "音声認識",
]

# Hacker News
HN_MIN_SCORE = 50
HN_MAX_STORIES = 50
HN_AI_KEYWORDS = [
    "ai", "gpt", "llm", "claude", "openai", "anthropic", "gemini", "mistral",
    "machine learning", "deep learning", "neural", "transformer", "diffusion",
    "stable diffusion", "midjourney", "copilot", "chatbot", "langchain",
    "rag", "vector", "embedding", "fine-tun", "inference", "nvidia",
    "hugging face", "ollama", "llama", "agent", "autonomous",
]

# Collection settings
MAX_ARTICLES_IN_REPORT = 15
DATE_LOOKBACK_HOURS = 28

# X (Twitter) bookmarks via Obsidian vault.
# The vault is synced by C:/develop/obsidian/2026/scripts/x-sync (Playwright)
# every hour from x.com/i/bookmarks → 00 Inbox/X-Bookmarks/*.md.
# We read those .md files directly — no auth, no scraping in this repo.
_default_vault = "C:/develop/obsidian/2026" if os.name == "nt" else os.path.expanduser("~/vault")
OBSIDIAN_VAULT_PATH = Path(os.environ.get("OBSIDIAN_VAULT_PATH", _default_vault))
X_BOOKMARKS_DIR = OBSIDIAN_VAULT_PATH / "00 Inbox" / "X-Bookmarks"
X_LOOKBACK_HOURS = 72
