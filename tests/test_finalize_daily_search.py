from scripts import finalize_day_slide


def test_finalize_search_and_home_refresh_is_ordered_and_dry_run_safe(monkeypatch,tmp_path):
    events=[]
    import build_search_index
    monkeypatch.setattr(finalize_day_slide,'ROOT',tmp_path)
    monkeypatch.setattr(build_search_index,'build_index',lambda root:events.append('read-search') or [])
    monkeypatch.setattr(build_search_index,'write_index',lambda root:events.append('write-search') or [])
    monkeypatch.setattr(finalize_day_slide.subprocess,'run',lambda *a,**k:events.append('home'))
    assert finalize_day_slide.run_search_and_home(True)==0
    assert events==['read-search']
    events.clear()
    assert finalize_day_slide.run_search_and_home(False)==0
    assert events==['write-search','home']
