"""HN keyword matching is whole-word; rows the collector sent without a body stay outside the exclusion ratio."""
from datetime import date, datetime, timezone

from src.auto_collect.collectors import hn_collector
from src.auto_collect.processor import LLMProcessor
from src.auto_collect.quality import failure_reason, filter_publishable

# Hacker News titles collected in October 2026 (daily_candidate logs and
# daily-news/data.json quality.excluded).
AI_STORIES = {
    'OpenAI fires three safety researchers for "mishandling research information"':
        'https://techcrunch.com/2026/10/08/fired-openai-safety-researchers-dispute-misconduct-claims-warn-of-chilling-effect',
    'Publish fake stats, get cited in LLMs':
        'https://peec.ai/blog/publish-stats-get-cited-the-tactic-that-put-my-data-all-over-the-web',
    "Wikipedia's Cleanup of AI-Generated Content":
        'https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup',
    'Building an AI-native engineering org':
        'https://twitter.com/sgondala2/status/2115832070274723875',
    'A 10-year-old CNN outperforms frontier LLMs for skin cancer diagnosis':
        'https://lynchlab.net/llm-skin-cancer',
    'ChatGPT Keeps Telling People 404 Media Can Solve Their Tech Support Problems':
        'https://404media.co/chatgpt-keeps-telling-people-404-media-can-solve-their-tech-support-problems',
    'Why are coding agents so dumb?':
        'https://mtlynch.io/why-are-coding-agents-so-dumb',
    'Why are good developers so wary of agentic development?':
        'https://martinfowler.com/rachels-ramblings/good-devs-wary.html',
    'Fixing Tool-Call Accuracy in vLLM':
        'https://ubicloud.com/blog/fixing-tool-call-accuracy-in-vllm',
    'US Reps Lead Democratic Resolution Opposing A.I. Bubble Bailout for Big Tech':
        'https://progressives.house.gov/2026/10/reps-casar-waters-lead-democratic-resolution-opposing-a-i-bubble-bailout-for-big-tech-commit-to-protecting-american-people-instead',
    'Show HN: I Turned DOOM into a Transformer':
        'https://github.com/mottopanikeiku/doomformer',
    'Gemini 4 Carbon':
        'https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon',
    'Backdoor in Claude Code for VS Code extension on the Cursor Marketplace':
        'https://phorion.io/blog/offical-claude-code-vsx-compromise',
    "Timestral: Mistral's time-series foundation models":
        'https://mistral.ai/news/timestral',
    'Compromised LiteLLM 1.107.0 on PyPI Installs a Credential Stealer and Backdoor':
        'https://safedep.io/litellm-pypi-compromise-credential-stealer-backdoor',
}
NOT_AI_STORIES = {
    'Jailbreaking the Switch 2': 'https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb',
    'Railway Security Disclosure': 'https://blog.railway.com/p/security-disclosure-wednesday-october-21st',
    'Airbnb bans making guests do dishes and take out the trash': 'https://theverge.com/tech/1015844/airbnb-chores-house-rules-update',
    'Jared Kushner Hacked Phone Reveals Secret Negotiations, Millions in Transactions':
        'https://vanityfair.com/story/jared-kushner-hacked-phone-secret-negotiations',
    'I paid people to try and follow my README': 'https://shkspr.mobi/blog/2026/10/i-paid-people-to-try-and-follow-my-readme',
    "Starlink limit hits Ukraine's drones":
        'https://defence24.com/geopolitics/starlink-limit-hits-ukraines-drones-the-battlefield-depends-on-spacex',
    "Postgres isn't slow, your storage is":
        'https://clickhouse.com/blog/posette-talk-recap-postgres-isnt-slow-your-storage-is',
    'Pico CSS is no longer maintained': 'https://github.com/picocss/pico/discussions/754',
    'AO3 Down for Maintenance': 'https://otwstatus.org',
    'Through Captain Jean-Luc Picard, Patrick Stewart taught us the measure of a man':
        'https://bostonglobe.com/2026/10/29/metro/patrick-stewart-picard-star-trek-the-next-generation',
    'Documents add to evidence in climate deception case against ExxonMobil':
        'https://insideclimatenews.org/news/07102026/exxonmobil-climate-deception-new-evidence',
    'Nine-Inch Snails': 'https://theatlantic.com/science/2026/10/giant-african-snails-florida-invasion/688850',
}


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 10, 31, 21, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


def _collect(monkeypatch, stories):
    monkeypatch.setattr(hn_collector, 'datetime', FrozenDatetime)
    posted = int(datetime(2026, 10, 31, 18, tzinfo=timezone.utc).timestamp())
    items = {i: {'title': title, 'url': url, 'score': 100, 'time': posted}
             for i, (title, url) in enumerate(stories.items(), 1)}

    class Response:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    class Session:
        def get(self, url, **kwargs):
            if 'topstories' in url:
                return Response(list(items))
            return Response(items[int(url.rsplit('/', 1)[1].split('.')[0])])

    collector = hn_collector.HNAutoCollector()
    collector.session = Session()
    monkeypatch.setattr(collector, '_rate_limit', lambda: None)
    return [row['name'] for row in collector.collect(date(2026, 11, 1))]


def test_hn_keeps_ai_stories_and_drops_substring_matches(monkeypatch):
    mixed = {}
    for pair in zip(AI_STORIES.items(), NOT_AI_STORIES.items()):
        mixed.update(pair)
    mixed.update(AI_STORIES)
    assert sorted(_collect(monkeypatch, mixed)) == sorted(AI_STORIES)


def test_keyword_match_is_case_insensitive_and_survives_hyphens_and_plurals():
    assert hn_collector.is_ai_story('GPT-5 is here', 'https://example.com/post')
    assert hn_collector.is_ai_story('AI-powered search', 'https://example.com/post')
    assert hn_collector.is_ai_story('What LLMs cannot do', 'https://example.com/post')
    assert hn_collector.is_ai_story('openai cli', 'https://example.com/post')
    assert hn_collector.is_ai_story('Fine-tuning on a laptop', 'https://example.com/post')
    assert not hn_collector.is_ai_story('Raise your storage game', 'https://example.com/garage-sale')


class NeverCalled:
    available = True
    name = 'test'

    def chat(self, prompt):
        raise AssertionError('a headline-only row must not reach the model')


def _good(i):
    return {'title': f'記事{i}の見出し', 'summary': '新しい言語モデルを公開しました。開発者は公式資料を確認できます。',
            'url': f'https://example.com/n{i}', 'source': 'Official' if i % 2 == 0 else 'Other',
            'processing_status': 'llm'}


def _hn_rows(count):
    processor = LLMProcessor(NeverCalled())
    return [processor._process_one({'name': f'HN story {i}', 'tagline': f'HN story {i}', 'source': 'hn',
                                    'links': {'official': f'https://news.example/{i}'}})
            for i in range(count)]


def _failed(i, error):
    row = _good(i)
    row.update(title=f'bad {i}', summary='English fallback', processing_status='fallback', processing_error=error)
    return row


def test_rows_without_a_source_body_are_excluded_but_outside_the_ratio():
    hn = _hn_rows(15)
    assert all(row['processing_error'] == 'source_context_missing' for row in hn)
    rows = [_good(i) for i in range(100)] + hn + [_failed(100 + i, 'invalid_japanese') for i in range(11)]
    kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'passed', quality['errors']
    assert len(kept) == 100 and not any(row.get('processing_error') for row in kept)
    assert quality['input_count'] == 126
    assert quality['excluded_count'] == len(quality['excluded']) == 26
    assert quality['ineligible_count'] == 15
    assert quality['excluded_ratio'] == round(11 / 111, 3)
    assert quality['max_excluded_ratio'] == 0.20
    listed = {row['url']: row['errors'] for row in quality['excluded']}
    assert all(listed[row['url']] for row in hn)


def test_a_thin_day_is_not_held_by_body_less_rows_alone():
    rows = [_good(i) for i in range(4)] + _hn_rows(2)
    kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'passed', quality['errors']
    assert len(kept) == 4
    assert quality['excluded_count'] == 2
    assert quality['excluded_ratio'] == 0.0


def test_generation_failures_still_count_and_stay_transient():
    rows = [_good(i) for i in range(100)] + _hn_rows(15) + [_failed(100 + i, 'http_503') for i in range(30)]
    _kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'failed'
    assert any(err == 'too many excluded articles: 30/130 > 20%' for err in quality['errors'])
    assert failure_reason(rows, quality) == 'transient_generation_failed'


def test_minimum_count_hold_from_a_provider_outage_stays_transient():
    rows = [_good(i) for i in range(2)] + _hn_rows(12) + [_failed(10 + i, 'http_429') for i in range(4)]
    _kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'failed'
    assert any('minimum' in err for err in quality['errors'])
    assert failure_reason(rows, quality) == 'transient_generation_failed'
