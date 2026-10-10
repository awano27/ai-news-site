"""Offline editorial recovery does not impersonate provider success."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import pytest
ROOT=Path(__file__).resolve().parents[1]
DAY='2026-10-10'
NOTICE='編集確認済み・3件の暫定版'

def publisher():
    assert importlib.util.find_spec('scripts.publish_editorial_recovery'), 'offline editorial publisher is not implemented'
    from scripts import publish_editorial_recovery
    return publish_editorial_recovery

def manifest():
    articles=[]
    for i in range(3):
        url=f'https://example.com/source-{i}'
        articles.append({'title':['企業が新しい安全対策を公開','開発者向けの計算環境を拡充','研究チームが日本語音声を評価'][i],'summary':'公式資料で公開された新しい取り組みを紹介します。効果は発表元の報告として扱います。','url':url,'source':'Publisher A' if i==0 else 'Publisher B','published_at':'2026-10-09','review':{'source_url':url,'source_date':'2026-10-09','reviewed_at':DAY,'review_method':'ai_document_review','reviewer':'assistant','scope':'Primary source and publication date read; claims attributed to publisher.'}})
    return {'version':1,'edition_date':DAY,'articles':articles}

def test_editorial_mode_is_distinct_and_retains_original_dates():
    m=publisher();articles,quality=m.prepare_editorial(manifest(),DAY)
    assert quality['status']=='editorial_reviewed' and quality['mode']=='editorial_review'
    assert quality['automatic_collection_status']=='not_recovered' and quality['notice']==NOTICE
    assert not quality.get('provider') and not quality.get('model')
    assert all(a['processing_status']=='editorial_reviewed' and a['published_at']=='2026-10-09' for a in articles)
    from scripts.check_daily_publication import validate_quality
    validate_quality({'date':DAY,'total':3,'items':articles,'quality':quality})

@pytest.mark.parametrize('change',[
 lambda d:d['articles'][0].update(summary='English paragraph only'),
 lambda d:d['articles'][0].update(title='English headline'),
 lambda d:d['articles'][0].update(published_at='2026-10-08'),
 lambda d:d['articles'][0].update(published_at='2026-10-11'),
 lambda d:d['articles'][0]['review'].update(source_date='2026-10-10'),
 lambda d:d['articles'][0]['review'].update(source_url='https://other.example/article'),
 lambda d:d['articles'][0]['review'].update(review_method='llm'),
 lambda d:d['articles'][0]['review'].update(reviewer=''),
 lambda d:d['articles'][0]['review'].update(scope=''),
 lambda d:d['articles'][0]['review'].update(reviewed_at='2026-10-08'),
 lambda d:d['articles'][0].update(url='javascript:alert(1)'),
 lambda d:d['articles'][1].update(url=d['articles'][0]['url']),
 lambda d:d.update(articles=d['articles'][:2]),
 lambda d:[a.update(source='Only publisher') for a in d['articles']],
])
def test_bad_manifest_fails(change):
    d=manifest();change(d)
    with pytest.raises(ValueError):publisher().prepare_editorial(d,DAY)

@pytest.mark.parametrize('change',[
 lambda d:d['quality'].update(provider='fake'),lambda d:d['quality'].update(model='fake'),
 lambda d:d['quality'].update(status='passed'),lambda d:d['quality'].update(automatic_collection_status='recovered'),
 lambda d:d['items'][0].update(processing_status='llm'),lambda d:d['items'][0].update(processing_status='source_japanese'),
 lambda d:d['items'][0].update(summary='内容を書き換えました。元の記事とは異なる説明に変更しています。'),
 lambda d:d['items'][0]['editorial_review'].update(content_sha256='0'*64),
 lambda d:d['items'][0]['editorial_review'].update(source_url='https://other.example/article'),
])
def test_strict_validation_rejects_fabrication(change):
    a,q=publisher().prepare_editorial(manifest(),DAY);d={'date':DAY,'total':3,'items':a,'quality':q};change(d)
    from scripts.check_daily_publication import validate_quality
    with pytest.raises(ValueError):validate_quality(d)

def fixture_root(tmp):
    root=tmp/'site';(root/'scripts').mkdir(parents=True)
    shutil.copy(ROOT/'scripts/build-homepage-latest.js',root/'scripts');shutil.copy(ROOT/'index.html',root)
    (root/'presentations/day_slides').mkdir(parents=True)
    (root/'presentations/day_slides/day_slide_2026_10_09.html').write_text('<title>前日スライド</title><meta name="description" content="前日の説明"><h1>前日スライド</h1>')
    def w(p,d):
        f=root/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(d,ensure_ascii=False))
    old={'date':'2026-10-09','title':'以前のニュースを保持','url':'https://old.example/a','source':'Old','type':'news','unrelated':'preserve this'}
    w('public-pages/news/search_index.json',[old]);w('daily-news/data.json',{'date':'2026-10-09','total':1,'items':[old]})
    w('public-pages/news/archive_index.json',[{'date':'2026-10-09','count':150}])
    w('presentations/daily_reports/index.json',{'count':1,'reports':[{'date':'2026-10-09','file':'auto_daily_report_2026_10_09.html','extra':'preserve'}]})
    w('presentations/daily_reports/searchable.json',{'count':1,'reports':[{'date':'2026-10-09','file':'auto_daily_report_2026_10_09.html','total':26,'titles':['前日'],'extra':'preserve'}]})
    (root/'daily-news/archive').mkdir();(root/'daily-news/archive/2026-10-09.html').write_text('prior edition bytes')
    return root,old

def test_offline_render_preserves_history_and_exposes_provisional_mode(tmp_path):
    m=publisher();root,old=fixture_root(tmp_path)
    indexes={n:json.loads((root/f'presentations/daily_reports/{n}.json').read_text())['reports'][0] for n in ['index','searchable']}
    result=m.publish_editorial(root,manifest(),DAY);assert result['total']==3
    for rel in ['daily-news/index.html','presentations/auto_daily_report.html','index.html']:
        h=(root/rel).read_text();assert NOTICE in h and '自動収集は未復旧' in h
        assert 'Ollama gemma3:4b' not in h and 'ローカルLLMでスコアリング' not in h
    assert (root/'daily-news/archive/2026-10-09.html').read_text()=='prior edition bytes'
    assert old in json.loads((root/'public-pages/news/search_index.json').read_text())
    for n,row in indexes.items():assert row in json.loads((root/f'presentations/daily_reports/{n}.json').read_text())['reports']
    daily=json.loads((root/'daily-news/data.json').read_text());report=json.loads((root/'presentations/auto_daily_report.json').read_text());snap=json.loads((root/f'public-pages/news/daily/{DAY}.json').read_text())
    assert daily['date']==report['date']==snap['date']==DAY
    assert all(a['published_at']=='2026-10-09' for a in daily['items']+report['headlines']+snap['items'])
    assert all(a['date']==DAY for a in snap['items'])
    from scripts.check_daily_publication import verify,Source
    assert 'editorial' in verify(Source(root),DAY,require_quality=True).lower()
    before=(root/'daily-news/data.json').read_bytes()
    with pytest.raises(ValueError,match='same or newer'):m.publish_editorial(root,manifest(),DAY)
    assert (root/'daily-news/data.json').read_bytes()==before

def test_bad_input_writes_nothing(tmp_path):
    root,_=fixture_root(tmp_path);before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    d=manifest();d['articles'][0]['review']['source_url']='https://wrong.example/source'
    with pytest.raises(ValueError):publisher().publish_editorial(root,d,DAY)
    assert before=={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}

def test_source_dates_are_visible_in_source_linked_notice(tmp_path):
    root,_=fixture_root(tmp_path);publisher().publish_editorial(root,manifest(),DAY)
    from scripts.check_daily_publication import Page
    for relative in ['daily-news/index.html','presentations/auto_daily_report.html','index.html']:
        page=Page((root/relative).read_text());text=page.elements['editorial-publication-notice']
        assert '原文掲載日: 2026-10-09' in text
        notices=[n for n in page.nodes if n['id']=='editorial-publication-notice']
        assert all(a['url'] in notices[0]['links'] for a in manifest()['articles'])

@pytest.mark.parametrize('relative',['daily-news/index.html','presentations/auto_daily_report.html','index.html'])
def test_hidden_editorial_notice_does_not_pass_strict_check(tmp_path,relative):
    root,_=fixture_root(tmp_path);publisher().publish_editorial(root,manifest(),DAY)
    path=root/relative;path.write_text(path.read_text().replace('id="editorial-publication-notice"','id="editorial-publication-notice" hidden'))
    from scripts.check_daily_publication import Source,verify
    with pytest.raises(ValueError,match='notice'):verify(Source(root),DAY,require_quality=True)

def test_homepage_builder_preserves_editorial_notice_then_removes_it_for_automatic_mode(tmp_path):
    import subprocess
    root,_=fixture_root(tmp_path);before=(root/'index.html').read_text();publisher().publish_editorial(root,manifest(),DAY)
    command=['node',str(root/'scripts/build-homepage-latest.js')]
    subprocess.run(command,check=True,capture_output=True)
    assert NOTICE in (root/'index.html').read_text()
    latest=json.loads((root/'news/latest.json').read_text())
    rows=[row for values in latest['sections'].values() for row in values]
    assert rows and all(row.get('published_at')=='2026-10-09' and row.get('stars') is None for row in rows)
    # Homepage identity is unrelated to this provisional daily edition.
    import re
    after=(root/'index.html').read_text()
    assert re.search(r'<title>(.*?)</title>',after).group(1)==re.search(r'<title>(.*?)</title>',before).group(1)
    for relative in ['public-pages/api/auto_daily_report/latest.json','daily-news/data.json']:
        path=root/relative;data=json.loads(path.read_text());data['quality']={'status':'passed','provider':'test','model':'test-model'};path.write_text(json.dumps(data,ensure_ascii=False))
    subprocess.run(command,check=True,capture_output=True)
    assert 'editorial-publication-notice' not in (root/'index.html').read_text()

@pytest.mark.parametrize('changes',[{'score':100},{'score_status':'ranked'},{'evidence_label':'独立検証済み'},{'evidence':{'evidence_label':'Fact'}}])
def test_report_cannot_add_rankings_or_verification_badges(tmp_path,changes):
    root,_=fixture_root(tmp_path);publisher().publish_editorial(root,manifest(),DAY)
    for relative in ['presentations/auto_daily_report.json','public-pages/api/auto_daily_report/latest.json']:
        path=root/relative;data=json.loads(path.read_text());data['headlines'][0].update(changes);path.write_text(json.dumps(data,ensure_ascii=False))
    from scripts.check_daily_publication import Source,verify
    with pytest.raises(ValueError):verify(Source(root),DAY,require_quality=True)

def test_editorial_report_cannot_silently_lose_reviewed_articles(tmp_path):
    root,_=fixture_root(tmp_path);publisher().publish_editorial(root,manifest(),DAY)
    for relative in ['presentations/auto_daily_report.json','public-pages/api/auto_daily_report/latest.json']:
        path=root/relative;data=json.loads(path.read_text());data['headlines']=data['headlines'][:1];data['total']=1;path.write_text(json.dumps(data,ensure_ascii=False))
    path=root/'presentations/auto_daily_report.html';path.write_text(path.read_text().replace('name="report:total" content="3"','name="report:total" content="1"'))
    from scripts.check_daily_publication import Source,verify
    with pytest.raises(ValueError,match='three|total'):verify(Source(root),DAY,require_quality=True)

def test_checked_in_editorial_manifests_pass_their_edition_contract():
    paths=sorted((ROOT/'config').glob('editorial_recovery_*.json'))
    assert paths, 'at least one reproducible editorial manifest must be committed'
    module=publisher()
    for path in paths:
        data=json.loads(path.read_text(encoding='utf-8'))
        assert path.stem=='editorial_recovery_'+data['edition_date']
        articles,quality=module.prepare_editorial(data,data['edition_date'])
        module.validate_editorial_quality({'date':data['edition_date'],'total':len(articles),'items':articles,'quality':quality})
        tampered=deepcopy(data);tampered['articles'][0]['review']['source_date']='2000-01-01'
        with pytest.raises(ValueError):module.prepare_editorial(tampered,data['edition_date'])
