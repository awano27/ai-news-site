import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def parse_titles(html):
    node = shutil.which('node')
    if not node:
        pytest.skip('node is required')
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    function = home.split('    function titlesFromIndex(html) {', 1)[1].split('    function renderWeek', 1)[0]
    source = 'function titlesFromIndex(html) {' + function
    result = subprocess.run(
        [node, '-e', 'const vm=require("vm"),fs=require("fs");const input=JSON.parse(fs.readFileSync(0,"utf8"));const ctx={};vm.createContext(ctx);vm.runInContext(input.source,ctx);console.log(JSON.stringify(ctx.titlesFromIndex(input.html)));'],
        input=json.dumps({'source': source, 'html': html}), text=True, encoding='utf-8', capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def test_week_titles_do_not_cross_anchor_boundaries():
    html = '''<a href="day_slides/day_slide_2026_09_30.html">Latest</a>
    <a href="day_slides/day_slide_2026_10_01.html"><h3 class="feat-title">HydraFusion &amp; Copilot</h3></a>
    <a href="day_slides/day_slide_2026_09_30.html"><span class="slide-title">Sol</span></a>'''
    assert parse_titles(html) == {'2026-10-01': 'HydraFusion & Copilot', '2026-09-30': 'Sol'}


def test_october_first_is_read_from_published_index():
    titles = parse_titles((ROOT / 'presentations/day_slides_index.html').read_text(encoding='utf-8'))
    assert 'HydraFusion' in titles['2026-10-01']
    assert 'Sol' in titles['2026-09-30']


def test_featured_title_keeps_priority_over_archive_title():
    html = '''<a href="day_slides/day_slide_2026_10_01.html"><h3 class="feat-title">Featured</h3></a>
    <a href="day_slides/day_slide_2026_10_01.html"><span class="slide-title">Archive</span></a>'''
    assert parse_titles(html) == {'2026-10-01': 'Featured'}


def test_python_generator_does_not_cross_anchor_boundaries():
    import importlib.util
    spec = importlib.util.spec_from_file_location('fallback', ROOT / 'scripts/update_home_fallback.py')
    fallback = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fallback)
    html = (ROOT / 'presentations/day_slides_index.html').read_text(encoding='utf-8')
    titles = fallback.titles_from_index(html)
    assert 'HydraFusion' in titles['2026-10-01']
    assert 'Sol' in titles['2026-09-30']
