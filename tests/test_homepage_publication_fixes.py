import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_URL = 'https://gigazine.net/news/20261017-sauna-camp-machiasobi31'
USEFUL_URL = 'https://gigazine.net/news/20261017-agentsview'


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


def setup_site(tmp_path):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copy2(ROOT / 'scripts/build-homepage-latest.js', scripts)
    shutil.copy2(ROOT / 'index.html', tmp_path / 'index.html')
    slides = tmp_path / 'presentations/day_slides'
    slides.mkdir(parents=True)
    (slides / 'day_slide_2026_10_17.html').write_text('<title>Previous | 2026-10-17</title>', encoding='utf-8')
    api = tmp_path / 'public-pages/api/auto_daily_report/latest.json'
    api.parent.mkdir(parents=True)
    return slides, api


def build(tmp_path):
    result = subprocess.run(['node', str(tmp_path / 'scripts/build-homepage-latest.js')],
                            capture_output=True, encoding='utf-8', cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    return (tmp_path / 'index.html').read_text(encoding='utf-8')


@pytest.mark.parametrize('suffix', ['', '/', '/?utm_source=feed#summary'])
@pytest.mark.parametrize('input_mode', ['report', 'same_day_news'])
def test_reviewed_non_ai_article_stays_off_homepage_without_deleting_sources(tmp_path, suffix, input_mode):
    _, api = setup_site(tmp_path)
    today = datetime.now(timezone.utc).date().isoformat()
    bad = {'title': 'Excluded camp article', 'url': EXCLUDED_URL + suffix, 'category': 'Product', 'score': 99}
    useful = {'title': 'Useful AI tool', 'url': USEFUL_URL, 'category': 'Product', 'score': 85}
    api.write_text(json.dumps({'date': today, 'headlines': [bad, useful]}), encoding='utf-8')
    original_api = api.read_bytes()
    news = tmp_path / 'news/latest.json'
    news.parent.mkdir()
    kept = {'title': useful['title'], 'source': {'name': 'GIGAZINE', 'url': USEFUL_URL}, 'custom_field': 'retain me'}
    published = {'news_date': today, 'sections': {'tools': [
        {'title': bad['title'], 'source': {'name': 'GIGAZINE', 'url': bad['url']}}, kept]}}
    for _ in range(2):
        # Simulate either producer supplying the same misclassified article again.
        if input_mode == 'same_day_news':
            news.write_text(json.dumps(published), encoding='utf-8')
        elif news.exists():
            news.unlink()
        html = build(tmp_path)
        generated = json.loads(news.read_text(encoding='utf-8'))
        assert all(item['title'] != bad['title'] for rows in generated['sections'].values() for item in rows)
        assert 'Excluded camp article' not in html
        assert useful['title'] in html
        assert api.read_bytes() == original_api
        assert any(link.get('href') == USEFUL_URL for link in Links(html).links)
        if input_mode == 'same_day_news':
            assert generated['sections']['tools'] == [kept]


def test_week_fallback_advances_with_actual_slide_files_and_keeps_gaps_unlinked(tmp_path):
    slides, _ = setup_site(tmp_path)
    for day in [17, 18, 19]:
        title = f'Current &amp; verified &lt;tool&gt; {day} / $1 / $&amp;'
        (slides / f'day_slide_2026_10_{day}.html').write_text(
            f'<title>{title} | 2026-10-{day}</title>', encoding='utf-8')
        html = build(tmp_path)
        week = re.search(r'<!-- fallback:this-week -->(.*?)<!-- fallback:end -->', html, re.S).group(1)
        cards = Links(week).links
        latest = [link for link in cards if 'is-today' in link.get('class', '').split()]
        assert len(latest) == 1
        assert latest[0]['href'] == f'presentations/day_slides/day_slide_2026_10_{day}.html'
        assert week.count('class="today-flag"') == 1
        assert len(cards) == day - 16
        assert 'day_slide_2026_10_16.html' not in week
        assert week.count('class="week-card is-empty"') == 7 - len(cards)
        assert title in week
        assert '<tool>' not in week


def test_personal_project_link_is_in_hero_and_survives_regeneration(tmp_path):
    setup_site(tmp_path)
    for _ in range(2):
        html = build(tmp_path)
        matches = [link for link in Links(html).links if link.get('id') == 'heroMyToolsLink']
        assert len(matches) == 1
        assert matches[0]['href'] == 'presentations/my_tools.html'
        assert html.index('id="heroTodayBtn"') < html.index('id="heroMyToolsLink"') < html.index('<!-- SITREP:start')
        assert '個人開発の実例を見る' in html
        assert 'href="presentations/my_tools.html"' in html
        assert 'id="heroIdentity"' in html and 'id="heroNewsBtn"' in html
