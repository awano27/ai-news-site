"""LLM provider abstraction for summarization.

Both supported endpoints implement the OpenAI chat-completions schema, so a
single client class with different base_url / api_key / model values handles
both:

  * Ollama (local, free):
      base_url = http://localhost:11434/v1
      requires Ollama daemon running with OLLAMA_MODEL pulled
  * NVIDIA NIM (cloud, separately verified production entitlement required):
      base_url = https://integrate.api.nvidia.com/v1
      requires env var NVIDIA_API_KEY
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional
from time import sleep
from threading import local

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
        self.last_error = ""
        self.available = self._health_check()

    @property
    def last_error(self) -> str:
        return getattr(getattr(self, "_errors", None), "value", "")

    @last_error.setter
    def last_error(self, value: str) -> None:
        if not hasattr(self, "_errors"):
            self._errors = local()
        self._errors.value = value

    @property
    def name(self) -> str:
        return self.config.name

    def _health_check(self) -> bool:
        # Never silently route a public site to a retired or trial-only default.
        if not self.config.model:
            self.last_error = "model_not_configured"
            logger.warning("[%s] explicit production-authorized model is required", self.name)
            return False
        if not self.config.api_key:
            self.last_error = "api_key_missing"
            return False
        if self.name == "nvidia" and os.environ.get("NVIDIA_PRODUCTION_USE_CONFIRMED") != "true":
            self.last_error = "production_entitlement_unverified"
            logger.warning("[nvidia] production entitlement must be confirmed before publishing API output")
            return False
        text = self._call(
            [{"role": "user", "content": "Reply with OK."}], max_tokens=16, timeout=30,
        )
        if text:
            logger.info("[%s] health-check OK (model=%s)", self.name, self.config.model)
        return bool(text)

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
            self.last_error = "api_key_missing"
            return None
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        body = {"model": self.config.model, "messages": messages, "stream": False,
                "max_tokens": max_tokens if max_tokens is not None else 2048}
        if self.config.model == "nvidia/nemotron-3-super-120b-a12b":
            body.update(reasoning_effort="none", temperature=1, top_p=0.95)
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.config.api_key}"}
        for attempt in range(2):
            try:
                response = requests.post(url, json=body, headers=headers,
                                         timeout=timeout or self.config.timeout)
                if response.status_code != 200:
                    self.last_error = f"http_{response.status_code}"
                    # Do not log response bodies or exception strings: either may
                    # contain credentials, prompt fragments, or private content.
                    logger.warning("[%s] HTTP %s", self.name, response.status_code)
                    if attempt == 0 and response.status_code in (429, 500, 502, 503, 504):
                        try:
                            delay = float(response.headers.get("Retry-After", "2"))
                        except (TypeError, ValueError):
                            delay = 2
                        sleep(max(1, min(delay, 60)))
                        continue
                    return None
                choice = response.json()["choices"][0]
                if choice.get("finish_reason") != "stop":
                    self.last_error = "truncated_response"
                    return None
                content = choice["message"].get("content")
                if not isinstance(content, str) or not content.strip():
                    self.last_error = "empty_response"
                    return None
                self.last_error = ""
                return content
            except (requests.Timeout, requests.ConnectionError):
                self.last_error = "network_error"
                if attempt == 0:
                    sleep(2)
                    continue
            except (KeyError, IndexError, TypeError, ValueError):
                self.last_error = "invalid_response"
            logger.warning("[%s] request failed (%s)", self.name, self.last_error)
            return None
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
            model=os.environ.get("NVIDIA_MODEL", "").strip(),
            timeout=120,
        )
    else:
        raise ValueError(f"unknown provider: {name}")
    return LLMProvider(cfg)
