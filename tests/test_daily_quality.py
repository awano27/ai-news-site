from copy import deepcopy
from types import SimpleNamespace
import pytest
from src.auto_collect import processor, llm_provider


def article(**changes):
    a={'title':'新しいモデルを公開','summary':'新しい言語モデルを公開しました。開発者は公式資料を確認できます。', 'url':'https://example.com/news','source':'Official','processing_status':'llm'}
    a.update(changes)
    return a


def test_quality_rejects_english_fallback_and_preserves_input():
    from src.auto_collect.quality import validate_articles
    rows=[article(), article(url='https://other.com/a',source='Other',summary='English fallback',processing_status='fallback')]
    before=deepcopy(rows)
    result=validate_articles(rows)
    assert result['status']=='failed'
    assert result['japanese_count']==1
    assert any('fallback' in e for e in result['errors'])
    assert rows==before


def test_quality_requires_actual_article_urls_and_sources():
    from src.auto_collect.quality import validate_articles
    r=validate_articles([article(url='javascript:alert(1)'),article(url='https://other.com/a',source='')])
    assert r['status']=='failed'
    assert any('URL' in e for e in r['errors'])
    assert any('source' in e for e in r['errors'])


def test_quality_does_not_accept_generic_japanese_wrapper_or_chinese_only():
    from src.auto_collect.quality import is_japanese_summary
    assert not is_japanese_summary('This model was released. 日本語')
    assert not is_japanese_summary('新模型研究成果測試結果')
    assert is_japanese_summary('OpenAIが新しいモデルを公開しました。APIから利用できます。')


def test_processor_marks_invalid_llm_english_response_as_fallback():
    class Provider:
        available=True
        name='test'
        def chat(self,_):return '{"title_ja":"New Model", "summary":"English only", "score":70}'
    row=processor.LLMProcessor(Provider())._process_one({'name':'New Model','tagline':'Original English','links':{'official':'https://example.com/a'}})
    assert row.get('processing_status')=='fallback'


def test_processor_marks_actual_japanese_model_response():
    class Provider:
        available=True
        name='test'
        def chat(self,_):return '{"title_ja":"新モデルを公開", "summary":"新しいモデルを公開しました。公式サイトで確認できます。", "score":70}'
    row=processor.LLMProcessor(Provider())._process_one({'name':'New Model','tagline':'Original English','published_at':'2026-10-09T01:00:00Z','links':{'official':'https://example.com/a'}})
    assert row.get('processing_status')=='llm'
    assert row.get('published_at')=='2026-10-09T01:00:00Z'


def test_provider_does_not_call_retired_default_model(monkeypatch):
    monkeypatch.delenv('NVIDIA_MODEL',raising=False)
    monkeypatch.setenv('NVIDIA_API_KEY','unit-test-key')
    calls=[]
    monkeypatch.setattr(llm_provider.requests,'post',lambda *a,**k:calls.append(1))
    p=llm_provider.make_provider('nvidia')
    assert not p.available
    assert calls==[]
    assert p.last_error=='model_not_configured'


def test_provider_retries_transient_only_and_rejects_truncated_response(monkeypatch):
    seq=[SimpleNamespace(status_code=503,headers={}),SimpleNamespace(status_code=200,headers={},json=lambda:{'choices':[{'message':{'content':'incomplete'},'finish_reason':'length'}]})]
    calls=[]
    def post(*a,**kw):calls.append(kw);return seq.pop(0)
    monkeypatch.setattr(llm_provider.requests,'post',post)
    monkeypatch.setattr(llm_provider,'sleep',lambda _:None,raising=False)
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('test','https://example.com/v1','unit-test-key','model')
    assert p._call([{'role':'user','content':'hello'}]) is None
    assert len(calls)==2
    assert p.last_error=='truncated_response'
    assert calls[0]['json']['max_tokens']<=2048


def test_provider_410_is_not_retried_or_logged_with_body(monkeypatch,caplog):
    calls=[]
    def post(*a,**kw):calls.append(1);return SimpleNamespace(status_code=410,headers={},text='unit-test-key secret body')
    monkeypatch.setattr(llm_provider.requests,'post',post)
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('test','https://example.com/v1','unit-test-key','model')
    assert p._call([]) is None
    assert calls==[1]
    assert p.last_error=='http_410'
    assert 'secret body' not in caplog.text


def test_structured_resource_summary_is_localized_without_renaming_repo():
    class Provider:
        available=True
        name='test'
        def chat(self,_):return '{"title_ja":"新しいツール", "summary":"開発者向けの公開ツールです。導入手順を公式資料で確認できます。", "score":70}'
    row=processor.LLMProcessor(Provider()).process_github_repos([{'name':'owner/tool','url':'https://github.com/owner/tool','tagline':'A tool for developers','stars':200}])[0]
    assert row['title']=='owner/tool'
    assert row.get('processing_status')=='llm'
    assert '開発者向け' in row['summary']
    assert row['evidence']['metrics']


def test_quality_gate_enforces_minimum_source_coverage():
    from src.auto_collect.quality import validate_articles
    result=validate_articles([article()], min_articles=3, min_sources=2)
    assert result['status']=='failed'
    assert any('minimum' in e for e in result['errors'])


def test_daily_json_retains_quality_and_processing_status(monkeypatch,tmp_path):
    import json
    from datetime import date
    from src.auto_collect import daily_news_page
    monkeypatch.setattr(daily_news_page,'DAILY_NEWS_DIR',tmp_path/'daily-news')
    monkeypatch.setattr(daily_news_page,'ARCHIVE_DIR',tmp_path/'daily-news/archive')
    quality={'status':'passed','article_count':1,'japanese_count':1,'provider':'test','model':'model','sources':['Official']}
    daily_news_page.generate_daily_news(date(2026,10,9),[article()],quality=quality)
    data=json.loads((tmp_path/'daily-news/data.json').read_text())
    assert data['quality']==quality
    assert data['items'][0]['processing_status']=='llm'


@pytest.mark.parametrize('url',['https://example.com/news/\\','https://example.com:invalid/news','https://example.com/news\x00'])
def test_quality_rejects_malformed_url_bytes_and_ports(url):
    from src.auto_collect.quality import valid_article_url
    assert not valid_article_url(url)


def test_transient_article_failure_keeps_retryable_provenance():
    from src.auto_collect.quality import failure_reason, validate_articles
    class Provider:
        available=True
        name='test'
        last_error='http_429'
        def chat(self,_):return None
    row=processor.LLMProcessor(Provider())._process_one({'name':'Model update','tagline':'original English','source':'Official','links':{'official':'https://example.com/a'}})
    assert row['processing_error']=='http_429'
    assert failure_reason([row],validate_articles([row]))=='transient_generation_failed'
    row['processing_error']='invalid_japanese'
    assert failure_reason([row],validate_articles([row]))=='japanese_quality_failed'


def test_provider_error_state_is_thread_local():
    from concurrent.futures import ThreadPoolExecutor
    p=object.__new__(llm_provider.LLMProvider)
    p.last_error='main_error'
    def worker():
        p.last_error='http_429'
        return p.last_error
    with ThreadPoolExecutor(max_workers=1) as ex:
        assert ex.submit(worker).result()=='http_429'
    assert p.last_error=='main_error'


def test_quality_uses_rendered_source_attribution():
    from src.auto_collect.quality import validate_articles
    result=validate_articles([article(source='TechCrunch',source_attribution='TechCrunch（Bloomberg報道）')])
    assert result['sources']==['TechCrunch（Bloomberg報道）']


def _numbered(count, *, bad_at=()):
    rows=[]
    for i in range(count):
        row=article(url=f'https://example.com/n{i}', source='Official' if i % 2 == 0 else 'Other', title=f'記事{i}の見出し')
        if i in bad_at:
            row.update(summary='English fallback', processing_status='fallback', processing_error='invalid_japanese', title=f'bad {i}')
        rows.append(row)
    return rows


def test_two_of_seventy_five_fallbacks_are_excluded_and_the_day_passes():
    from src.auto_collect.quality import filter_publishable
    rows=_numbered(75, bad_at={72, 73})
    before=deepcopy(rows)
    kept, quality=filter_publishable(rows, min_articles=3, min_sources=2)
    assert rows==before
    assert quality['status']=='passed'
    assert quality['excluded_count']==2
    assert quality['input_count']==75
    assert quality['article_count']==73
    assert quality['japanese_count']==73
    assert round(quality['excluded_ratio'], 3)==round(2/75, 3)
    assert [row['index'] for row in quality['excluded']]==[73, 74]
    assert quality['excluded'][0]['url']=='https://example.com/n72'
    assert quality['excluded'][0]['title']=='bad 72'
    assert any('fallback' in err for err in quality['excluded'][0]['errors'])
    assert any('Japanese' in err for err in quality['excluded'][0]['errors'])
    assert all(row.get('processing_status')=='llm' for row in kept)


def test_exclusion_ratio_above_twenty_percent_holds_the_day():
    from src.auto_collect.quality import filter_publishable
    rows=_numbered(100, bad_at=set(range(79, 100)))
    _kept, quality=filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status']=='failed'
    assert any(err=='too many excluded articles: 21/100 > 20%' for err in quality['errors'])


def test_exclusion_ratio_of_exactly_twenty_percent_still_publishes():
    from src.auto_collect.quality import filter_publishable
    rows=_numbered(10, bad_at={8, 9})
    kept, quality=filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status']=='passed'
    assert len(kept)==8
    assert quality['excluded_count']==2


def test_exclusion_that_drops_below_source_minimum_holds_the_day():
    from src.auto_collect.quality import filter_publishable
    rows=[article(url=f'https://example.com/only{i}', source='Official') for i in range(4)]
    rows.append(article(url='https://example.com/other', source='Other', summary='English fallback', processing_status='fallback'))
    _kept, quality=filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status']=='failed'
    assert any('source' in err for err in quality['errors'])
    assert not any('too many excluded' in err for err in quality['errors'])


def test_clean_articles_match_validate_articles_and_record_no_exclusions():
    from src.auto_collect.quality import filter_publishable, validate_articles
    rows=[article(), article(url='https://other.example/a', source='Other')]
    kept, quality=filter_publishable(rows, min_articles=1, min_sources=1)
    base=validate_articles(rows, min_articles=1, min_sources=1)
    for key in ('status', 'article_count', 'japanese_count', 'sources', 'errors'):
        assert quality[key]==base[key]
    assert kept==rows
    assert quality['excluded']==[]
    assert quality['excluded_count']==0
    assert quality['input_count']==2


def test_non_dict_article_is_excluded_without_a_title_or_url():
    from src.auto_collect.quality import filter_publishable
    rows=_numbered(4)+['not-an-article']
    _kept, quality=filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status']=='passed'
    assert quality['excluded']==[{'index': 5, 'title': None, 'url': None, 'errors': ['invalid object']}]


def test_rate_limit_exclusions_remain_transient_when_the_day_is_held():
    from src.auto_collect.quality import failure_reason, filter_publishable
    rows=_numbered(8)
    rows+=[article(url=f'https://example.com/rate{i}', source='Official' if i % 2 == 0 else 'Other', summary='English fallback', processing_status='fallback', processing_error='http_429') for i in range(3)]
    _kept, quality=filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status']=='failed'
    assert failure_reason(rows, quality)=='transient_generation_failed'


def test_wait_budget_exclusions_remain_transient_when_the_day_is_held():
    from src.auto_collect.quality import failure_reason, filter_publishable
    rows=_numbered(8)
    rows+=[article(url=f'https://example.com/wait{i}', source='Official' if i % 2 == 0 else 'Other', summary='English fallback', processing_status='fallback', processing_error='wait_budget_exceeded') for i in range(3)]
    _kept, quality=filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status']=='failed'
    assert failure_reason(rows, quality)=='transient_generation_failed'


def test_structural_exclusions_are_not_classified_as_transient():
    from src.auto_collect.quality import failure_reason, filter_publishable
    rows=_numbered(8)
    rows.append(article(url='javascript:alert(1)', source='Official', summary='English fallback', processing_status='fallback', processing_error='http_429'))
    rows+=[article(url=f'https://example.com/rate{i}', source='Other', summary='English fallback', processing_status='fallback', processing_error='http_429') for i in range(3)]
    _kept, quality=filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status']=='failed'
    assert failure_reason(rows, quality)=='japanese_quality_failed'


def test_processor_retries_unparseable_json_once_then_accepts_japanese():
    calls=[]
    class Provider:
        available=True
        name='test'
        last_error=''
        def chat(self, _prompt):
            calls.append(_prompt)
            if len(calls)==1:
                return 'not json at all'
            return '{"title_ja":"新モデルを公開", "summary":"新しいモデルを公開しました。公式サイトで確認できます。", "score":70}'
    row=processor.LLMProcessor(Provider())._process_one({'name':'New Model','tagline':'Original English','links':{'official':'https://example.com/a'}})
    assert len(calls)==2
    assert row.get('processing_status')=='llm'


def test_processor_stops_after_one_json_retry():
    calls=[]
    class Provider:
        available=True
        name='test'
        last_error=''
        def chat(self, _prompt):
            calls.append(1)
            return 'still not json'
    row=processor.LLMProcessor(Provider())._process_one({'name':'New Model','tagline':'Original English','links':{'official':'https://example.com/a'}})
    assert len(calls)==2
    assert row.get('processing_status')=='fallback'
    assert row.get('processing_error')=='invalid_japanese'


def test_processor_does_not_retry_json_when_the_provider_returns_nothing():
    calls=[]
    class Provider:
        available=True
        name='test'
        last_error='http_429'
        def chat(self, _prompt):
            calls.append(1)
            return None
    row=processor.LLMProcessor(Provider())._process_one({'name':'New Model','tagline':'Original English','source':'Official','links':{'official':'https://example.com/a'}})
    assert calls==[1]
    assert row.get('processing_error')=='http_429'


def _ok_response():
    return SimpleNamespace(status_code=200, headers={}, json=lambda: {'choices':[{'message':{'content':'ok'},'finish_reason':'stop'}]})


def _http(code, headers=None):
    return SimpleNamespace(status_code=code, headers=headers or {}, text='secret body')


def test_provider_retries_429_with_exponential_backoff(monkeypatch):
    sleeps=[]
    seq=[_http(429), _http(429), _http(429), _ok_response()]
    monkeypatch.setattr(llm_provider.random, 'uniform', lambda _a, _b: 0)
    monkeypatch.setattr(llm_provider, 'sleep', lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_a, **_k: seq.pop(0))
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('test','https://example.com/v1','unit-test-key','model')
    assert p._call([{'role':'user','content':'hello'}])=='ok'
    assert sleeps==[2, 4, 8]
    assert seq==[]


def test_provider_honors_retry_after_on_each_429(monkeypatch):
    sleeps=[]
    seq=[_http(429, {'Retry-After':'5'}), _http(429, {'Retry-After':'5'}), _ok_response()]
    monkeypatch.setattr(llm_provider, 'sleep', lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_a, **_k: seq.pop(0))
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('test','https://example.com/v1','unit-test-key','model')
    assert p._call([{'role':'user','content':'hello'}])=='ok'
    assert sleeps==[5, 5]


def test_provider_stops_after_the_retry_budget(monkeypatch):
    calls=[]
    monkeypatch.setenv('LLM_MAX_RETRIES', '4')
    monkeypatch.setattr(llm_provider.random, 'uniform', lambda _a, _b: 0)
    monkeypatch.setattr(llm_provider, 'sleep', lambda _seconds: None)
    def post(*_a, **_k):
        calls.append(1)
        return _http(429)
    monkeypatch.setattr(llm_provider.requests, 'post', post)
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('test','https://example.com/v1','unit-test-key','model')
    assert p._call([{'role':'user','content':'hello'}]) is None
    assert calls==[1, 1, 1, 1, 1]
    assert p.last_error=='http_429'


def test_nvidia_paces_by_default_and_ollama_does_not(monkeypatch):
    sleeps=[]
    clock={'now': 10.0}
    monkeypatch.delenv('LLM_MIN_INTERVAL_SEC', raising=False)
    monkeypatch.setattr(llm_provider, 'monotonic', lambda: clock['now'])
    def sleep(seconds):
        sleeps.append(seconds)
        clock['now'] += seconds
    monkeypatch.setattr(llm_provider, 'sleep', sleep)
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_a, **_k: _ok_response())
    nvidia=object.__new__(llm_provider.LLMProvider)
    nvidia.config=llm_provider.ProviderConfig('nvidia','https://example.com/v1','unit-test-key','model')
    assert nvidia._call([{'role':'user','content':'a'}])=='ok'
    assert nvidia._call([{'role':'user','content':'b'}])=='ok'
    ollama=object.__new__(llm_provider.LLMProvider)
    ollama.config=llm_provider.ProviderConfig('ollama','http://localhost/v1','ollama','gemma3:4b')
    assert ollama._call([{'role':'user','content':'a'}])=='ok'
    assert ollama._call([{'role':'user','content':'b'}])=='ok'
    assert sleeps==[1.5]


def test_provider_waits_for_the_minimum_interval_between_calls(monkeypatch):
    clock={'now': 1000.0}
    sleeps=[]
    monkeypatch.setenv('LLM_MIN_INTERVAL_SEC', '1.5')
    monkeypatch.setattr(llm_provider, 'monotonic', lambda: clock['now'])
    def sleep(seconds):
        sleeps.append(seconds)
        clock['now']+=seconds
    monkeypatch.setattr(llm_provider, 'sleep', sleep)
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_a, **_k: _ok_response())
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('nvidia','https://example.com/v1','unit-test-key','model')
    assert p._call([{'role':'user','content':'hello'}])=='ok'
    assert p._call([{'role':'user','content':'hello'}])=='ok'
    assert sleeps==[1.5]
    assert not p._pace_lock.locked()


def test_provider_interval_sleep_is_outside_the_lock(monkeypatch):
    monkeypatch.setenv('LLM_MIN_INTERVAL_SEC', '1.5')
    monkeypatch.setattr(llm_provider, 'monotonic', lambda: 50.0)
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('test','https://example.com/v1','unit-test-key','model')
    def sleep(seconds):
        assert seconds==1.5
        assert not p._pace_lock.locked()
    monkeypatch.setattr(llm_provider, 'sleep', sleep)
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_a, **_k: _ok_response())
    p._call([{'role':'user','content':'one'}])
    p._call([{'role':'user','content':'two'}])


def test_provider_does_not_wait_once_the_total_budget_is_exhausted(monkeypatch):
    sleeps=[]
    clock={'now': 0.0}
    monkeypatch.setenv('LLM_MIN_INTERVAL_SEC', '1.5')
    monkeypatch.setenv('LLM_MAX_TOTAL_WAIT_SEC', '1')
    monkeypatch.setattr(llm_provider, 'monotonic', lambda: clock['now'])
    def sleep(seconds):
        sleeps.append(seconds)
        clock['now']+=seconds
    monkeypatch.setattr(llm_provider, 'sleep', sleep)
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_a, **_k: _ok_response())
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('test','https://example.com/v1','unit-test-key','model')
    assert p._call([{'role':'user','content':'hello'}])=='ok'
    assert p._call([{'role':'user','content':'hello'}]) is None
    assert sleeps==[]
    assert p.last_error=='wait_budget_exceeded'


def test_retry_backoff_stops_without_sleeping_past_the_wait_budget(monkeypatch):
    calls=[]
    sleeps=[]
    monkeypatch.setenv('LLM_MAX_TOTAL_WAIT_SEC', '3')
    monkeypatch.setattr(llm_provider.random, 'uniform', lambda _a, _b: 0)
    monkeypatch.setattr(llm_provider, 'sleep', lambda seconds: sleeps.append(seconds))
    def post(*_a, **_k):
        calls.append(1)
        return _http(429)
    monkeypatch.setattr(llm_provider.requests, 'post', post)
    p=object.__new__(llm_provider.LLMProvider)
    p.config=llm_provider.ProviderConfig('test','https://example.com/v1','unit-test-key','model')
    assert p._call([{'role':'user','content':'hello'}]) is None
    assert sleeps==[2]
    assert calls==[1, 1]
    assert p.last_error=='http_429'


def test_nvidia_override_requires_a_confirmed_key_and_hides_the_secret():
    from src.auto_collect.provider_selection import select_daily_provider
    provider, note=select_daily_provider('nvapi-unit-test-secret', None)
    assert provider=='ollama'
    assert "NVIDIA_PRODUCTION_USE_CONFIRMED is not 'true'" in note
    assert 'nvapi-unit-test-secret' not in note
    assert select_daily_provider('nvapi-unit-test-secret', 'true')==('nvidia', None)
    assert select_daily_provider('NVAPI-unit-test-secret', 'True')[0]=='ollama'
    assert select_daily_provider('', 'true')==('ollama', None)
    assert select_daily_provider('sk-other', 'true')==('ollama', None)


def test_provider_selection_cli_prints_provider_not_the_key():
    import os
    import subprocess
    import sys
    env=dict(os.environ)
    env['NVIDIA_API_KEY']='nvapi-unit-test-secret'
    env['NVIDIA_PRODUCTION_USE_CONFIRMED']='false'
    result=subprocess.run([sys.executable, '-m', 'src.auto_collect.provider_selection'], capture_output=True, text=True, env=env)
    assert result.returncode==0
    assert 'provider=ollama' in result.stdout
    assert 'nvapi-unit-test-secret' not in result.stdout + result.stderr
    assert "not 'true'" in result.stdout


def test_anthropic_news_rss_is_not_collected():
    from src.auto_collect.config import EN_RSS_FEEDS, JP_RSS_FEEDS
    urls=[feed['url'] for feed in EN_RSS_FEEDS+JP_RSS_FEEDS]
    assert 'https://www.anthropic.com/news/rss.xml' not in urls


def _ollama_provider(monkeypatch):
    monkeypatch.setattr(llm_provider.LLMProvider, '_health_check', lambda self: True)
    return llm_provider.make_provider('ollama')


def test_ollama_defaults_to_ipv4_loopback_not_localhost(monkeypatch):
    monkeypatch.delenv('OLLAMA_HOST', raising=False)
    monkeypatch.delenv('OLLAMA_BASE_URL', raising=False)
    from src.auto_collect.config import ollama_origin, ollama_generate_url, ollama_chat_url
    assert ollama_origin()=='http://127.0.0.1:11434'
    assert ollama_generate_url()=='http://127.0.0.1:11434/api/generate'
    assert ollama_chat_url()=='http://127.0.0.1:11434/v1/chat/completions'
    provider=_ollama_provider(monkeypatch)
    assert provider.config.base_url=='http://127.0.0.1:11434/v1'
    assert 'localhost' not in provider.config.base_url


def test_ollama_base_url_overrides_host(monkeypatch):
    monkeypatch.setenv('OLLAMA_HOST', '10.0.0.2:11434')
    monkeypatch.setenv('OLLAMA_BASE_URL', 'http://10.0.0.8:11434/v1/')
    from src.auto_collect.config import ollama_origin, ollama_generate_url, ollama_chat_url
    assert ollama_origin()=='http://10.0.0.8:11434'
    assert ollama_generate_url()=='http://10.0.0.8:11434/api/generate'
    assert ollama_chat_url()=='http://10.0.0.8:11434/v1/chat/completions'
    assert _ollama_provider(monkeypatch).config.base_url=='http://10.0.0.8:11434/v1'


def test_ollama_host_without_scheme_is_an_http_origin(monkeypatch):
    monkeypatch.delenv('OLLAMA_BASE_URL', raising=False)
    monkeypatch.setenv('OLLAMA_HOST', '192.168.1.9:11434')
    from src.auto_collect.config import ollama_origin
    assert ollama_origin()=='http://192.168.1.9:11434'
    assert _ollama_provider(monkeypatch).config.base_url=='http://192.168.1.9:11434/v1'
