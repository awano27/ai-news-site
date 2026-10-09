from datetime import date, datetime, timezone
from src.auto_collect.collectors import hn_collector
from src.auto_collect.daily_news_page import _is_recent


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        value=cls(2026,10,9,21,tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


def test_hn_excludes_stale_and_future_stories_and_preserves_source_time(monkeypatch):
    monkeypatch.setattr(hn_collector,'datetime',FrozenDatetime)
    epoch=lambda value:int(datetime.fromisoformat(value).timestamp())
    stories={
        1:{'title':'New AI model','url':'https://example.com/current','score':100,'time':epoch('2026-10-08T18:00:00+00:00')},
        2:{'title':'Old AI model','url':'https://example.com/stale','score':100,'time':epoch('2026-10-08T10:00:00+00:00')},
        3:{'title':'Future AI model','url':'https://example.com/future','score':100,'time':epoch('2026-10-10T00:00:00+00:00')},
    }
    class Response:
        def __init__(self,data):self.data=data
        def raise_for_status(self):pass
        def json(self):return self.data
    class Session:
        def get(self,url,**kwargs):
            return Response([1,2,3] if 'topstories' in url else stories[int(url.rsplit('/',1)[1].split('.')[0])])
    collector=hn_collector.HNAutoCollector()
    collector.session=Session()
    monkeypatch.setattr(collector,'_rate_limit',lambda:None)
    rows=collector.collect(date(2026,10,10))
    assert [r['name'] for r in rows]==['New AI model']
    assert rows[0]['published_at']=='2026-10-08T18:00:00+00:00'


def test_timeline_recency_uses_jst_for_aware_source_timestamps():
    # 10/8 UTC 18:00 is 10/9 JST 03:00, valid for the 10/10 morning edition.
    assert _is_recent({'date':'2026-10-08T18:00:00+00:00'},date(2026,10,10))
    assert not _is_recent({'date':'2026-10-08T14:00:00+00:00'},date(2026,10,10))
    assert not _is_recent({'date':'2026-10-11'},date(2026,10,10))
