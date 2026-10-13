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


X_SUMMARY = '新しい言語モデルの発表を紹介しています。研究者は公式資料を確認できます。'
LUNCH_SUMMARY = '昼ごはんの写真が共有されています。食事の様子が写っています。'


def x_post(**changes):
    row = {
        'name': 'New model thread',
        'description': 'A new language model was announced for researchers.',
        'tagline': 'A new language model was announced.',
        'rss_source': 'X (@example)',
        'source': 'X',
        'url': 'https://x.com/example/status/1',
        'links': {'official': 'https://x.com/example/status/1'},
        'x_curated': True,
        'x_tweet_id': '1',
        'x_images': ['https://pbs.twimg.com/media/a.jpg'],
        'x_note': 'memo',
        'bookmark_date': '2026-10-12',
        'authors': '@example',
    }
    row.update(changes)
    return row


def x_json(*, related=True, summary=X_SUMMARY, title='新しいモデルの発表'):
    return '{"title_ja":"%s","summary":"%s","ai_related":%s}' % (title, summary, 'true' if related else 'false')


def test_news_without_an_ai_judgement_still_passes_article_checks():
    from src.auto_collect.quality import article_errors
    assert article_errors(article()) == []
    assert 'ai_related' not in article()


def test_x_posts_are_summarized_through_provider_chat():
    prompts = []

    class Provider:
        available = True
        name = 'ollama'
        last_error = ''

        def chat(self, prompt):
            prompts.append(prompt)
            return x_json()

    row = processor.LLMProcessor(Provider()).process_x_posts([x_post()])[0]
    assert prompts and 'ai_related' in prompts[0]
    assert 'language model was announced' in prompts[0]
    assert row['processing_status'] == 'llm'
    assert row['ai_related'] is True
    assert row['x_curated'] is True
    assert row['summary'] == X_SUMMARY
    assert row['url'] == 'https://x.com/example/status/1'
    assert row['rss_source'] == 'X (@example)'
    assert row['x_tweet_id'] == '1'
    assert row['x_images'] == ['https://pbs.twimg.com/media/a.jpg']
    assert row['bookmark_date'] == '2026-10-12'


def test_x_summary_retries_broken_json_once_then_accepts():
    calls = []

    class Provider:
        available = True
        name = 'ollama'
        last_error = ''

        def chat(self, _prompt):
            calls.append(1)
            return 'not json' if len(calls) == 1 else x_json()

    row = processor.LLMProcessor(Provider()).process_x_posts([x_post()])[0]
    assert calls == [1, 1]
    assert row['processing_status'] == 'llm'
    assert row['ai_related'] is True


def test_x_summary_does_not_retry_when_the_provider_returns_nothing():
    calls = []

    class Provider:
        available = True
        name = 'ollama'
        last_error = 'http_429'

        def chat(self, _prompt):
            calls.append(1)
            return None

    row = processor.LLMProcessor(Provider()).process_x_posts([x_post()])[0]
    assert calls == [1]
    assert row['processing_status'] == 'fallback'
    assert row['processing_error'] == 'http_429'
    assert row['url'] == 'https://x.com/example/status/1'


def test_failed_x_summary_is_excluded_with_a_reason():
    from src.auto_collect.quality import filter_publishable

    class Provider:
        available = True
        name = 'ollama'
        last_error = ''

        def chat(self, _prompt):
            return 'not json'

    broken = processor.LLMProcessor(Provider()).process_x_posts([x_post()])[0]
    kept, quality = filter_publishable(_numbered(4) + [broken], min_articles=3, min_sources=2)
    assert quality['status'] == 'passed'
    assert quality['input_count'] == 5
    assert quality['article_count'] == 4
    assert quality['excluded_count'] == 1
    assert quality['excluded'][0]['url'] == 'https://x.com/example/status/1'
    assert 'Japanese summary missing or invalid' in quality['excluded'][0]['errors']
    assert 'fallback or unverified processing' in quality['excluded'][0]['errors']
    assert all(row.get('url') != 'https://x.com/example/status/1' for row in kept)


def test_x_post_judged_not_ai_related_is_excluded_with_that_reason():
    from src.auto_collect.quality import article_errors, filter_publishable

    class Provider:
        available = True
        name = 'ollama'
        last_error = ''

        def chat(self, _prompt):
            return x_json(related=False, summary=LUNCH_SUMMARY, title='昼ごはんの写真')

    row = processor.LLMProcessor(Provider()).process_x_posts([x_post(description='NOTAI lunch photo')])[0]
    assert row['processing_status'] == 'llm'
    assert row['ai_related'] is False
    assert article_errors(row) == ['not AI-related']
    kept, quality = filter_publishable(_numbered(4) + [row], min_articles=3, min_sources=2)
    assert quality['status'] == 'passed'
    assert quality['excluded_count'] == 1
    assert quality['excluded'][0]['errors'] == ['not AI-related']
    assert all(item.get('ai_related') is not False for item in kept)


def test_x_post_without_a_boolean_judgement_is_excluded():
    from src.auto_collect.quality import article_errors
    row = article(x_curated=True, url='https://x.com/example/status/9', rss_source='X (@example)', source='X (@example)')
    assert 'AI relevance judgement missing' in article_errors(row)


def test_x_posts_share_one_gate_with_news():
    """X joins the same input, 20% ratio, article count, and source minimum.

    Six irrelevant posts among 64 combined items stay under 20% and do not
    hold the day. Kept posts increase article_count and sources. There is
    no separate X budget, and these drops are quality.excluded, not
    excluded_item_count.
    """
    from src.auto_collect.quality import filter_publishable
    unrelated = [
        article(
            url=f'https://x.com/example/status/{i}',
            source=f'X (@user{i})',
            rss_source=f'X (@user{i})',
            x_curated=True,
            ai_related=False,
            title=f'昼ごはん {i}',
        )
        for i in range(6)
    ]
    kept, quality = filter_publishable(_numbered(58) + unrelated, min_articles=3, min_sources=2)
    assert quality['status'] == 'passed'
    assert quality['input_count'] == 64
    assert quality['excluded_count'] == 6
    assert quality['excluded_ratio'] == round(6 / 64, 3)
    assert quality['article_count'] == 58
    assert quality['japanese_count'] == 58
    assert 'excluded_item_count' not in quality
    assert len(kept) == 58
    assert [row['errors'] for row in quality['excluded']] == [['not AI-related']] * 6

    related = article(
        url='https://x.com/example/status/kept',
        source='X (@example)',
        rss_source='X (@example)',
        x_curated=True,
        ai_related=True,
        title='新しいモデルの発表',
    )
    kept, quality = filter_publishable(_numbered(4) + [related], min_articles=3, min_sources=2)
    assert quality['status'] == 'passed'
    assert quality['article_count'] == 5
    assert quality['japanese_count'] == 5
    assert quality['input_count'] == 5
    assert quality['excluded_count'] == 0
    assert 'X (@example)' in quality['sources']

    boundary, boundary_quality = filter_publishable(_numbered(4) + unrelated[:1], min_articles=3, min_sources=2)
    assert boundary_quality['excluded_count'] == 1
    assert boundary_quality['input_count'] == 5
    assert boundary_quality['status'] == 'passed'
    assert len(boundary) == 4
    held, held_quality = filter_publishable(_numbered(4) + unrelated[:2], min_articles=3, min_sources=2)
    assert held_quality['status'] == 'failed'
    assert any('too many excluded articles: 2/6' in err for err in held_quality['errors'])
    assert len(held) == 4


def test_not_ai_related_exclusions_are_not_transient():
    from src.auto_collect.quality import failure_reason, filter_publishable
    rows = _numbered(2) + [
        article(url=f'https://x.com/example/status/{i}', x_curated=True, ai_related=False, title=f'昼ごはん {i}')
        for i in range(3)
    ]
    _kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'failed'
    assert failure_reason(rows, quality) == 'japanese_quality_failed'


def test_x_summary_retries_http_429_through_the_provider(monkeypatch):
    payload = x_json()
    seq = [
        _http(429, {'Retry-After': '5'}),
        SimpleNamespace(status_code=200, headers={}, json=lambda: {'choices': [{'message': {'content': payload}, 'finish_reason': 'stop'}]}),
    ]
    sleeps = []
    monkeypatch.setattr(llm_provider, 'sleep', lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(llm_provider.requests, 'post', lambda *_a, **_k: seq.pop(0))
    provider = object.__new__(llm_provider.LLMProvider)
    provider.config = llm_provider.ProviderConfig('ollama', 'http://127.0.0.1:11434/v1', 'ollama', 'gemma3:4b')
    provider.available = True
    row = processor.LLMProcessor(provider).process_x_posts([x_post()])[0]
    assert sleeps == [5]
    assert seq == []
    assert row['processing_status'] == 'llm'
    assert row['ai_related'] is True
    assert row['summary'] == X_SUMMARY


def test_published_x_card_shows_the_japanese_summary(monkeypatch, tmp_path):
    import json
    from datetime import date
    from src.auto_collect import daily_news_page
    monkeypatch.setattr(daily_news_page, 'DAILY_NEWS_DIR', tmp_path / 'daily-news')
    monkeypatch.setattr(daily_news_page, 'ARCHIVE_DIR', tmp_path / 'daily-news' / 'archive')
    day = date(2026, 10, 12)
    daily_news_page.generate_daily_news(day, [], x_articles=[{
        'name': 'New model thread',
        'title': '新しいモデルの発表',
        'url': 'https://x.com/example/status/1',
        'summary': X_SUMMARY,
        'description': 'raw english tweet should not be the card',
        'processing_status': 'llm',
        'rss_source': 'X (@example)',
        'ai_related': True,
        'bookmark_date': '2026-10-12',
    }])
    data = json.loads((tmp_path / 'daily-news' / 'data.json').read_text(encoding='utf-8'))
    item = data['items'][0]
    assert item['type'] == 'x'
    assert item['summary'] == X_SUMMARY
    assert item['processing_status'] == 'llm'
    assert item['source'] == 'X (@example)'
    html = (tmp_path / 'daily-news' / 'index.html').read_text(encoding='utf-8')
    assert X_SUMMARY in html
    assert 'raw english tweet should not be the card' not in html


def _eligible(rows, today, *, x=False):
    from src.auto_collect.daily_news_page import within_publication_window
    return [row for row in rows if within_publication_window(row, today, x=x)]


def test_quality_counts_match_the_published_page_when_stale_items_are_dropped(monkeypatch, tmp_path):
    """2026-10-13: article_count 115 (122-7) was computed before the page dropped 22 stale items, leaving 93."""
    import json
    from datetime import date
    from src.auto_collect.daily_news_page import generate_daily_news
    from src.auto_collect.quality import filter_publishable
    from scripts.check_daily_publication import validate_quality

    today = date(2026, 10, 13)
    recent_news = [
        article(url=f'https://example.com/recent/{i}', source='Official' if i % 2 == 0 else 'Other', title=f'新しい見出し{i}', date='2026-10-13')
        for i in range(82)
    ]
    recent_x = [
        article(
            url=f'https://x.com/lab/status/{i}', rss_source='X (@lab)', source='X (@lab)',
            title=f'Model thread {i}', date='', bookmark_date='2026-10-13', x_curated=True, ai_related=True,
        )
        for i in range(11)
    ]
    stale = [
        article(url=f'https://example.com/stale/{i}', source='Official', title=f'古い見出し{i}', date='2026-10-10', published_at='2026-10-10')
        for i in range(22)
    ]
    bad = [
        article(url=f'https://example.com/bad/{i}', source='Other', title=f'失敗{i}', date='2026-10-13', summary='English fallback', processing_status='fallback')
        for i in range(7)
    ]
    assert len(recent_news) + len(recent_x) + len(stale) + len(bad) == 122
    eligible = _eligible(recent_news + stale + bad, today) + _eligible(recent_x, today, x=True)
    kept, quality = filter_publishable(eligible, min_articles=3, min_sources=2)
    quality.update(provider='ollama', model='gemma3:4b')
    assert quality['status'] == 'passed'
    assert quality['input_count'] == 100
    assert quality['excluded_count'] == 7
    assert quality['excluded_ratio'] == round(7 / 100, 3)
    assert quality['article_count'] == 93
    assert quality['japanese_count'] == 93
    assert all(not str(row.get('url', '')).startswith('https://example.com/stale/') for row in quality['excluded'])
    news_kept = [row for row in kept if 'x.com' not in row['url']]
    x_kept = [row for row in kept if 'x.com' in row['url']]
    monkeypatch.setattr('src.auto_collect.daily_news_page.DAILY_NEWS_DIR', tmp_path / 'daily-news')
    monkeypatch.setattr('src.auto_collect.daily_news_page.ARCHIVE_DIR', tmp_path / 'daily-news' / 'archive')
    generate_daily_news(today, news_kept, x_articles=x_kept, quality=quality)
    data = json.loads((tmp_path / 'daily-news' / 'data.json').read_text(encoding='utf-8'))
    assert data['total'] == 93
    assert data['news_count'] == 82
    assert data['x_count'] == 11
    assert data['quality']['article_count'] == len(data['items']) == 93
    validate_quality(data)


def test_stale_items_neither_dilute_nor_inflate_the_exclusion_ratio():
    from datetime import date
    from src.auto_collect.quality import filter_publishable
    today = date(2026, 10, 13)
    stale = [article(url=f'https://example.com/old/{i}', date='2026-10-10') for i in range(20)]
    held = _eligible(
        [article(url=f'https://example.com/good/{i}', source='Official' if i % 2 == 0 else 'Other') for i in range(4)]
        + [article(url=f'https://example.com/bad/{i}', summary='English fallback', processing_status='fallback', source='Other') for i in range(2)]
        + stale,
        today,
    )
    _kept, quality = filter_publishable(held, min_articles=3, min_sources=2)
    assert quality['input_count'] == 6
    assert quality['status'] == 'failed'
    assert any('too many excluded articles: 2/6' in err for err in quality['errors'])
    published, ok = filter_publishable(_eligible(
        [article(url=f'https://example.com/keep/{i}', source='Official' if i % 2 == 0 else 'Other') for i in range(8)]
        + [article(url='https://example.com/one-bad', summary='English fallback', processing_status='fallback', source='Other')]
        + stale,
        today,
    ), min_articles=3, min_sources=2)
    assert ok['status'] == 'passed'
    assert ok['input_count'] == 9
    assert ok['excluded_count'] == 1
    assert ok['article_count'] == len(published) == 8
