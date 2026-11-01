"""Hacker News AI-filtered auto-collector."""

import logging
import re
from datetime import date, datetime, timezone, timedelta
from typing import List, Dict, Optional

from scripts.collectors.hn import HackerNewsCollector, HN_API_BASE, ITEM_URL, TOP_STORIES_URL
from ..config import HN_MIN_SCORE, HN_MAX_STORIES, HN_AI_KEYWORDS

logger = logging.getLogger(__name__)

# A substring test let "ai" match jail, railway and Airbnb, and "rag" match
# storage. Digits may follow (GPT5, AI2) and so may a plural s (LLMs, agents).
AI_KEYWORD = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(re.escape(kw) for kw in HN_AI_KEYWORDS) + r")s?(?![a-z])",
    re.IGNORECASE,
)


def is_ai_story(title: str, url: str) -> bool:
    return bool(AI_KEYWORD.search(f"{title} {url}"))


class HNAutoCollector(HackerNewsCollector):
    """Hacker News collector filtered for AI-related stories."""

    MAX_STORIES = HN_MAX_STORIES
    MIN_SCORE = HN_MIN_SCORE

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """Collect AI-related stories from HN top stories."""
        if target_date is None:
            target_date = date.today()

        # The previous implementation computed but never applied its window.
        # Bound both sides in UTC, with historical edition boundaries in JST.
        jst = timezone(timedelta(hours=9))
        edition_end = datetime.combine(target_date + timedelta(days=1),
                                       datetime.min.time()).replace(tzinfo=jst)
        end_ts = min(datetime.now(timezone.utc).timestamp(), edition_end.timestamp())
        start_ts = end_ts - 28 * 60 * 60

        logger.info(f"[HN] Collecting AI stories for {target_date}")

        tools = []
        try:
            self._rate_limit()
            response = self.session.get(TOP_STORIES_URL, timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:self.MAX_STORIES * 3]

            for story_id in story_ids:
                if len(tools) >= self.MAX_STORIES:
                    break

                self._rate_limit()
                try:
                    item_resp = self.session.get(ITEM_URL.format(id=story_id), timeout=10)
                    item_resp.raise_for_status()
                    item = item_resp.json()

                    if not item:
                        continue

                    title = item.get("title", "")
                    url = item.get("url", "")
                    score = item.get("score", 0)
                    item_time = item.get("time", 0)
                    if not isinstance(item_time, (int, float)) or not start_ts <= item_time <= end_ts:
                        continue

                    if not is_ai_story(title, url):
                        continue
                    if score < self.MIN_SCORE:
                        continue
                    if not url:
                        continue

                    hn_url = f"https://news.ycombinator.com/item?id={story_id}"

                    tool = self.create_tool_dict(
                        name=title[:200],
                        tagline=title,
                        official_url=url,
                        categories=self._categorize_from_content(title, url),
                        source_rank=len(tools) + 1,
                        source_votes=score,
                        extra_links={"hn": hn_url}
                    )
                    tool["hn_score"] = score
                    tool["published_at"] = datetime.fromtimestamp(item_time, timezone.utc).isoformat()
                    tools.append(tool)

                except Exception as e:
                    logger.debug(f"[HN] Error processing {story_id}: {e}")

            logger.info(f"[HN] Collected {len(tools)} AI stories")

        except Exception as e:
            logger.error(f"[HN] Error: {e}")

        return tools
