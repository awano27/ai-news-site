from src.auto_collect.daily_news_page import _flatten_news
from src.auto_collect.reviewed_summaries import apply_reviewed_summary


def test_microsoft_course_is_not_an_organization():
    item = {'url': 'https://github.com/microsoft/generative-ai-for-beginners', 'title': 'Course', 'summary': '21 Lessonsという組織'}
    corrected = apply_reviewed_summary(item)
    assert 'Microsoft Cloud Advocates' in corrected['summary']
    assert '21レッスン' in corrected['summary']
    assert 'という組織' not in corrected['summary']
    assert item['summary'] == '21 Lessonsという組織'
    assert _flatten_news([item])[0]['summary'] == corrected['summary']


def test_ecc_describes_tools_not_models():
    item = {'url': 'https://github.com/affaan-m/ECC', 'title': 'ECC', 'summary': 'Claude Code、Codex、CursorなどのAIモデルのハーンネス'}
    corrected = apply_reviewed_summary(item)
    assert '開発ツール' in corrected['summary']
    assert 'AIモデル' not in corrected['summary']
    assert 'ハーンネス' not in corrected['summary']
    assert _flatten_news([item])[0]['summary'] == corrected['summary']
