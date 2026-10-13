from src.auto_collect.processor import LLMProcessor
from src.auto_collect.quality import article_errors


class NeverCalled:
    available = True
    name = 'test'
    def chat(self, prompt):
        raise AssertionError('headline-only input must not call the model')


def test_hn_headline_is_not_source_body():
    result = LLMProcessor(NeverCalled())._process_one({
        'name': 'OpenFatigue - Open is the new closed',
        'tagline': 'OpenFatigue - Open is the new closed',
        'source': 'hn', 'links': {'official': 'https://openfatigue.ai'},
    })
    assert result['processing_error'] == 'source_context_missing'
    assert result['processing_status'] == 'fallback'
    assert article_errors(result)


def test_rss_headline_only_is_also_held():
    result = LLMProcessor(NeverCalled())._process_one({
        'name': 'AI news', 'description': '  AI   news ', 'source': 'RSS',
        'links': {'official': 'https://example.com/news'},
    })
    assert result['processing_error'] == 'source_context_missing'


def test_empty_body_is_held():
    result = LLMProcessor(NeverCalled())._process_one({
        'name': 'AI news', 'description': '', 'source': 'RSS',
        'links': {'official': 'https://example.com/news'},
    })
    assert result['processing_error'] == 'source_context_missing'
