"""AI Benchmark / Leaderboard collector (LMSYS, Open LLM Leaderboard)."""

import logging
import re
from datetime import date
from typing import List, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# Public endpoints
LMSYS_URL = "https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard"
OPEN_LLM_URL = "https://huggingface.co/api/spaces/open-llm-leaderboard/open_llm_leaderboard"


class BenchmarkCollector:
    """Collect AI benchmark data from public leaderboards."""

    def collect(self, target_date: Optional[date] = None) -> List[Dict]:
        """Collect latest benchmark highlights."""
        results = []

        # Fetch from HuggingFace API for trending models
        try:
            results.extend(self._fetch_trending_models())
        except Exception as e:
            logger.warning(f"[Benchmark] HF trending failed: {e}")

        logger.info(f"[Benchmark] Collected {len(results)} benchmark entries")
        return results

    def _fetch_trending_models(self) -> List[Dict]:
        """Fetch trending models from HuggingFace."""
        models = []
        try:
            resp = requests.get(
                "https://huggingface.co/api/models",
                params={
                    "sort": "likes7d",
                    "direction": "-1",
                    "limit": 15,
                },
                timeout=15,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

            for model in data:
                model_id = model.get("id", "")
                downloads = model.get("downloads", 0)
                likes = model.get("likes", 0)
                tags = model.get("tags", [])
                pipeline_tag = model.get("pipeline_tag", "")

                models.append({
                    "name": model_id,
                    "tagline": f"HuggingFace Trending Model ({pipeline_tag})",
                    "url": f"https://huggingface.co/{model_id}",
                    "downloads": downloads,
                    "likes": likes,
                    "tags": tags,
                    "pipeline_tag": pipeline_tag,
                    "source": "hf_trending",
                })

        except Exception as e:
            logger.warning(f"[Benchmark] HF API error: {e}")

        return models
