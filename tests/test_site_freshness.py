import pytest
from scripts import check_site_freshness as guard

SLUG = 'day_slide_2026_10_03'


@pytest.fixture
def site(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, 'ROOT', str(tmp_path))
    directory = tmp_path / 'presentations' / 'day_slides'; directory.mkdir(parents=True)
    (directory / (SLUG + '.html')).write_text('<html></html>', encoding='utf-8')
    (tmp_path / 'sitemap.xml').write_text('<urlset><url><loc>https://visionhub.jp/presentations/day_slides/' + SLUG + '.html</loc></url></urlset>', encoding='utf-8')
    return tmp_path


def card(kind, slug=SLUG):
    return f'<a href="day_slides/{slug}.html" class="other {kind}">slide</a>'


@pytest.mark.parametrize('content,expected', [
    (card('feat-card') + card('slide-card'), True),
    (card('feat-card'), False), (card('slide-card'), False),
    ('<!--' + card('feat-card') + card('slide-card') + '-->', False),
    (card('feat-card', 'day_slide_2026_10_02') + card('slide-card'), False),
    (card('feat-card') + card('slide-card') + card('slide-card', 'day_slide_2026_10_01'), False),
    ('<script>' + card('feat-card') + card('slide-card') + '</script>', False),
])
def test_actual_cards_and_existing_destinations(site, content, expected):
    (site / 'presentations' / 'day_slides_index.html').write_text(content, encoding='utf-8')
    report = guard.run(1, gap_days=1)
    assert report['ok'] is expected


def test_sitemap_comment_does_not_count(site):
    (site / 'presentations' / 'day_slides_index.html').write_text(card('feat-card') + card('slide-card'), encoding='utf-8')
    (site / 'sitemap.xml').write_text('<urlset><!-- ' + SLUG + ' --></urlset>', encoding='utf-8')
    assert not guard.run(1, gap_days=1)['ok']
