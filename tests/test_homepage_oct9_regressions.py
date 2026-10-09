import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build(tmp_path, headlines):
    scripts = tmp_path/'scripts'; scripts.mkdir()
    shutil.copy2(ROOT/'scripts/build-homepage-latest.js', scripts)
    shutil.copy2(ROOT/'index.html', tmp_path/'index.html')
    slides = tmp_path/'presentations/day_slides'; slides.mkdir(parents=True)
    (slides/'day_slide_2026_10_09.html').write_text('<title>独立スライド</title><h1>独立スライド</h1>')
    api = tmp_path/'public-pages/api/auto_daily_report'; api.mkdir(parents=True)
    (api/'latest.json').write_text(json.dumps({'date':'2026-10-09','headlines':headlines}))
    result = subprocess.run(['node',str(scripts/'build-homepage-latest.js')],capture_output=True,text=True)
    assert result.returncode == 0,result.stderr
    return (tmp_path/'index.html').read_text(),json.loads((tmp_path/'news/latest.json').read_text())

def test_unknown_english_data_does_not_promise_nonexistent_japanese_report(tmp_path):
    html,_=build(tmp_path,[{'title':'English only headline','tldr':'English summary','impact':'','score':70}])
    brief=html.split('id="dailyHeadlines"')[1].split('</ol>')[0]
    assert '日本語の要約は日次レポートで確認してください' not in brief
    assert '日本語要約は未作成' in brief
    assert '影響対象は未確認' in brief

def test_news_selection_does_not_fabricate_slide_score_or_monthly_top10(tmp_path):
    html,data=build(tmp_path,[{'title':'日本語ニュース','tldr':'確認済み内容','impact':'利用者','score':70,'url':'https://example.com/story'}])
    ranking=html.split('id="rankingGrid"')[1].split('</section>')[0]
    assert '独立スライド' not in ranking
    assert 'rc-score' not in ranking
    assert 'TOP 10 をすべて見る' not in html
    assert 'stars' not in data['highlight']
    assert '最新掲載ニュースの注目3本' in html


def test_js_behavior_regressions():
    result=subprocess.run(['node','--test',str(ROOT/'tests/homepage_ui_regressions.cjs')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr

def test_reviewed_registry_reaches_homepage_and_news_sections(tmp_path):
    config=tmp_path/'config';config.mkdir()
    (config/'reviewed_news_summaries.json').write_text(json.dumps({'version':1,'articles':{
        'https://example.com/reviewed/':{'source_url':'https://example.com/reviewed/','source_date':'2026-10-08','reviewed_at':'2026-10-09','review_method':'ai_document_review','publisher':'一次資料','title':'確認した日本語見出し','tldr':'一次資料で確認した変更点。','summary':'確認した詳細です。','impact':'開発者に関係する事例です。'}
    }}))
    html,data=build(tmp_path,[{'title':'English','url':'https://example.com/reviewed','score':70}])
    assert '確認した日本語見出し' in html
    assert '一次資料で確認した変更点。' in html
    assert data['sections']['tech'][0]['title']=='確認した日本語見出し'
    assert data['sections']['tech'][0]['blurb']=='一次資料で確認した変更点。'

import pytest
@pytest.mark.parametrize('url',[
    'https://user:password@openai.com/index/oracle','https://openai.com/\nindex/oracle',
    'https://openai.com:443/index/oracle','https://openai.com/a/../index/oracle',
    'https://openai.com/index/oracle?different=1','https://openai.com/index/oracle#different',
])
def test_reviewed_copy_does_not_cross_url_identity_boundaries(tmp_path,url):
    config=tmp_path/'config';config.mkdir()
    shutil.copy2(ROOT/'config/reviewed_news_summaries.json',config)
    _,data=build(tmp_path,[{'title':'Original title','url':url,'score':70}])
    from src.auto_collect.reviewed_summaries import apply_reviewed_summary
    expected=apply_reviewed_summary({'title':'Original title','url':url,'score':70})
    assert data['sections']['tech'][0]['title']==expected['title']=='Original title'

@pytest.mark.parametrize('corruption',['date','publisher','duplicate','version'])
def test_javascript_rejects_malformed_editorial_registry(tmp_path,corruption):
    payload=json.loads((ROOT/'config/reviewed_news_summaries.json').read_text())
    key,record=next(iter(payload['articles'].items()))
    if corruption=='date':record['source_date']='2026-02-30'
    if corruption=='publisher':record.pop('publisher')
    if corruption=='duplicate':payload['articles'][key.rstrip('/')]=dict(record)
    if corruption=='version':payload['version']=2
    config=tmp_path/'config';config.mkdir()
    (config/'reviewed_news_summaries.json').write_text(json.dumps(payload))
    with pytest.raises(AssertionError,match='reviewed summaries'):
        build(tmp_path,[{'title':'Original title','url':key,'score':70}])
