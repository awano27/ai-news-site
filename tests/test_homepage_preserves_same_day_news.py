import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('same_day',[True,False])
@pytest.mark.parametrize('date_format',['explicit','producer','conflicting'])
def test_slide_refresh_keeps_only_current_day_news(tmp_path,same_day,date_format):
    node=shutil.which('node')
    if not node: pytest.skip('node is required')
    scripts=tmp_path/'scripts';scripts.mkdir()
    shutil.copy2(ROOT/'scripts/build-homepage-latest.js',scripts/'build-homepage-latest.js')
    shutil.copy2(ROOT/'index.html',tmp_path/'index.html')
    slides=tmp_path/'presentations/day_slides';slides.mkdir(parents=True)
    (slides/'day_slide_2026_10_03.html').write_text('<title>New slide | 2026-10-03</title><h1>New slide</h1>',encoding='utf8')
    today=datetime.now(timezone.utc).date()
    report=tmp_path/'public-pages/api/auto_daily_report';report.mkdir(parents=True)
    (report/'latest.json').write_text(json.dumps({'date':today.isoformat(),'news':[]}),encoding='utf8')
    news=tmp_path/'news';news.mkdir()
    kept={'tools':[{'title':'Existing tool','source':{'url':'https://example.com/tool'}}],
          'sns':[{'title':'Existing X post','source':{'url':'https://x.com/example/status/1'}}]}
    news_day=today if same_day else today-timedelta(days=1)
    published={'sections':kept}
    if date_format != 'producer':
        published['news_date']=news_day.isoformat()
    generated_day=(today-timedelta(days=1) if same_day else today) if date_format == 'conflicting' else news_day
    published['generated_at']=f'{generated_day.isoformat()}T09:00:00+09:00'
    (news/'latest.json').write_text(json.dumps(published),encoding='utf8')
    csv=tmp_path/'public-pages/news';csv.mkdir(parents=True)
    (csv/'daily_latest.json').write_text(json.dumps({'sections':{'sns':[{'title':'CSV sentinel'}]}}),encoding='utf8')
    subprocess.run([node,str(scripts/'build-homepage-latest.js')],cwd=tmp_path,capture_output=True,check=True)
    generated=json.loads((news/'latest.json').read_text(encoding='utf8'))
    assert generated['highlight']['title']=='New slide'
    assert generated['sections']==(kept if same_day else {})
    assert 'CSV sentinel' not in json.dumps(generated)
    first=(news/'latest.json').read_bytes()
    subprocess.run([node,str(scripts/'build-homepage-latest.js')],cwd=tmp_path,capture_output=True,check=True)
    assert (news/'latest.json').read_bytes()==first
