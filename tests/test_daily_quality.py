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


def _row(i, **changes):
    base = article(
        url=f'https://host{i}.example/item-{i}',
        source='Alpha' if i % 2 == 0 else 'Beta',
        title=f'記事{i}の見出し',
    )
    base.update(changes)
    return base


def test_two_fallbacks_among_seventy_five_are_excluded_and_the_rest_pass():
    from src.auto_collect.quality import filter_publishable
    rows = [_row(i) for i in range(75)]
    rows[10] = _row(10, title='解析できなかった記事', summary='not japanese', processing_status='fallback')
    rows[40] = _row(40, title='もう一つの失敗', summary='English only', processing_status='fallback')
    before = deepcopy(rows)
    kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert rows == before
    assert quality['status'] == 'passed'
    assert quality['input_count'] == 75
    assert quality['excluded_count'] == 2
    assert quality['excluded_ratio'] == round(2 / 75, 3)
    assert len(kept) == 73
    assert quality['article_count'] == 73
    assert quality['japanese_count'] == 73
    assert [row['index'] for row in quality['excluded']] == [11, 41]
    assert [row['url'] for row in quality['excluded']] == [rows[10]['url'], rows[40]['url']]
    assert quality['excluded'][0]['title'] == '解析できなかった記事'
    assert any('fallback' in err for err in quality['excluded'][0]['errors'])
    assert any('Japanese' in err for err in quality['excluded'][0]['errors'])
    excluded_urls = {row['url'] for row in quality['excluded']}
    assert excluded_urls.isdisjoint(row['url'] for row in kept)


def test_excluded_ratio_above_twenty_percent_fails_publication():
    from src.auto_collect.quality import filter_publishable
    rows = []
    for i in range(100):
        bad = i < 21
        rows.append(_row(
            i,
            processing_status='fallback' if bad else 'llm',
            summary='English fallback' if bad else article()['summary'],
        ))
    kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert len(kept) == 79
    assert quality['status'] == 'failed'
    assert any(err.startswith('too many excluded articles: 21/100 > 20%') for err in quality['errors'])


def test_fewer_than_two_sources_after_exclusion_fails():
    from src.auto_collect.quality import filter_publishable
    rows = [_row(i, source='Alpha') for i in range(4)]
    rows.append(_row(4, source='Beta', processing_status='fallback', summary='English fallback'))
    _kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'failed'
    assert quality['excluded_count'] == 1
    assert any('source coverage' in err for err in quality['errors'])
    assert not any('too many excluded' in err for err in quality['errors'])


def test_clean_articles_match_validate_articles_and_exclude_nothing():
    from src.auto_collect.quality import filter_publishable, validate_articles
    rows = [article(), article(url='https://other.example/a', source='Other')]
    direct = validate_articles(rows)
    kept, quality = filter_publishable(rows)
    assert kept == rows
    assert quality['excluded'] == []
    assert quality['excluded_count'] == 0
    assert quality['input_count'] == 2
    for key in ('status', 'article_count', 'japanese_count', 'sources', 'errors'):
        assert quality[key] == direct[key]


def test_invalid_object_is_excluded_by_itself():
    from src.auto_collect.quality import filter_publishable
    rows = [_row(i) for i in range(9)]
    rows.insert(3, 'not-an-article')
    kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'passed'
    assert len(kept) == 9
    assert quality['excluded'] == [{
        'index': 4,
        'title': None,
        'url': None,
        'errors': ['article 4: invalid object'],
    }]


def test_transient_exclusions_stay_retryable_when_the_ratio_holds_publication():
    from src.auto_collect.quality import failure_reason, filter_publishable
    rows = [_row(i) for i in range(3)]
    rows.extend(
        _row(i, processing_status='fallback', processing_error='http_429', summary='English fallback')
        for i in range(3, 5)
    )
    _kept, quality = filter_publishable(rows, min_articles=3, min_sources=2)
    assert quality['status'] == 'failed'
    assert failure_reason(rows, quality) == 'transient_generation_failed'
    for row in rows[3:]:
        row['processing_error'] = 'invalid_japanese'
    assert failure_reason(rows, quality) == 'japanese_quality_failed'


def test_anthropic_rss_404_url_is_not_collected():
    from src.auto_collect.config import EN_RSS_FEEDS
    urls = [feed['url'] for feed in EN_RSS_FEEDS]
    assert 'https://www.anthropic.com/news/rss.xml' not in urls
    assert all('sitemap' not in url for url in urls)
