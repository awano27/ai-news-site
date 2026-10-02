"""Offline browser verification; temporary site, external responses mocked."""
from pathlib import Path
from datetime import date
import functools
import http.server
import json
import shutil
import sys
import tempfile
import threading
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from playwright.sync_api import sync_playwright, expect
from src.auto_collect import daily_news_page
from src.generators.ranking_report_generator import RankingReportGenerator

OUT = Path(__file__).resolve().parent / 'browser'
OUT.mkdir(exist_ok=True)
CHROME = Path.home() / 'AppData/Local/ms-playwright/chromium-1200/chrome-win64/chrome.exe'
PAYLOAD = '</script><script>window.__injected=true</script><img src=x onerror="window.__injected=true">'


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def translate_path(self, path):
        local = super().translate_path(path)
        if not Path(local).exists():
            from urllib.parse import urlsplit, unquote
            relative = unquote(urlsplit(path).path).lstrip('/')
            candidate = (ROOT / relative).resolve()
            allowed = (ROOT / 'assets').resolve()
            image_dir = (ROOT / 'presentations/day_slides/images').resolve()
            if candidate.is_relative_to(allowed) or candidate.is_relative_to(image_dir):
                if candidate.is_file():
                    return str(candidate)
        return local


def run():
    with tempfile.TemporaryDirectory(prefix='visionhub-browser-') as directory:
        site = Path(directory)
        for rel in ['index.html', 'articles/claim-evidence-design.html', 'presentations/ai_coding_agents_guide.html',
                    'presentations/day_slides/day_slide_2026_09_13.html', 'news/latest.json',
                    'presentations/day_slides_index.html', 'presentations/day_slides/list.json',
                    'presentations/day_slides/meta_index.json', 'public-pages/news/archive_index.json',
                    'config/analytics.json']:
            dest = site / rel; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dest)
        shutil.copytree(ROOT / 'assets/js', site / 'assets/js')
        for name in ('claim-evidence.css',):
            shutil.copy2(ROOT / 'assets' / name, site / 'assets' / name)
        with patch.object(daily_news_page, 'DAILY_NEWS_DIR', site / 'daily-news'), \
             patch.object(daily_news_page, 'ARCHIVE_DIR', site / 'daily-news/archive'):
            articles = [dict(title='AI fixture '+PAYLOAD, summary='Fixture summary & <b>literal</b>',
                             url='https://example.test/source', source='fixture', category='tech',
                             impact_score=85, published_at='2026-10-03T00:00:00+09:00',
                             collected_at='2026-10-03T09:00:00+09:00', evidence={'evidence_label':'Fact'}),
                        dict(title='AI unrelated fixture', summary='Second fixture',
                             url='https://example.test/second', source='fixture', category='research',
                             impact_score=70, published_at='2026-10-02T23:00:00+09:00')]
            daily_news_page.generate_daily_news(date(2026, 10, 3), articles)
        generator = RankingReportGenerator(output_dir=str(site / 'presentations'))
        data = dict(period_start='2026年9月4日', period_end='2026年10月3日',
                    ranking_items=[dict(rank=1,name=PAYLOAD,description=PAYLOAD,benefits='fixture',
                                        eng_tool=4,biz_eff=4,total_score=8)],
                    key_points=['fixture'],sectors=[],total_items=1)
        with patch.object(generator, 'parse_ranking_data', return_value=data):
            ranking = Path(generator.generate_ranking_report('fixture', PAYLOAD))
        handler = functools.partial(QuietHandler, directory=str(site))
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{server.server_port}'
        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, executable_path=str(CHROME))
                for width in (390, 1440):
                    context = browser.new_context(viewport={'width':width,'height':900})
                    def route(request):
                        if request.request.url.startswith(base+'/'):
                            request.continue_()
                        elif 'mermaid' in request.request.url:
                            request.fulfill(content_type='application/javascript', body='window.mermaid={initialize:()=>{}};')
                        elif 'chart' in request.request.url.lower():
                            request.fulfill(content_type='application/javascript', body='window.Chart=function(){}; Chart.defaults={font:{},plugins:{legend:{labels:{}}}};')
                        else:
                            request.fulfill(status=200, body='')
                    context.route('**/*', route)
                    page = context.new_page()
                    errors=[];console_errors=[];failed_responses=[]
                    page.on('pageerror',lambda error:errors.append(str(error)))
                    page.on('console', lambda message: console_errors.append(message.text) if message.type=='error' else None)
                    page.on('response', lambda response: failed_responses.append({'url':response.url.replace(base,''),'status':response.status}) if response.status>=400 else None)
                    paths = ['/', '/daily-news/', '/articles/claim-evidence-design.html',
                             '/presentations/ai_coding_agents_guide.html',
                             '/presentations/day_slides/day_slide_2026_09_13.html',
                             '/'+ranking.relative_to(site).as_posix()]
                    for number, path in enumerate(paths):
                        errors.clear()
                        console_errors.clear()
                        failed_responses.clear()
                        page.goto(base+path);page.wait_for_load_state('networkidle')
                        metrics=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,injected:!!window.__injected})')
                        assert not metrics['injected'], path
                        assert page.locator('img[onerror]').count()==0
                        if path=='/daily-news/':
                            expect(page.locator('[data-search]')).to_have_count(2)
                            assert PAYLOAD in page.locator('.card-title').first.inner_text()
                            search=page.locator('#q');search.fill('unrelated fixture')
                            expect(page.locator('[data-search]:visible')).to_have_count(1)
                            search.fill('no such fixture');expect(page.locator('[data-search]:visible')).to_have_count(0)
                            expect(page.locator('#empty')).to_be_visible()
                            search.fill('')
                        if path=='/':
                            assert page.locator('#rankingGrid .rc-score').first.inner_text()=='編集推薦'
                            assert page.locator('#heroNewsBtn').get_attribute('href')=='daily-news/'
                            page.locator('#heroNewsBtn').click();page.wait_for_load_state('networkidle')
                            assert page.url==base+'/daily-news/'
                            page.goto(base+'/');page.wait_for_load_state('networkidle')
                        page.evaluate('scrollTo(0,0)')
                        screenshot=OUT/f'{width}-{number}.png';page.screenshot(path=str(screenshot),full_page=False)
                        results.append(dict(width=width,path=path,page_errors=list(errors),metrics=metrics,
                                            console_errors=list(console_errors),failed_responses=list(failed_responses),screenshot=screenshot.name))
                    context.close()
                    static = browser.new_context(viewport={'width':width,'height':900}, java_script_enabled=False)
                    static.route('**/*', route)
                    page=static.new_page();page.goto(base+'/');page.wait_for_load_state('networkidle')
                    assert page.locator('#rankingGrid .rc-score').first.inner_text()=='編集推薦'
                    assert '30日間の TOP 30' in page.locator('#ranking .section-link').inner_text()
                    results.append(dict(width=width,path='/',javascript=False,static_recommendation=True))
                    static.close()
                browser.close()
        finally:
            server.shutdown();server.server_close()
        (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(results,ensure_ascii=False))


if __name__=='__main__':
    run()
