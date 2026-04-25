"""LLM provider abstraction for summarization.

Both supported endpoints implement the OpenAI chat-completions schema, so a
single client class with different base_url / api_key / model values handles
both:

  * Ollama (local, free):
      base_url = http://localhost:11434/v1
      requires Ollama daemon running with OLLAMA_MODEL pulled
  * NVIDIA NIM (cloud, free developer tier from build.nvidia.com):
      base_url = https://integrate.api.nvidia.com/v1
      requires env var NVIDIA_API_KEY
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

import requests

from .config import OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    api_key: str
    model: str
    timeout: int = 120


class LLMProvider:
    """OpenAI chat-completions compatible client.

    Used by `processor.LLMProcessor` for article summarization. Constructor
    runs a one-shot health-check so callers can branch on `.available`
    without retrying the full pipeline per article.
    """

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.available = self._health_check()

    @property
    def name(self) -> str:
        return self.config.name

    def _health_check(self) -> bool:
        try:
            text = self._call(
                [{"role": "user", "content": "ping"}],
                max_tokens=4,
                timeout=30,
            )
            ok = text is not None
            if ok:
                logger.info(f"[{self.name}] health-check OK (model={self.config.model})")
            else:
                logger.warning(f"[{self.name}] health-check failed (no response)")
            return ok
        except Exception as e:
            logger.warning(f"[{self.name}] health-check exception: {e}")
            return False

    def chat(self, prompt: str) -> Optional[str]:
        return self._call(
            [{"role": "user", "content": prompt}],
            timeout=self.config.timeout,
        )

    def _call(
        self,
        messages: List[dict],
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        if not self.config.api_key:
            return None
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        body = {"model": self.config.model, "messages": messages, "stream": False}
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        headers = {"Content-Type": "application/json"}
        # Ollama ignores Authorization but accepting it does no harm.
        headers["Authorization"] = f"Bearer {self.config.api_key}"
        try:
            r = requests.post(url, json=body, headers=headers, timeout=timeout or self.config.timeout)
            if r.status_code != 200:
                logger.warning(f"[{self.name}] HTTP {r.status_code}: {r.text[:200]}")
                return None
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"[{self.name}] request failed: {e}")
            return None


def make_provider(name: str = "ollama") -> LLMProvider:
    """Factory.

    Raises ValueError on unknown name. Returns a provider whose
    `.available` flag indicates whether downstream code should attempt
    LLM processing or fall back to heuristic scoring.
    """
    name = (name or "ollama").lower()
    if name == "ollama":
        cfg = ProviderConfig(
            name="ollama",
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model=OLLAMA_MODEL,
            timeout=OLLAMA_TIMEOUT,
        )
    elif name == "nvidia":
        api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
        if not api_key:
            logger.warning("[nvidia] NVIDIA_API_KEY not set; provider will be unavailable")
        cfg = ProviderConfig(
            name="nvidia",
            base_url=os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            api_key=api_key,
            model=os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"),
            timeout=120,
        )
    else:
        raise ValueError(f"unknown provider: {name}")
    return LLMProvider(cfg)
