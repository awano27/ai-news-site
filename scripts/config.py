"""
Configuration for tool ingest pipeline.
"""

import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_DIR = DATA_DIR / "schema"
DAILY_DIR = DATA_DIR / "daily"

# Data files
TOOLS_FILE = DATA_DIR / "tools.json"
INDEX_FILE = DATA_DIR / "index.json"
TOOL_SCHEMA_FILE = SCHEMA_DIR / "tool.json"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SCHEMA_DIR.mkdir(exist_ok=True)
DAILY_DIR.mkdir(exist_ok=True)

# Scoring weights
SCORING_WEIGHTS = {
    "source_rank": 30,      # Higher rank = higher score (inverted)
    "source_votes": 25,     # Votes/stars contribution
    "has_official_url": 15, # Has non-GitHub/non-PH URL
    "has_description": 10,  # Has meaningful description
    "topic_diversity": 10,  # Multiple relevant topics
    "category_match": 10    # Matches high-priority categories
}

# Priority categories (higher weight in scoring)
PRIORITY_CATEGORIES = ["ai", "automation", "meeting", "docs"]

# Deduplication settings
DEDUPE_URL_SIMILARITY = True
DEDUPE_NAME_THRESHOLD = 0.85  # Fuzzy match threshold for names

# Category keywords for classification
CATEGORY_KEYWORDS = {
    "meeting": [
        "meeting", "video", "conference", "zoom", "teams", "webex",
        "transcription", "transcript", "recording", "calendar", "schedule",
        "agenda", "minutes", "attendee", "video call"
    ],
    "docs": [
        "document", "documentation", "wiki", "notion", "obsidian",
        "notes", "note-taking", "markdown", "editor", "writing",
        "knowledge base", "confluence", "readme"
    ],
    "pm": [
        "project", "task", "kanban", "jira", "asana", "trello",
        "sprint", "agile", "scrum", "roadmap", "milestone",
        "team", "collaboration", "board"
    ],
    "automation": [
        "automation", "automate", "workflow", "zapier", "n8n", "make",
        "integration", "webhook", "trigger", "action", "pipeline",
        "no-code", "low-code", "rpa"
    ],
    "ai": [
        "ai", "artificial intelligence", "machine learning", "ml",
        "gpt", "chatgpt", "openai", "claude", "anthropic", "llm",
        "generative", "neural", "deep learning", "nlp", "transformer"
    ],
    "dev": [
        "developer", "development", "programming", "code", "coding",
        "github", "git", "api", "sdk", "cli", "terminal",
        "ide", "debug", "deploy", "devops", "ci/cd"
    ]
}

# Logging configuration
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
