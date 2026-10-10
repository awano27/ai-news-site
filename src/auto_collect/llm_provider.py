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
from dataclasses import dataclass
from typing import List, Optional
from time import monotonic, sleep
from threading import Lock, local

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

    def _ensure_pace(self) -> None:
        if getattr(self, "_pace_lock", None) is None:
            self._pace_lock = Lock()
            self._next_allowed = 0.0
            self._dispatch_after = 0.0
            self._cooldown_until = 0.0
            self._waited = 0.0

    def _env_float(self, name: str) -> Optional[float]:
        raw = os.environ.get(name)
        if raw is None or not str(raw).strip():
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    def _max_attempts(self) -> int:
        raw = os.environ.get("LLM_MAX_RETRIES", "4")
        try:
            retries = int(raw)
        except (TypeError, ValueError):
            retries = 4
        return max(0, retries) + 1

    def _min_interval(self) -> float:
        configured = self._env_float("LLM_MIN_INTERVAL_SEC")
        if configured is not None:
            return max(0.0, configured)
        return 1.5 if self.name == "nvidia" else 0.0

    def _max_total_wait(self) -> float:
        configured = self._env_float("LLM_MAX_TOTAL_WAIT_SEC")
        if configured is None:
            configured = 600.0
        return max(0.0, configured)

    def _await_interval(self, minimum_wait: float = 0.0) -> bool:
        """Reserve a paced slot, rechecking shared cooldowns after sleeping."""
        self._ensure_pace()
        interval = self._min_interval()
        while True:
            with self._pace_lock:
                now = monotonic()
                start = max(now, self._next_allowed, self._cooldown_until)
                delay = max(minimum_wait, start - now)
                start = now + delay
                if self._waited + delay > self._max_total_wait() + 1e-9:
                    return False
                self._waited += delay
                self._next_allowed = start + interval
            if delay > 0:
                sleep(delay)
            minimum_wait = 0.0
            with self._pace_lock:
                # Sleep has reached at least the reserved start. Use the
                # actual wake time if scheduling delayed this worker further.
                now = max(start, monotonic())
                if start >= self._cooldown_until and now >= self._dispatch_after:
                    self._dispatch_after = now + interval
                    self._next_allowed = max(self._next_allowed, self._dispatch_after)
                    return True
                # A cooldown or a late worker invalidated this slot. Reserve
                # another rather than releasing sleeping workers in a burst.

    def _consume_wait(self, seconds: float) -> bool:
        """Publish backoff for every worker; charge its sleep in _await_interval."""
        self._ensure_pace()
        seconds = max(0.0, float(seconds))
        with self._pace_lock:
            # Publish even when this caller cannot retry, so other workers
            # cannot bypass a Retry-After that exceeds the remaining budget.
            self._cooldown_until = max(self._cooldown_until, monotonic() + seconds)
            if self._waited + seconds > self._max_total_wait() + 1e-9:
                return False
        return True

    def _retry_delay(self, response, attempt: int) -> float:
        header = response.headers.get("Retry-After") if response is not None else None
        if header not in (None, ""):
            try:
                return max(0.0, min(float(header), 60.0))
            except (TypeError, ValueError):
                pass
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
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        body = {"model": self.config.model, "messages": messages, "stream": False,
                "max_tokens": max_tokens if max_tokens is not None else 2048}
        if self.config.model == "nvidia/nemotron-3-super-120b-a12b":
            body.update(reasoning_effort="none", temperature=1, top_p=0.95)
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.config.api_key}"}
        attempts = self._max_attempts()
        retryable = {429, 500, 502, 503, 504}
        delay = 0.0
        for attempt in range(attempts):
            if not self._await_interval(delay):
                self.last_error = "wait_budget_exceeded"
                logger.warning("[%s] wait budget exceeded before request", self.name)
                return None
            try:
                response = requests.post(url, json=body, headers=headers,
                                         timeout=timeout or self.config.timeout)
            except (requests.Timeout, requests.ConnectionError):
                self.last_error = "network_error"
                if attempt < attempts - 1:
                    delay = self._retry_delay(None, attempt)
                    if self._consume_wait(delay):
                        logger.warning("[%s] retrying after network error (attempt %s)", self.name, attempt + 1)
                        continue
                logger.warning("[%s] request failed (%s)", self.name, self.last_error)
                return None
            if response.status_code != 200:
                self.last_error = f"http_{response.status_code}"
                # Do not log response bodies or exception strings: either may
                # contain credentials, prompt fragments, or private content.
                logger.warning("[%s] HTTP %s", self.name, response.status_code)
                if response.status_code in retryable and (attempt < attempts - 1 or response.status_code == 429):
                    delay = self._retry_delay(response, attempt)
                    can_wait = self._consume_wait(delay)
                    if can_wait and attempt < attempts - 1:
                        logger.warning("[%s] retrying after %.1fs (attempt %s)", self.name, delay, attempt + 1)
                        continue
                    if not can_wait:
                        logger.warning("[%s] wait budget exceeded during retry", self.name)
                return None
            try:
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

