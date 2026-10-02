from pathlib import Path
from datetime import datetime
import json
from unittest.mock import patch

from bs4 import BeautifulSoup
from jinja2 import Template
import pytest

from src.utils.sanitize import sanitize_html, sanitize_text
from src.generators.ranking_report_generator import RankingReportGenerator
from src.generators.slide_generator import SlideGenerator

ROOT = Path(__file__).resolve().parents[1]
PAYLOADS = ['<img src=x onerror="alert(1)">', '</script><script>alert(1)</script>',
            '" onmouseover="alert(1)', "A & B < C", "&amp;#26085;本 09朁E03日"]


@pytest.mark.parametrize('payload', PAYLOADS)
def test_rendered_html_keeps_escaping(payload):
    output = sanitize_html(Template('<head></head><p>{{ value }}</p>', autoescape=True)
                           .render(value=sanitize_text(payload)))
    soup = BeautifulSoup(output, 'html.parser')
    assert soup.p.get_text() == sanitize_text(payload)
    assert not soup.find(['img', 'script'])
    assert not soup.p.attrs


@pytest.mark.parametrize('payload', PAYLOADS)
def test_ranking_html_and_charts_keep_data_inert(tmp_path, payload):
    item = dict(rank=1, name=payload, description=payload, benefits=payload,
                eng_tool=4, biz_eff=4, total_score=8)
    data = dict(period_start='2026年9月1日', period_end='2026年9月30日',
                ranking_items=[item], key_points=[payload], sectors=[], total_items=1)
    generator = RankingReportGenerator(output_dir=str(tmp_path))
    with patch.object(generator, 'parse_ranking_data', return_value=data), \
         patch('src.generators.ranking_report_generator.datetime') as clock:
        clock.now.return_value = datetime(2026, 10, 3, 9)
        output = Path(generator.generate_ranking_report('fixture', payload)).read_text(encoding='utf-8')
        repeated = Path(generator.generate_ranking_report('fixture', payload)).read_text(encoding='utf-8')
        assert repeated == output
    soup = BeautifulSoup(output, 'html.parser')
    assert soup.h1.get_text() == sanitize_text(payload)
    assert soup.find('script', src='/assets/js/analytics.js') is not None
    assert not soup.find('img')
    assert len(soup.find_all('script')) == 4
    assert all(not any(key.startswith('on') for key in tag.attrs) for tag in soup.find_all())
    script = soup.find_all('script')[-1].string
    assert '</script>' not in script
    if '<' in sanitize_text(payload)[:20]:
        assert '\\u003c' in script


def test_monthly_slides_escape_and_serialize(tmp_path):
    news = tmp_path / 'news'; news.mkdir()
    payload = PAYLOADS[1]
    (news / '2026-09-01.json').write_text(json.dumps([
        dict(title=payload, summary=PAYLOADS[0], source=payload,
             evaluation={'overall_score': .95})]), encoding='utf-8')
    generator = SlideGenerator(str(news), str(ROOT / 'templates'), str(tmp_path / 'out'))
    for file in (generator.generate_monthly_slides(2026, 9),):
        assert file
        output = Path(file).read_text(encoding='utf-8')
        soup = BeautifulSoup(output, 'html.parser')
        assert soup.find('script', src='/assets/js/analytics.js') is not None
        assert payload in soup.get_text()
        assert not soup.find('img', attrs={'onerror': True})
        assert not soup.find('script', string='alert(1)')


def test_normalization_and_document_repair_are_separate():
    assert sanitize_text('&amp;#26085;本 09朁E03日') == '日本 09月03日'
    assert '&lt;img' in sanitize_html('<head></head><p>&lt;img src=x&gt;</p>')
