import json
import pytest
from src.auto_collect.quality import article_errors, filter_publishable
from src.auto_collect.processor import LLMProcessor
from scripts.check_daily_publication import is_japanese, narrative_title


def row(**changes):
    value = dict(title="新しいAI技術を公開", summary="新しいAI技術を公開しました。公式資料で詳細を確認できます。",
                 source="Official", url="https://example.com/a", processing_status="llm")
    value.update(changes)
    return value


def test_english_news_headline_is_rejected_before_rendering():
    value = row(title="OpenFatigue - Open is the new closed")
    assert narrative_title(value) and not is_japanese(value["title"])
    assert "Japanese headline missing" in article_errors(value)
    kept, report = filter_publishable([value, row(url="https://example.com/b")], max_excluded_ratio=1)
    assert len(kept) == 1 and report["excluded_count"] == 1
    assert report["excluded"][0]["errors"] == ["Japanese headline missing"]


@pytest.mark.parametrize("source", ["GitHub Trending", "HuggingFace Trending", "Hugging Face"])
def test_repository_and_model_names_keep_the_existing_exception(source):
    assert article_errors(row(title="owner/model-id", source=source)) == []


def test_x_original_title_keeps_the_existing_exception_and_relevance_gate():
    assert article_errors(row(title="Original English post", x_curated=True, ai_related=True)) == []
    assert "not AI-related" in article_errors(row(title="Original English post", x_curated=True, ai_related=False))


def test_processor_retries_english_title_without_accepting_it_as_japanese():
    class Provider:
        available=True
        name="test"
        def __init__(self): self.prompts=[]
        def chat(self,prompt):
            self.prompts.append(prompt)
            return json.dumps({"title_ja": "OpenFatigue" if len(self.prompts)==1 else "オープンなAI技術の課題を整理",
                               "summary": row()["summary"], "score": 70})
    provider=Provider()
    result=LLMProcessor(provider)._process_one({"name":"OpenFatigue", "description":"public source", "source":"Official", "links":{"official":"https://example.com/a"}})
    assert len(provider.prompts)==2 and "title_ja" in provider.prompts[1]
    assert result["processing_status"]=="llm" and is_japanese(result["title"])


def test_processor_does_not_mark_repeated_english_headline_as_verified():
    class Provider:
        available=True
        name="test"
        def chat(self,_):return json.dumps({"title_ja":"OpenFatigue", "summary":row()["summary"], "score":70})
    result=LLMProcessor(Provider())._process_one({"name":"OpenFatigue", "description":"public source", "source":"Official", "links":{"official":"https://example.com/a"}})
    assert result["processing_status"]=="fallback"
    assert article_errors(result)
