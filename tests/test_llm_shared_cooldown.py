"""Offline, event-driven regressions for workers sharing one LLM provider."""

from collections import Counter
from threading import Condition, Event, Thread, current_thread
from types import SimpleNamespace

import pytest

from src.auto_collect import llm_provider


def response(status=200, retry_after="10"):
    return SimpleNamespace(
        status_code=status,
        headers={"Retry-After": retry_after},
        json=lambda: {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]},
    )


class Workers:
    """Advance a virtual clock only after all workers have slept or finished."""

    def __init__(self, monkeypatch):
        self.condition = Condition()
        self.now = 0.0
        self.sleeping = {}
        self.results = {}
        self.errors = {}
        self.threads = {}
        self.calls = []
        self.counts = Counter()
        self.closed = False
        self.reply = lambda _prompt, _count: response()
        self.provider = object.__new__(llm_provider.LLMProvider)
        self.provider.config = llm_provider.ProviderConfig(
            "nvidia", "https://example.invalid/v1", "offline-test-key", "test-model"
        )
        self.provider.last_error = "main-thread-error"
        self.provider._ensure_pace()
        monkeypatch.setattr(llm_provider, "monotonic", lambda: self.now)
        monkeypatch.setattr(llm_provider, "sleep", self.sleep)
        monkeypatch.setattr(llm_provider.requests, "post", self.post)
        monkeypatch.setenv("LLM_MAX_RETRIES", "1")
        monkeypatch.setenv("LLM_MIN_INTERVAL_SEC", "1.5")
        monkeypatch.setenv("LLM_MAX_TOTAL_WAIT_SEC", "600")

    def post(self, _url, *, json, **_kwargs):
        prompt = json["messages"][0]["content"]
        with self.condition:
            self.calls.append((prompt, self.now))
            self.counts[prompt] += 1
            count = self.counts[prompt]
        return self.reply(prompt, count)

    def sleep(self, seconds):
        name = current_thread().name
        with self.condition:
            deadline = self.now + seconds
            self.sleeping[name] = deadline
            self.condition.notify_all()
            assert self.condition.wait_for(lambda: self.closed or self.now >= deadline, 5)
            self.sleeping.pop(name)
            if self.closed:
                raise RuntimeError("test workers closed")

    def start(self, name):
        def run():
            try:
                result = (self.provider.chat(name), self.provider.last_error)
                with self.condition:
                    self.results[name] = result
            except BaseException as exc:
                with self.condition:
                    self.errors[name] = exc
            finally:
                with self.condition:
                    self.condition.notify_all()

        self.threads[name] = Thread(target=run, name=name, daemon=True)
        self.threads[name].start()

    def wait_for(self, predicate):
        with self.condition:
            assert self.condition.wait_for(lambda: predicate() or self.errors, 5), (
                self.now, self.sleeping, self.results
            )
            assert not self.errors, self.errors

    def settled(self, name):
        self.wait_for(lambda: name in self.results or self.sleeping.get(name, -1) > self.now)

    def advance(self, now):
        with self.condition:
            assert now >= self.now
            self.now = now
            self.condition.notify_all()

    def finish(self):
        while len(self.results) < len(self.threads):
            for name in self.threads:
                self.settled(name)
            if len(self.results) < len(self.threads):
                self.advance(min(self.sleeping.values()))
        for thread in self.threads.values():
            thread.join(5)
            assert not thread.is_alive()

    def close(self):
        with self.condition:
            self.closed = True
            self.condition.notify_all()
        for thread in self.threads.values():
            thread.join(5)


@pytest.fixture
def workers(monkeypatch):
    workers = Workers(monkeypatch)
    yield workers
    workers.close()


@pytest.mark.parametrize("status", [429, 503])
def test_retry_after_blocks_new_workers_and_retains_pacing(workers, status):
    workers.reply = lambda prompt, count: response(status if prompt == "limited" and count == 1 else 200)
    workers.start("limited")
    workers.settled("limited")
    workers.start("newcomer")
    workers.settled("newcomer")

    assert workers.sleeping["newcomer"] >= 10
    workers.finish()
    later_calls = sorted(when for _prompt, when in workers.calls[1:])
    assert later_calls[0] >= 10
    assert later_calls[1] - later_calls[0] >= 1.5
    assert all(result == ("ok", "") for result in workers.results.values())
    assert workers.provider.last_error == "main-thread-error"


def test_workers_already_sleeping_recheck_new_cooldown(workers):
    entered, release = Event(), Event()

    def reply(prompt, count):
        if prompt == "limited" and count == 1:
            entered.set()
            assert release.wait(5)
            return response(429)
        return response()

    workers.reply = reply
    workers.start("limited")
    assert entered.wait(5)
    try:
        workers.start("queued-a")
        workers.settled("queued-a")
        workers.start("queued-b")
        workers.settled("queued-b")
        assert workers.sleeping == {"queued-a": 1.5, "queued-b": 3.0}
    finally:
        release.set()
    workers.settled("limited")
    workers.advance(1.5)
    workers.settled("queued-a")

    assert "queued-a" not in workers.results
    assert workers.sleeping["queued-a"] >= 10
    workers.finish()
    later_calls = sorted(when for _prompt, when in workers.calls[1:])
    assert later_calls[0] >= 10
    assert all(b - a >= 1.5 for a, b in zip(later_calls, later_calls[1:]))


def test_repeated_cooldown_extends_waiting_workers(workers, monkeypatch):
    monkeypatch.setenv("LLM_MIN_INTERVAL_SEC", "0")
    entered, release = Event(), Event()

    def reply(prompt, count):
        if prompt == "second" and count == 1:
            entered.set()
            assert release.wait(5)
        return response(429 if count == 1 else 200)

    workers.reply = reply
    workers.start("second")
    assert entered.wait(5)
    try:
        workers.start("first")
        workers.settled("first")
        workers.advance(4)
    finally:
        release.set()
    workers.settled("second")
    workers.advance(10)
    workers.settled("first")

    assert "first" not in workers.results
    assert workers.sleeping["first"] == 14
    workers.finish()
    assert [when for _prompt, when in workers.calls[2:]] == [14, 14]


@pytest.mark.parametrize("retry_budget, wait_budget", [("0", "600"), ("1", "5")])
def test_exhausted_retry_still_protects_other_workers(workers, monkeypatch, retry_budget, wait_budget):
    monkeypatch.setenv("LLM_MAX_RETRIES", retry_budget)
    monkeypatch.setenv("LLM_MAX_TOTAL_WAIT_SEC", wait_budget)
    workers.reply = lambda prompt, _count: response(429 if prompt == "limited" else 200)
    workers.start("limited")
    workers.wait_for(lambda: "limited" in workers.results)
    assert workers.results["limited"] == (None, "http_429")
    workers.start("newcomer")
    workers.settled("newcomer")

    assert workers.calls == [("limited", 0)]
    if wait_budget == "5":
        assert workers.results.get("newcomer") == (None, "wait_budget_exceeded")
        assert workers.provider._waited == 0
    else:
        assert workers.sleeping["newcomer"] >= 10
    workers.finish()


def test_shared_wait_budget_counts_cooldown_for_each_waiter(workers, monkeypatch):
    monkeypatch.setenv("LLM_MIN_INTERVAL_SEC", "0")
    monkeypatch.setenv("LLM_MAX_TOTAL_WAIT_SEC", "19")
    workers.reply = lambda prompt, count: response(429 if prompt == "limited" and count == 1 else 200)
    workers.start("limited")
    workers.settled("limited")
    workers.start("newcomer")
    workers.settled("newcomer")

    assert workers.results["newcomer"] == (None, "wait_budget_exceeded")
    assert workers.provider._waited == 10
    workers.finish()
    assert workers.calls == [("limited", 0), ("limited", 10)]
    assert workers.results["limited"] == ("ok", "")
    assert workers.provider.last_error == "main-thread-error"


def test_shared_wait_budget_allows_its_exact_boundary(workers, monkeypatch):
    monkeypatch.setenv("LLM_MIN_INTERVAL_SEC", "0")
    monkeypatch.setenv("LLM_MAX_TOTAL_WAIT_SEC", "20")
    workers.reply = lambda prompt, count: response(429 if prompt == "limited" and count == 1 else 200)
    workers.start("limited")
    workers.settled("limited")
    workers.start("newcomer")
    workers.settled("newcomer")

    assert workers.provider._waited == 20
    workers.finish()
    assert [when for _prompt, when in workers.calls[1:]] == [10, 10]
    assert all(result == ("ok", "") for result in workers.results.values())


def test_late_wakeups_after_cooldown_do_not_burst(workers):
    workers.reply = lambda prompt, count: response(429 if prompt == "limited" and count == 1 else 200)
    workers.start("limited")
    workers.settled("limited")
    workers.start("newcomer")
    workers.settled("newcomer")
    workers.advance(20)
    workers.finish()

    later_calls = sorted(when for _prompt, when in workers.calls[1:])
    assert later_calls[0] == 20
    assert later_calls[1] - later_calls[0] >= 1.5


@pytest.mark.parametrize("missing", ["model", "api_key", "entitlement"])
def test_production_safeguards_still_prevent_requests(workers, monkeypatch, missing):
    monkeypatch.delenv("NVIDIA_PRODUCTION_USE_CONFIRMED", raising=False)
    config = llm_provider.ProviderConfig(
        "nvidia", "https://example.invalid/v1", "offline-test-key", "test-model"
    )
    if missing != "entitlement":
        setattr(config, missing, "")
    provider = llm_provider.LLMProvider(config)

    assert not provider.available
    assert provider.last_error == {
        "model": "model_not_configured",
        "api_key": "api_key_missing",
        "entitlement": "production_entitlement_unverified",
    }[missing]
    assert workers.calls == []
