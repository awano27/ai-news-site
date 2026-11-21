"""Content retries for translations that miss the Japanese quality checks.

The publication gate stays strict. These tests mock the LLM and check that a
bad title or summary is retried, that a still-bad article stays unpublished,
and that a good first answer is not sent again.
"""
import json
import logging

from src.auto_collect.processor import LLMProcessor
from src.auto_collect.quality import article_errors, filter_publishable


GOOD_SUMMARY = "ChatGPTとCodexの利用上限が一つにまとまりました。公式ヘルプで確認できます。"
GOOD = {
    "title_ja": "ChatGPTとCodexの利用上限が統合された",
    "summary": GOOD_SUMMARY,
    "score": 70,
}
BAD = {
    "title_ja": "ChatGPT and Codex usage limits merging",
    "summary": "The limits are merging into one pool.",
    "score": 40,
}
ARTICLE = {
    "name": "ChatGPT and Codex usage limits merging",
    "description": "OpenAI is merging ChatGPT and Codex usage limits into one pool.",
    "source": "Official",
    "rss_source": "Official",
    "links": {"official": "https://help.openai.com/en/articles/limits"},
}


def _dumps(payload):
    return json.dumps(payload, ensure_ascii=False)


def _good_row():
    return {
        "title": "新しいモデルを公開",
        "summary": "新しい言語モデルを公開しました。開発者は公式資料を確認できます。",
        "url": "https://example.com/good",
        "source": "Other",
        "processing_status": "llm",
    }


class Scripted:
    available = True
    last_error = ""

    def __init__(self, replies, *, name="ollama", model="gemma3:4b"):
        self.name = name
        self.config = type("Config", (), {"model": model})()
        self._replies = list(replies)
        self.prompts = []
        self.options = []

    def set_request_options(self, *, temperature=None, model=None):
        self.options.append((temperature, model))

    def chat(self, prompt):
        self.prompts.append(prompt)
        reply = self._replies.pop(0)
        if isinstance(reply, tuple):
            self.last_error, reply = reply
        else:
            self.last_error = ""
        return reply


def test_translation_succeeds_on_the_second_retry_and_passes_quality(caplog):
    provider = Scripted([_dumps(BAD), _dumps(BAD), _dumps(GOOD)])
    processor = LLMProcessor(provider)
    caplog.set_level(logging.INFO)
    row = processor._process_one(ARTICLE)

    assert len(provider.prompts) == 3
    assert "前の応答は必須条件を満たしていません" not in provider.prompts[0]
    assert "前の応答は必須条件を満たしていません" in provider.prompts[1]
    assert "前の応答は必須条件を満たしていません" in provider.prompts[2]
    assert provider.options[0] == (None, None)
    assert provider.options[1] == (0.2, None)
    assert provider.options[2] == (0.7, None)
    assert row["processing_status"] == "llm"
    assert row["title"] == GOOD["title_ja"]
    assert row["summary"] == GOOD_SUMMARY
    assert article_errors(row) == []
    kept, quality = filter_publishable([row], min_articles=1, min_sources=1)
    assert kept == [row]
    assert quality["status"] == "passed"
    assert quality["excluded"] == []
    stats = processor.translation_retry_stats()
    assert stats["ok_first"] == 0
    assert stats["retried"] == 1
    assert stats["recovered"] == 1
    assert stats["dropped"] == 0
    assert stats["extra_calls"] == 2
    processor.log_translation_retry_summary()
    assert "translation retry 1/2" in caplog.text
    assert "translation retry 2/2" in caplog.text
    assert "reason=invalid_japanese" in caplog.text
    assert "temperature=0.2" in caplog.text
    assert "temperature=0.7" in caplog.text
    assert "translation retry recovered" in caplog.text
    assert "recovered=1" in caplog.text
    assert "dropped=0" in caplog.text


def test_translation_that_never_passes_stays_excluded(caplog):
    provider = Scripted([_dumps(BAD), _dumps(BAD), _dumps(BAD)])
    processor = LLMProcessor(provider)
    caplog.set_level(logging.INFO)
    row = processor._process_one(ARTICLE)

    assert len(provider.prompts) == 3
    assert row["processing_status"] == "fallback"
    assert row["processing_error"] == "invalid_japanese"
    assert row["title"] == ARTICLE["name"]
    assert article_errors(row)
    kept, quality = filter_publishable(
        [_good_row(), row], min_articles=1, min_sources=1, max_excluded_ratio=1,
    )
    assert quality["status"] == "passed"
    assert [item["url"] for item in kept] == ["https://example.com/good"]
    assert quality["excluded"][0]["url"] == ARTICLE["links"]["official"]
    assert "Japanese headline missing" in quality["excluded"][0]["errors"]
    assert "Japanese summary missing or invalid" in quality["excluded"][0]["errors"]
    assert "fallback or unverified processing" in quality["excluded"][0]["errors"]
    stats = processor.translation_retry_stats()
    assert stats["recovered"] == 0
    assert stats["dropped"] == 1
    assert stats["retried"] == 1
    assert stats["extra_calls"] == 2
    processor.log_translation_retry_summary()
    assert "translation dropped" in caplog.text
    assert "dropped=1" in caplog.text
    assert "recovered=0" in caplog.text


def test_valid_first_translation_is_not_retried():
    provider = Scripted([_dumps(GOOD), _dumps(BAD)])
    processor = LLMProcessor(provider)
    row = processor._process_one(ARTICLE)

    assert len(provider.prompts) == 1
    assert provider.options == [(None, None)]
    assert row["processing_status"] == "llm"
    assert article_errors(row) == []
    stats = processor.translation_retry_stats()
    assert stats == {
        "ok_first": 1,
        "retried": 0,
        "recovered": 0,
        "dropped": 0,
        "extra_calls": 0,
        "budget_skipped": 0,
    }


def test_additional_retry_stops_when_the_call_budget_is_zero(monkeypatch):
    monkeypatch.setenv("SUMMARY_RETRY_CALL_BUDGET", "0")
    provider = Scripted([_dumps(BAD), _dumps(BAD), _dumps(GOOD)])
    processor = LLMProcessor(provider)
    row = processor._process_one(ARTICLE)

    assert len(provider.prompts) == 2
    assert row["processing_status"] == "fallback"
    assert article_errors(row)
    stats = processor.translation_retry_stats()
    assert stats["extra_calls"] == 1
    assert stats["budget_skipped"] == 1
    assert stats["recovered"] == 0
    assert stats["dropped"] == 1


def test_last_retry_uses_the_configured_local_fallback_model(monkeypatch):
    monkeypatch.setenv("OLLAMA_FALLBACK_MODEL", "qwen2.5:7b")
    provider = Scripted([_dumps(BAD), _dumps(BAD), _dumps(GOOD)])
    processor = LLMProcessor(provider)
    row = processor._process_one(ARTICLE)

    assert row["processing_status"] == "llm"
    assert provider.options[0] == (None, None)
    assert provider.options[1] == (0.2, None)
    assert provider.options[2] == (0.2, "qwen2.5:7b")
    assert processor.translation_retry_stats()["recovered"] == 1


def test_truncated_response_is_retried_and_can_be_recovered():
    provider = Scripted([("truncated_response", None), _dumps(GOOD)])
    processor = LLMProcessor(provider)
    row = processor._process_one(ARTICLE)

    assert len(provider.prompts) == 2
    assert row["processing_status"] == "llm"
    assert article_errors(row) == []
    assert processor.translation_retry_stats()["recovered"] == 1


def test_transport_failure_is_not_content_retried():
    provider = Scripted([("http_429", None), _dumps(GOOD)])
    processor = LLMProcessor(provider)
    row = processor._process_one(ARTICLE)

    assert len(provider.prompts) == 1
    assert row["processing_status"] == "fallback"
    assert row["processing_error"] == "http_429"
    assert article_errors(row)
    stats = processor.translation_retry_stats()
    assert stats["retried"] == 0
    assert stats["extra_calls"] == 0
    assert stats["dropped"] == 1


def test_listing_keeps_a_japanese_summary_when_the_title_is_the_repo_name():
    summary = "複数のモデルをつないでアプリを作るオープンソースの基盤です。手順は公式リポジトリで確認できます。"
    provider = Scripted([_dumps({"title_ja": "langgenius/dify", "summary": summary, "score": 80})])
    row = LLMProcessor(provider).process_github_repos([{
        "name": "langgenius/dify",
        "url": "https://github.com/langgenius/dify",
        "tagline": "An open-source LLM app development platform.",
        "stars": 50000,
        "forks": 10,
    }])[0]

    assert len(provider.prompts) == 1
    assert row["title"] == "langgenius/dify"
    assert row["summary"] == summary
    assert row["processing_status"] == "llm"
    assert article_errors(row) == []


def test_listing_with_an_english_summary_stays_excluded():
    provider = Scripted([_dumps(BAD), _dumps(BAD), _dumps(BAD)])
    row = LLMProcessor(provider).process_github_repos([{
        "name": "langgenius/dify",
        "url": "https://github.com/langgenius/dify",
        "tagline": "An open-source LLM app development platform.",
        "stars": 50000,
        "forks": 10,
    }])[0]

    assert len(provider.prompts) == 3
    assert row["processing_status"] == "fallback"
    assert "Japanese summary missing or invalid" in article_errors(row)


def test_x_summary_recovers_on_the_second_retry():
    bad = _dumps({"title_ja": "Anthropic blocks training", "summary": "English only.", "ai_related": True})
    good = _dumps({
        "title_ja": "大規模モデルの学習に触れた利用者をAnthropicが止めた",
        "summary": "大規模モデルの学習に関係する操作をした利用者をAnthropicが制限しました。公式の発表で確認できます。",
        "ai_related": True,
    })
    provider = Scripted([bad, bad, good])
    post = {
        "name": "Anthropic blocks users for anything touching training larger models",
        "description": "Anthropic is blocking accounts that try to train larger models.",
        "rss_source": "X (@example)",
        "source": "X",
        "url": "https://x.com/example/status/2116475922190922088",
        "links": {"official": "https://x.com/example/status/2116475922190922088"},
        "x_curated": True,
        "x_tweet_id": "2116475922190922088",
    }
    row = LLMProcessor(provider).process_x_posts([post])[0]

    assert len(provider.prompts) == 3
    assert row["processing_status"] == "llm"
    assert row["ai_related"] is True
    assert article_errors(row) == []


def test_x_post_judged_not_ai_related_is_not_retried():
    reply = _dumps({
        "title_ja": "昼ごはんの写真",
        "summary": "昼ごはんの写真が共有されています。食事の様子が写っています。",
        "ai_related": False,
    })
    provider = Scripted([reply, _dumps(GOOD)])
    post = {
        "name": "lunch photo",
        "description": "A photo of lunch with no AI content.",
        "rss_source": "X (@example)",
        "source": "X",
        "url": "https://x.com/example/status/2",
        "links": {"official": "https://x.com/example/status/2"},
        "x_curated": True,
        "x_tweet_id": "2",
    }
    row = LLMProcessor(provider).process_x_posts([post])[0]

    assert len(provider.prompts) == 1
    assert row["ai_related"] is False
    assert "not AI-related" in article_errors(row)


def test_nvidia_requests_ignore_ollama_retry_options(monkeypatch):
    from src.auto_collect import llm_provider

    captured = {}

    def post(_url, json, headers, timeout):
        captured["body"] = json
        return type("Response", (), {
            "status_code": 200,
            "headers": {},
            "json": lambda self: {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]},
        })()

    monkeypatch.setattr(llm_provider.requests, "post", post)
    provider = object.__new__(llm_provider.LLMProvider)
    provider.config = llm_provider.ProviderConfig(
        "nvidia", "https://integrate.api.nvidia.com/v1", "unit-test-key",
        "nvidia/nemotron-3-super-120b-a12b",
    )
    provider.set_request_options(temperature=0.2, model="qwen2.5:7b")
    assert provider.chat("hello") == "ok"
    assert captured["body"]["model"] == "nvidia/nemotron-3-super-120b-a12b"
    assert captured["body"]["temperature"] == 1
    assert captured["body"]["top_p"] == 0.95


def test_ollama_request_uses_retry_temperature_and_fallback_model(monkeypatch):
    from src.auto_collect import llm_provider

    captured = {}

    def post(_url, json, headers, timeout):
        captured["body"] = json
        return type("Response", (), {
            "status_code": 200,
            "headers": {},
            "json": lambda self: {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]},
        })()

    monkeypatch.setattr(llm_provider.requests, "post", post)
    provider = object.__new__(llm_provider.LLMProvider)
    provider.config = llm_provider.ProviderConfig(
        "ollama", "http://127.0.0.1:11434/v1", "ollama", "gemma3:4b",
    )
    provider.set_request_options(temperature=0.7, model="qwen2.5:7b")
    assert provider.chat("hello") == "ok"
    assert captured["body"]["model"] == "qwen2.5:7b"
    assert captured["body"]["temperature"] == 0.7
    assert "reasoning_effort" not in captured["body"]
