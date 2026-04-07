"""Ollama-based AI summarizer and scorer with evidence layer."""

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

import requests

from .config import OLLAMA_URL, OLLAMA_CHAT_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT = """以下のAIニュース記事を日本語で要約し、エビデンス情報を抽出してください。

タイトル: {title}
ソース: {source}
内容: {content}

以下のJSON形式のみで回答してください（説明文不要）:
{{
  "title_ja": "日本語タイトル",
  "summary": "3文以内の日本語要約",
  "points": ["・ポイント1", "・ポイント2", "・ポイント3"],
  "score": 50,
  "category": "AI Model",
  "metrics": ["具体的な数値データがあれば抽出"],
  "competitors": ["競合・比較対象があれば記載"],
  "impact_ja": "日本企業・エンジニアへの影響を1文で",
  "actionable": "エンジニアが今すぐ試せるか（pip install名、URL、API等）"
}}

scoreは20-100の重要度:
- 90-100: 業界を変える発表
- 70-89: エンジニア必読
- 50-69: 注目すべき動き
- 20-49: 参考情報
categoryは AI Model / Business / Research / Product / Hardware のいずれか"""


class OllamaProcessor:
    """Process articles using Ollama for summarization, scoring, and evidence extraction."""

    def __init__(self):
        self.available = self._check_ollama()

    def _check_ollama(self) -> bool:
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            logger.warning("[Processor] Ollama not available, using fallback scoring")
            return False

    def _process_one(self, article: Dict) -> Optional[Dict]:
        """Process a single article with Ollama or fallback."""
        try:
            if self.available:
                result = self._process_with_ollama(article)
            else:
                result = self._fallback_process(article)
            return result
        except Exception as e:
            logger.warning(f"[Processor] Error: '{article.get('name', '?')}': {e}")
            return self._fallback_process(article)

    def process_batch(self, articles: List[Dict]) -> List[Dict]:
        """Process all articles with parallel execution."""
        processed = []
        workers = 3 if self.available else 1

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._process_one, a): a for a in articles}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    processed.append(result)

        processed.sort(key=lambda x: x.get("score", 0), reverse=True)
        return processed

    def process_github_repos(self, repos: List[Dict]) -> List[Dict]:
        """Process GitHub trending repos into article format."""
        processed = []
        for repo in repos:
            stars = repo.get("stars", 0)
            forks = repo.get("forks", 0)
            lang = repo.get("language", "")
            license_id = repo.get("license", "")
            topics = repo.get("topics", [])

            score = 40
            if stars > 1000:
                score = 85
            elif stars > 500:
                score = 75
            elif stars > 100:
                score = 60

            processed.append({
                "title": repo["name"],
                "title_en": repo["name"],
                "summary": repo.get("tagline", ""),
                "points": [],
                "score": score,
                "category": "Product",
                "url": repo.get("url", ""),
                "source": "GitHub Trending",
                "evidence": {
                    "metrics": [f"⭐ {stars:,} stars", f"🔀 {forks:,} forks"],
                    "competitors": [],
                    "impact_ja": f"{lang}で実装。今すぐclone可能。",
                    "actionable": f"git clone {repo.get('url', '')}",
                    "license": license_id,
                    "topics": topics[:5],
                },
            })

        processed.sort(key=lambda x: x.get("score", 0), reverse=True)
        return processed

    def process_benchmarks(self, benchmarks: List[Dict]) -> List[Dict]:
        """Process benchmark/trending model data."""
        processed = []
        for item in benchmarks:
            downloads = item.get("downloads", 0)
            likes = item.get("likes", 0)

            score = 45
            if downloads > 1_000_000:
                score = 80
            elif downloads > 100_000:
                score = 65
            elif likes > 100:
                score = 55

            processed.append({
                "title": item["name"],
                "title_en": item["name"],
                "summary": item.get("tagline", ""),
                "points": [],
                "score": score,
                "category": "AI Model",
                "url": item.get("url", ""),
                "source": "HuggingFace Trending",
                "evidence": {
                    "metrics": [
                        f"📥 {downloads:,} downloads" if downloads else "",
                        f"❤️ {likes:,} likes" if likes else "",
                    ],
                    "competitors": [],
                    "impact_ja": f"HuggingFaceでトレンド中。{item.get('pipeline_tag', '')}タスク向け。",
                    "actionable": f"from transformers import AutoModel; model = AutoModel.from_pretrained('{item['name']}')",
                },
            })

        processed.sort(key=lambda x: x.get("score", 0), reverse=True)
        return processed

    def process_funding(self, funding_items: List[Dict]) -> List[Dict]:
        """Process funding/M&A news."""
        processed = []
        for item in funding_items:
            amount = item.get("funding_amount", "")
            score = 70 if amount else 55

            processed.append({
                "title": item["name"],
                "title_en": item["name"],
                "summary": item.get("tagline", ""),
                "points": [],
                "score": score,
                "category": "Business",
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "evidence": {
                    "metrics": [f"💰 {amount}"] if amount else [],
                    "competitors": [],
                    "impact_ja": "AI業界の資金動向。投資判断の参考に。",
                    "actionable": "",
                },
            })

        processed.sort(key=lambda x: x.get("score", 0), reverse=True)
        return processed

    def _process_with_ollama(self, article: Dict) -> Optional[Dict]:
        """Summarize, score, and extract evidence using Ollama."""
        title = article.get("name", "")
        source = article.get("rss_source", article.get("source", ""))
        content = article.get("description", article.get("tagline", ""))

        prompt = SUMMARIZE_PROMPT.format(
            title=title[:200],
            source=source,
            content=content[:500]
        )

        try:
            resp = requests.post(
                OLLAMA_CHAT_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=OLLAMA_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]

            parsed = self._extract_json(text)
            if parsed:
                return {
                    "title": parsed.get("title_ja", title),
                    "title_en": title,
                    "summary": parsed.get("summary", ""),
                    "points": parsed.get("points", []),
                    "score": max(20, min(100, int(parsed.get("score", 50)))),
                    "category": parsed.get("category", "AI Technology"),
                    "url": article.get("links", {}).get("official", ""),
                    "source": source,
                    "hn_score": article.get("hn_score"),
                    "evidence": {
                        "metrics": parsed.get("metrics", []),
                        "competitors": parsed.get("competitors", []),
                        "impact_ja": parsed.get("impact_ja", ""),
                        "actionable": parsed.get("actionable", ""),
                    },
                }

        except Exception as e:
            logger.warning(f"[Ollama] Failed for '{title}': {e}")

        return self._fallback_process(article)

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from model response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        match = re.search(r'\{[^{}]*"title_ja"[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _fallback_process(self, article: Dict) -> Dict:
        """Fallback scoring without Ollama."""
        title = article.get("name", "")
        tagline = article.get("tagline", "")
        url = article.get("links", {}).get("official", "")

        score = 40
        if article.get("source_rank", 99) <= 1:
            score += 20
        if article.get("hn_score", 0) > 100:
            score += 15
        elif article.get("hn_score", 0) > 50:
            score += 10

        text_lower = (title + " " + tagline).lower()
        category = "AI Technology"
        for cat, keywords in {
            "AI Model": ["gpt", "llm", "model", "claude", "gemini", "llama"],
            "Business": ["funding", "acquisition", "ipo", "valuation", "資金調達"],
            "Research": ["paper", "research", "study", "benchmark", "論文"],
            "Product": ["launch", "release", "announce", "リリース", "発表"],
            "Hardware": ["chip", "gpu", "cpu", "nvidia", "チップ"],
        }.items():
            if any(kw in text_lower for kw in keywords):
                category = cat
                break

        return {
            "title": title,
            "title_en": title,
            "summary": tagline[:300],
            "points": [],
            "score": min(100, score),
            "category": category,
            "url": url,
            "source": article.get("rss_source", article.get("source", "")),
            "hn_score": article.get("hn_score"),
            "evidence": {
                "metrics": [],
                "competitors": [],
                "impact_ja": "",
                "actionable": "",
            },
        }
