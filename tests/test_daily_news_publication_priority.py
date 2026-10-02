import json
from datetime import date

import pytest

from src.auto_collect import daily_news_page as page
from src.auto_collect.publication_priority import prefer_existing
from tests.test_publish_daily_report import create_repo, git, run_publisher, REPORT_DATE


def report(day, x_count):
    return {"date": day, "items": [{"type": "x"}] * x_count}


@pytest.mark.parametrize("existing,candidate,expected", [
    (report("2026-10-02", 15), report("2026-10-02", 0), True),
    (report("2026-10-02", 15), report("2026-10-03", 0), False),
    (report("2026-10-03", 0), report("2026-10-02", 15), True),
    (report("2026-10-02", 0), report("2026-10-02", 15), False),
])
def test_priority(existing, candidate, expected):
    assert prefer_existing(existing, candidate) is expected


def test_delayed_cloud_preserves_bundle_then_next_day_updates(monkeypatch, tmp_path):
    monkeypatch.setattr(page, "DAILY_NEWS_DIR", tmp_path)
    monkeypatch.setattr(page, "ARCHIVE_DIR", tmp_path / "archive")
    day = date(2026, 10, 2)
    page.generate_daily_news(day, [], x_articles=[{"name": "curated", "url": "https://x.com/example/status/1"}])
    paths = [tmp_path / "index.html", tmp_path / "data.json", tmp_path / "archive/2026-10-02.html"]
    before = [path.read_bytes() for path in paths]
    page.generate_daily_news(day, [])
    assert [path.read_bytes() for path in paths] == before
    page.generate_daily_news(date(2026, 10, 3), [])
    assert json.loads(paths[1].read_text(encoding="utf-8"))["date"] == "2026-10-03"
    assert paths[2].read_bytes() == before[2]


@pytest.mark.parametrize("local_x,remote_x,local_day,other_change", [
    (0, 15, REPORT_DATE.isoformat(), True),
    (15, 0, REPORT_DATE.isoformat(), True),
    (0, 15, "2026-07-19", True),
    (0, 15, REPORT_DATE.isoformat(), False),
])
def test_competing_push_preserves_priority_bundle(tmp_path, local_x, remote_x, local_day, other_change):
    repo, _ = create_repo(tmp_path)
    origin = tmp_path / "origin.git"
    writer = tmp_path / "writer"
    git(tmp_path, "init", "--bare", str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "origin", "HEAD:main")
    git(tmp_path, "clone", "--branch", "main", str(origin), str(writer))
    git(writer, "config", "user.name", "Writer")
    git(writer, "config", "user.email", "writer@example.com")
    archive = f"daily-news/archive/{REPORT_DATE.isoformat()}.html"
    for target, label, day, count in [(writer, "remote", REPORT_DATE.isoformat(), remote_x), (repo, "local", local_day, local_x)]:
        (target / "daily-news/data.json").write_text(json.dumps(report(day, count)), encoding="utf-8")
        for path in ["daily-news/index.html", archive]:
            (target / path).write_text(label, encoding="utf-8")
    git(writer, "add", "daily-news")
    git(writer, "commit", "-m", "remote publication")
    git(writer, "push", "origin", "HEAD:main")
    # Keep an independent daily artifact change so the losing timeline's
    # publication still has useful work after preserving the remote bundle.
    if other_change:
        (repo / "input/day/0718.txt").write_text("other report", encoding="utf-8")
    result = run_publisher(repo, push=True)
    assert result.returncode == 0, result.stderr
    expected = "remote" if local_day == REPORT_DATE.isoformat() and remote_x > local_x else "local"
    for path in ["daily-news/index.html", archive]:
        assert git(tmp_path, "--git-dir", str(origin), "show", f"main:{path}").stdout == expected
    data = json.loads(git(tmp_path, "--git-dir", str(origin), "show", "main:daily-news/data.json").stdout)
    assert data == report(REPORT_DATE.isoformat(), remote_x) if expected == "remote" else data == report(local_day, local_x)
