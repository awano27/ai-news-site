"""Retry, pacing, and wait-budget behavior for LLM chat calls."""
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import threading

from src.auto_collect import llm_provider


def _ok(content='ok'):
    return SimpleNamespace(
        status_code=200,
        headers={},
        json=lambda: {'choices': [{'message': {'content': content}, 'finish_reason': 'stop'}]},
    )


def _status(code, headers=None):
    return SimpleNamespace(status_code=code, headers=headers or {}, text='unit-test-key secret body')


def _provider(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(llm_provider.random, 'uniform', lambda _start, _end: 0)
    provider = object.__new__(llm_provider.LLMProvider)
    provider.config = llm_provider.ProviderConfig('test', 'https://example.com/v1', 'unit-test-key', 'model')
    return provider


def test_retryable_statuses_use_exponential_backoff_then_succeed(monkeypatch):
    sleeps = []
    monkeypatch.setattr(llm_provider, 'sleep', lambda seconds: sleeps.append(seconds))
    responses = [_status(429), _status(503), _status(500), _ok('要約できた')]
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_args, **_kwargs: responses.pop(0))
    provider = _provider(monkeypatch)
    assert provider._call([{'role': 'user', 'content': 'hello'}]) == '要約できた'
    assert sleeps == [2, 4, 8]
    assert provider.last_error == ''


def test_retry_after_header_is_honored_and_capped(monkeypatch):
    sleeps = []
    monkeypatch.setattr(llm_provider, 'sleep', lambda seconds: sleeps.append(seconds))
    responses = [_status(429, {'Retry-After': '5'}), _ok()]
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_args, **_kwargs: responses.pop(0))
    provider = _provider(monkeypatch)
    assert provider._call([]) == 'ok'
    assert sleeps == [5]

    sleeps.clear()
    responses = [_status(503, {'Retry-After': '120'}), _ok()]
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_args, **_kwargs: responses.pop(0))
    provider = _provider(monkeypatch)
    assert provider._call([]) == 'ok'
    assert sleeps == [60]


def test_retry_exhaustion_returns_none_without_logging_secrets(monkeypatch, caplog):
    sleeps = []
    calls = []
    monkeypatch.setattr(llm_provider, 'sleep', lambda seconds: sleeps.append(seconds))

    def post(*_args, **_kwargs):
        calls.append(1)
        return _status(429)

    monkeypatch.setattr(llm_provider.requests, 'post', post)
    provider = _provider(monkeypatch, LLM_MAX_RETRIES='4')
    assert provider._call([]) is None
    assert calls == [1, 1, 1, 1, 1]
    assert sleeps == [2, 4, 8, 16]
    assert provider.last_error == 'http_429'
    assert 'secret body' not in caplog.text
    assert 'unit-test-key' not in caplog.text


def test_second_call_waits_for_the_minimum_interval(monkeypatch):
    clock = {'now': 1000.0}
    sleeps = []
    posts = []

    def sleep(seconds):
        sleeps.append(seconds)
        clock['now'] += seconds

    monkeypatch.setattr(llm_provider, 'monotonic', lambda: clock['now'])
    monkeypatch.setattr(llm_provider, 'sleep', sleep)
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_args, **_kwargs: posts.append(clock['now']) or _ok())
    provider = _provider(monkeypatch, LLM_MIN_INTERVAL_SEC='1.5')
    assert provider._call([]) == 'ok'
    assert provider._call([]) == 'ok'
    assert sleeps == [1.5]
    assert posts == [1000.0, 1001.5]


def test_minimum_interval_is_reserved_across_threads(monkeypatch):
    sleeps = []
    lock = threading.Lock()
    monkeypatch.setattr(llm_provider, 'monotonic', lambda: 5000.0)

    def sleep(seconds):
        with lock:
            sleeps.append(seconds)

    monkeypatch.setattr(llm_provider, 'sleep', sleep)
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_args, **_kwargs: _ok())
    provider = _provider(monkeypatch, LLM_MIN_INTERVAL_SEC='1.5')
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda _index: provider._call([]), range(3)))
    assert sorted(sleeps) == [1.5, 3.0]


def test_total_wait_cap_fails_later_calls_without_sleeping(monkeypatch):
    sleeps = []
    calls = []
    monkeypatch.setattr(llm_provider, 'sleep', lambda seconds: sleeps.append(seconds))

    def post(*_args, **_kwargs):
        calls.append(1)
        return _status(429, {'Retry-After': '30'})

    monkeypatch.setattr(llm_provider.requests, 'post', post)
    provider = _provider(monkeypatch, LLM_MAX_TOTAL_WAIT_SEC='5', LLM_MIN_INTERVAL_SEC='0')
    assert provider._call([]) is None
    assert provider._call([]) is None
    assert sleeps == []
    assert calls == [1]
    assert provider.last_error == 'wait_budget_exhausted'
