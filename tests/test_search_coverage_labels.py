import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_homepage_and_archive_show_actual_separate_corpus_ranges(tmp_path):
    (tmp_path/'scripts').mkdir()
    shutil.copy2(ROOT/'scripts/build-homepage-latest.js',tmp_path/'scripts')
    shutil.copy2(ROOT/'index.html',tmp_path/'index.html')
    (tmp_path/'presentations').mkdir()
    shutil.copy2(ROOT/'presentations/news_archive.html',tmp_path/'presentations/news_archive.html')
    data=tmp_path/'public-pages/news';data.mkdir(parents=True)
    records=[{'date':'2025-01-17','title':'old'},{'date':'2026-08-23','title':'new'},
             {'date':'2025-07-30','type':'slide'},{'date':'2026-09-28','type':'slide'},
             {'date':'2026-99-99','title':'invalid'}]
    (data/'search_index.json').write_text(json.dumps(records))
    subprocess.run(['node',str(tmp_path/'scripts/build-homepage-latest.js')],check=True,capture_output=True)
    for path,element in [('index.html','searchArchiveRange'),('presentations/news_archive.html','archiveCoverage')]:
        html=(tmp_path/path).read_text()
        label=re.search(rf'id="{element}"[^>]*>([^<]*)<',html)
        assert label
        assert label.group(1)=='ニュース収録: 2025-01-17〜2026-08-23 / スライド収録: 2025-07-30〜2026-09-28'
        assert '2026-99-99' not in label.group(1)


def test_archive_never_promises_unverified_daily_refresh():
    html=(ROOT/'presentations/news_archive.html').read_text()
    assert '毎朝07:00に更新される最新情報' not in html
    assert '最新の掲載ニュースは' in html and 'href="../daily-news/"' in html


def test_archive_live_label_tracks_received_index_and_preserves_missing_state():
    html=(ROOT/'presentations/news_archive.html').read_text()
    script=next(x for x in re.findall(r'<script[^>]*>(.*?)</script>',html,re.S) if 'corpusLabel' in x)
    # Evaluate the real pure coverage function independently of the browser DOM.
    match=re.search(r'function coverageLabel\(rows\)\{(.*?)\n    \}',script,re.S)
    assert match
    js=match.group(0)+"\nconsole.log(JSON.stringify([coverageLabel([{date:'2026-10-09'},{date:'2026-10-10',type:'slide'}]),coverageLabel([])]));"
    result=subprocess.run(['node','-e',js],check=True,capture_output=True,text=True)
    labels=json.loads(result.stdout)
    assert labels==['ニュース収録: 2026-10-09〜2026-10-09 / スライド収録: 2026-10-10〜2026-10-10','ニュース収録: 未収録 / スライド収録: 未収録']
    assert "document.getElementById('archiveCoverage').textContent=coverageLabel(all)" in script
