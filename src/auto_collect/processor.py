"""LLM-backed AI summarizer and scorer with evidence layer.

Uses `llm_provider.LLMProvider` so the same processor can run against either
local Ollama or cloud NVIDIA NIM. The provider is responsible for the actual
chat-completions call; this module owns prompt construction and JSON parsing.
"""

import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from time import monotonic
from typing import Callable, Dict, List, Optional

from .config import ollama_fallback_model
from .llm_provider import LLMProvider, make_provider
from .content_integrity import apply_financial_integrity
from .quality import is_japanese_summary, is_japanese

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT = """以下のAIニュース記事を日本語で要約し、エビデンス情報を抽出してください。

タイトル: {title}
ソース: {source}
内容: {content}

以下のJSON形式のみで回答してください（説明文不要）:
{{
  "title_ja": "日本語タイトル",
  "tldr": "1行・40字以内の超短要約（記事本質のみ）",
  "summary": "3文以内の日本語要約",
  "points": ["・ポイント1", "・ポイント2", "・ポイント3"],
  "score": 50,
  "category": "AI Model",
  "metrics": ["具体的な数値データがあれば抽出"],
  "competitors": ["競合・比較対象があれば記載"],
  "impact_ja": "日本企業・エンジニアへの影響を1文で",
  "actionable": "エンジニアが今すぐ試せるか（pip install名、URL、API等）",
  "evidence_label": "Fact"
}}

scoreは20-100の重要度:
- 90-100: 業界を変える発表
- 70-89: エンジニア必読
- 50-69: 注目すべき動き
- 20-49: 参考情報
categoryは AI Model / Business / Research / Product / Hardware のいずれか
evidence_labelは Fact（公式発表・一次情報） / Claim（企業/関係者の主張） / Rumor（噂・未確認） のいずれか"""


X_SUMMARIZE_PROMPT = """次のX投稿を日本語で要約し、AI関連かどうか判定してください。

投稿者: {source}
本文: {content}

以下のJSON形式のみで回答してください（説明文不要）:
{{
  "title_ja": "日本語の短い見出し",
  "summary": "3文以内の日本語要約",
  "ai_related": true
}}

ai_relatedは、AIのモデル・研究・製品・企業・規制・実装に関係する投稿ならtrue、それ以外はfalse。"""

# Appended only after the first answer fails the same Japanese checks the
# publication gate uses. The first request is unchanged.
NEWS_RETRY_SUFFIX = (
    "\n前の応答は必須条件を満たしていません。title_jaは製品名だけでなく日本語で内容を説明し、"
    "summaryも日本語で返してください。JSON以外は返さないでください。"
)
X_RETRY_SUFFIX = (
    "\n前の応答は必須条件を満たしていません。title_jaとsummaryは日本語にし、"
    "ai_relatedはtrueかfalseだけにしてください。JSON以外は返さないでください。"
)
# The provider already retries HTTP 429/5xx and network errors. These are
# output failures, so a new completion can still produce a usable summary.
CONTENT_RETRYABLE_ERRORS = frozenset({
    "",
    "invalid_japanese",
    "truncated_response",
    "empty_response",
    "invalid_response",
})
# One stricter retry, then one temperature or fallback-model retry.
SUMMARY_RETRY_ATTEMPTS = 2


class LLMProcessor:
    """Process articles using an LLM for summarization, scoring, and evidence extraction.

    Pass `provider` to override the default Ollama backend. When the provider
    is unavailable (health-check failed), the processor transparently falls
    back to heuristic scoring so the pipeline never produces an empty report.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or make_provider("ollama")
        self.available = self.provider.available
        self._retry_lock = Lock()
        self._stats = {
            "ok_first": 0,
            "retried": 0,
            "recovered": 0,
            "dropped": 0,
            "extra_calls": 0,
            "budget_skipped": 0,
        }
        self._additional_calls = 0
        self._additional_started: Optional[float] = None

    def translation_retry_stats(self) -> Dict[str, int]:
        with self._retry_lock:
            return dict(self._stats)

    def log_translation_retry_summary(self, target_logger: Optional[logging.Logger] = None) -> None:
        stats = self.translation_retry_stats()
        (target_logger or logger).info(
            "translation retry summary: ok_first=%d retried=%d recovered=%d dropped=%d extra_calls=%d budget_skipped=%d",
            stats["ok_first"], stats["retried"], stats["recovered"],
            stats["dropped"], stats["extra_calls"], stats["budget_skipped"],
        )

    def _count(self, key: str) -> None:
        with self._retry_lock:
            self._stats[key] += 1

    def _additional_budget(self) -> int:
        raw = os.environ.get("SUMMARY_RETRY_CALL_BUDGET", "24")
        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            return 24

    def _additional_seconds(self) -> float:
        raw = os.environ.get("SUMMARY_RETRY_BUDGET_SEC", "120")
        try:
            return max(0.0, float(raw))
        except (TypeError, ValueError):
            return 120.0

    def _reserve_additional(self, title: str) -> bool:
        """Bound the second content retry so the 08:00 run cannot grow without limit."""
        with self._retry_lock:
            now = monotonic()
            if self._additional_started is None:
                self._additional_started = now
            over_budget = (
                self._additional_calls >= self._additional_budget()
                or now - self._additional_started > self._additional_seconds()
            )
            if over_budget:
                self._stats["budget_skipped"] += 1
                logger.info(
                    "[%s] translation retry budget exhausted; not retrying '%s' again",
                    getattr(self.provider, "name", ""), title[:60],
                )
                return False
            self._additional_calls += 1
            return True

    def _current_model(self) -> str:
        return str(getattr(getattr(self.provider, "config", None), "model", "") or "")

    def _provider_error(self) -> str:
        return getattr(self.provider, "last_error", "") or "provider_unavailable"

    def _retry_request(self, retry_index: int) -> tuple:
        # Temperature and a second local model apply only to Ollama. NVIDIA
        # request bodies stay on the provider's existing configuration.
        if getattr(self.provider, "name", "") != "ollama":
            return None, None
        if retry_index >= SUMMARY_RETRY_ATTEMPTS:
            fallback = ollama_fallback_model(self._current_model())
            if fallback:
                return 0.2, fallback
            return 0.7, None
        return 0.2, None

    def _invoke(self, prompt: str, *, temperature: Optional[float] = None, model: Optional[str] = None):
        setter = getattr(self.provider, "set_request_options", None)
        if callable(setter):
            setter(temperature=temperature, model=model)
        return self.provider.chat(prompt)

    def _complete_translation(
        self,
        prompt: str,
        accept: Callable[[str], Optional[Dict]],
        *,
        title: str,
        strict_suffix: str,
    ) -> tuple:
        """Return (parsed, error). A still-failing article is not published."""
        label = title[:60]
        name = getattr(self.provider, "name", "")
        text = self._invoke(prompt)
        parsed = accept(text) if text else None
        if parsed is not None:
            self._count("ok_first")
            return parsed, ""
        if not text:
            reason = self._provider_error()
            if reason not in CONTENT_RETRYABLE_ERRORS:
                self._count("dropped")
                logger.warning("[%s] no response for '%s' (%s)", name, label, reason)
                logger.info("[%s] translation dropped '%s' reason=%s", name, label, reason)
                return None, reason
        else:
            reason = "invalid_japanese"

        self._count("retried")
        for retry_index in range(1, SUMMARY_RETRY_ATTEMPTS + 1):
            if retry_index >= SUMMARY_RETRY_ATTEMPTS and not self._reserve_additional(label):
                break
            temperature, model = self._retry_request(retry_index)
            logger.warning(
                "[%s] translation retry %s/%s for '%s' reason=%s temperature=%s model=%s",
                name, retry_index, SUMMARY_RETRY_ATTEMPTS, label, reason,
                "default" if temperature is None else temperature,
                model or self._current_model(),
            )
            self._count("extra_calls")
            text = self._invoke(prompt + strict_suffix, temperature=temperature, model=model)
            if not text:
                reason = self._provider_error()
                logger.warning(
                    "[%s] no response for '%s' on translation retry %s (%s)",
                    name, label, retry_index, reason,
                )
                if reason not in CONTENT_RETRYABLE_ERRORS:
                    break
                continue
            parsed = accept(text)
            if parsed is not None:
                self._count("recovered")
                logger.info(
                    "[%s] translation retry recovered '%s' on attempt %s",
                    name, label, retry_index,
                )
                return parsed, ""
            reason = "invalid_japanese"
        self._count("dropped")
        logger.info("[%s] translation dropped '%s' reason=%s", name, label, reason)
        return None, reason or "invalid_japanese"

    def _localize_structured(self, rows: List[Dict], *, preserve_names: bool) -> List[Dict]:
        """Translate descriptive text while retaining source-specific facts."""
        for row in rows:
            raw = {"name": row["title"], "description": row.get("summary", ""),
                   "tagline": row.get("summary", ""), "source": row.get("source", ""),
                   "links": {"official": row.get("url", "")}}
            localized = self._process_one(raw, accept_english_title=preserve_names)
            if localized:
                row["summary"] = localized.get("summary", "")
                row["processing_status"] = localized.get("processing_status", "fallback")
                if localized.get("processing_error"):
                    row["processing_error"] = localized["processing_error"]
                if not preserve_names:
                    row["title"] = localized.get("title", row["title"])
                row.update({k: v for k, v in apply_financial_integrity(row).items()})
        return rows

    def _process_one(self, article: Dict, *, accept_english_title: bool = False) -> Optional[Dict]:
        try:
            if self.available:
                result = self._process_with_llm(article, accept_english_title=accept_english_title)
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

            processed.append(apply_financial_integrity({
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
            }))

        processed.sort(key=lambda x: x.get("score", 0), reverse=True)
        return self._localize_structured(processed, preserve_names=True)

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

            processed.append(apply_financial_integrity({
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
            }))

        processed.sort(key=lambda x: x.get("score", 0), reverse=True)
        return self._localize_structured(processed, preserve_names=True)

    def process_x_posts(self, posts: List[Dict]) -> List[Dict]:
        """Summarize X posts through the same provider.chat path as news.

        The provider owns request spacing and HTTP 429 retry. A response that
        arrives but breaks the summary or judgement format is retried up to
        twice before the quality gate. A completed judgement that the post is
        not about AI is not sent again. Posts are returned either way so the
        publication gate can record summary failures and ai_related false in
        quality.excluded.
        """
        return [self._process_x_post(post) for post in posts]

    def _process_x_post(self, post: Dict) -> Dict:
        source = post.get("rss_source") or post.get("source") or "X"
        content = post.get("description") or post.get("tagline") or ""
        prompt = X_SUMMARIZE_PROMPT.format(source=source, content=str(content)[:500])
        if not self.available:
            return self._x_row(post, error=getattr(self.provider, "last_error", "") or "provider_unavailable")
        parsed, error = self._complete_translation(
            prompt, self._accepted_x, title=str(post.get("name") or ""), strict_suffix=X_RETRY_SUFFIX,
        )
        if parsed is None:
            return self._x_row(post, error=error or "invalid_japanese")
        return self._x_row(post, parsed=parsed)

    def _accepted_x(self, text: str) -> Optional[Dict]:
        parsed = self._extract_json(text)
        if not (isinstance(parsed, dict) and isinstance(parsed.get("title_ja"), str)
                and parsed["title_ja"].strip() and is_japanese_summary(parsed.get("summary"))):
            return None
        if parsed.get("ai_related") is not True and parsed.get("ai_related") is not False:
            return None
        return parsed

    def _x_row(self, post: Dict, *, parsed: Optional[Dict] = None, error: str = "") -> Dict:
        url = post.get("url") or (post.get("links") or {}).get("official") or ""
        source = post.get("rss_source") or post.get("source") or "X"
        title = ((parsed or {}).get("title_ja") or post.get("name") or "")
        summary = (parsed or {}).get("summary") or str(post.get("tagline") or "")[:300]
        row = {
            "title": title,
            "name": post.get("name") or title,
            "processing_status": "llm" if parsed else "fallback",
            "title_en": post.get("name") or "",
            "summary": summary,
            "tldr": (str(parsed.get("title_ja") or "")[:80] if parsed else str(post.get("tagline") or "")[:80]),
            "url": url,
            "source": source,
            "rss_source": source,
            "x_curated": True,
            "x_tweet_id": post.get("x_tweet_id") or "",
            "x_images": list(post.get("x_images") or []),
            "x_note": post.get("x_note") or "",
            "bookmark_date": post.get("bookmark_date") or "",
            "authors": post.get("authors") or "",
            "description": post.get("description") or "",
            "links": post.get("links") or ({"official": url} if url else {}),
            "score": int(post.get("score") or 75),
            "category": post.get("category") or "X ポスト",
            "evidence_label": post.get("evidence_label") or "Curated",
        }
        if parsed is not None:
            row["ai_related"] = parsed.get("ai_related") is True
        if error:
            row["processing_error"] = error
        return apply_financial_integrity(row)

    def process_funding(self, funding_items: List[Dict]) -> List[Dict]:
        """Process funding/M&A news."""
        processed = []
        for item in funding_items:
            amount = item.get("funding_amount", "")
            score = 70 if amount else 55

            processed.append(apply_financial_integrity({
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
            }))

        processed.sort(key=lambda x: x.get("score", 0), reverse=True)
        return self._localize_structured(processed, preserve_names=False)

    def _process_with_llm(self, article: Dict, *, accept_english_title: bool = False) -> Optional[Dict]:
        """Summarize, score, and extract evidence using the configured LLM."""
        title = article.get("name", "")
        source = article.get("rss_source", article.get("source", ""))
        content = str(article.get("description") or article.get("tagline") or "").strip()
        # A headline is not evidence for a substantive summary. In particular,
        # HN supplies its title as tagline; never ask the model to fill that gap.
        normalized = lambda value: " ".join(str(value).split()).casefold()
        if not content or normalized(content) == normalized(title):
            return self._fallback_process(article, error="source_context_missing")

        prompt = SUMMARIZE_PROMPT.format(
            title=title[:200],
            source=source,
            content=content[:500]
        )
        prompt += "\n与えたタイトルと本文だけを根拠にしてください。未記載の性能・料金・開発元・導入手順・用途・効果を推測しないでください。情報がない項目は空配列または空文字にし、短い紹介文を詳しい製品評価に膨らませないでください。"

        parsed, error = self._complete_translation(
            prompt,
            lambda response: self._accepted_summary(response, require_japanese_title=not accept_english_title),
            title=title,
            strict_suffix=NEWS_RETRY_SUFFIX,
        )
        if parsed is None:
            return self._fallback_process(article, error=error or "invalid_japanese")
        return apply_financial_integrity({
            "title": parsed.get("title_ja", title),
            "processing_status": "llm",
            "published_at": article.get("published_at") or article.get("date") or "",
            "title_en": title,
            "tldr": parsed.get("tldr", "")[:80],
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
                "evidence_label": parsed.get("evidence_label", ""),
            },
        })

    def _accepted_summary(self, text: str, *, require_japanese_title: bool = True) -> Optional[Dict]:
        parsed = self._extract_json(text)
        if not isinstance(parsed, dict) or not is_japanese_summary(parsed.get("summary")):
            return None
        # GitHub and Hugging Face listings publish the source identifier as the
        # title. The quality gate already allows that, so a Japanese summary is
        # enough. Narrative articles still need a Japanese title_ja.
        if require_japanese_title:
            title = parsed.get("title_ja")
            if not isinstance(title, str) or not title.strip() or not is_japanese(title):
                return None
        return parsed

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

    def _fallback_process(self, article: Dict, *, error: str = "provider_unavailable") -> Dict:
        """Fallback scoring when the LLM provider is unavailable."""
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

        return apply_financial_integrity({
            "title": title,
            "processing_status": "fallback",
            "processing_error": error,
            "published_at": article.get("published_at") or article.get("date") or "",
            "title_en": title,
            "tldr": tagline[:80],
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
                "evidence_label": "",
            },
        })


# Backward-compatible alias for any external importer.
OllamaProcessor = LLMProcessor
