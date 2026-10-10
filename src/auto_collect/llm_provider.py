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
import random
import threading
from dataclasses import dataclass
from typing import List, Optional
from time import monotonic, sleep
from threading import local

import requests

from .config import OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
DEFAULT_MAX_RETRIES = 4
DEFAULT_MAX_TOTAL_WAIT_SEC = 600.0
NVIDIA_MIN_INTERVAL_SEC = 1.5


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
        self._ensure_pace()
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

    _pace_init_lock = threading.Lock()

    def _ensure_pace(self) -> None:
        if getattr(self, "_pace_ready", False):
            return
        with LLMProvider._pace_init_lock:
            if getattr(self, "_pace_ready", False):
                return
            self._pace_lock = threading.Lock()
            self._next_allowed = 0.0
            self._waited = 0.0
            self._budget_exhausted = False
            retry_raw = os.environ.get("LLM_MAX_RETRIES", "").strip()
            wait_raw = os.environ.get("LLM_MAX_TOTAL_WAIT_SEC", "").strip()
            interval_raw = os.environ.get("LLM_MIN_INTERVAL_SEC", "").strip()
            self._max_retries = int(retry_raw) if retry_raw else DEFAULT_MAX_RETRIES
            self._max_total_wait = float(wait_raw) if wait_raw else DEFAULT_MAX_TOTAL_WAIT_SEC
            if interval_raw:
                self._min_interval = max(0.0, float(interval_raw))
            elif self.config.name == "nvidia":
                self._min_interval = NVIDIA_MIN_INTERVAL_SEC
            else:
                self._min_interval = 0.0
            self._pace_ready = True

    def _await_interval(self) -> bool:
        """Reserve the next call slot. Sleep outside the lock so workers do not queue behind each other."""
        self._ensure_pace()
        with self._pace_lock:
            if self._budget_exhausted:
                return False
            now = monotonic()
            start = max(now, self._next_allowed)
            wait = start - now
            if self._waited + wait > self._max_total_wait:
                self._budget_exhausted = True
                return False
            self._waited += wait
            self._next_allowed = start + self._min_interval
        if wait > 0:
            sleep(wait)
        return True

    def _sleep_within_budget(self, delay: float) -> bool:
        self._ensure_pace()
        delay = max(0.0, float(delay))
        with self._pace_lock:
            if self._budget_exhausted or self._waited + delay > self._max_total_wait:
                self._budget_exhausted = True
                return False
            self._waited += delay
        if delay > 0:
            sleep(delay)
        return True

    def _retry_delay(self, response, attempt: int) -> float:
        header = ""
        try:
            header = str(response.headers.get("Retry-After") or "").strip()
        except (AttributeError, TypeError, ValueError):
            header = ""
        if header:
            try:
                delay = float(header)
            except (TypeError, ValueError):
                delay = -1
            if delay >= 0:
                return min(delay, 60.0)
        return min((2 ** attempt) * 2, 60) + random.uniform(0, 1)

    def _call(
        self,
        messages: List[dict],
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        if not self.config.api_key:
            self.last_error = "api_key_missing"
            return None
        self._ensure_pace()
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        body = {"model": self.config.model, "messages": messages, "stream": False,
                "max_tokens": max_tokens if max_tokens is not None else 2048}
        if self.config.model == "nvidia/nemotron-3-super-120b-a12b":
            body.update(reasoning_effort="none", temperature=1, top_p=0.95)
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.config.api_key}"}
        for attempt in range(self._max_retries + 1):
            if not self._await_interval():
                self.last_error = "wait_budget_exhausted"
                logger.warning("[%s] wait budget exhausted", self.name)
                return None
            try:
                response = requests.post(url, json=body, headers=headers,
                                         timeout=timeout or self.config.timeout)
                if response.status_code != 200:
                    self.last_error = f"http_{response.status_code}"
                    # Do not log response bodies, exception strings, or keys.
                    logger.warning("[%s] HTTP %s attempt %s", self.name, response.status_code, attempt + 1)
                    if response.status_code in RETRYABLE_STATUS and attempt < self._max_retries:
                        delay = self._retry_delay(response, attempt)
                        logger.warning("[%s] waiting %.1fs", self.name, delay)
                        if not self._sleep_within_budget(delay):
                            self.last_error = "wait_budget_exhausted"
                            logger.warning("[%s] wait budget exhausted", self.name)
                            return None
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
                logger.warning("[%s] HTTP network attempt %s", self.name, attempt + 1)
                if attempt == 0 and self._sleep_within_budget(2):
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
