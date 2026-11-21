from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from scripts import publish_daily_report
from scripts import build_search_index
from scripts.publish_daily_report import load_manifest, validate_changes


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "publish_daily_report.py"
MANIFEST_PATH = REPO_ROOT / "scripts" / "daily_report_paths.json"
REPORT_DATE = date(2026, 7, 18)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def create_repo(tmp_path: Path, *, include_optional: bool = False) -> tuple[Path, object]:
    repo = tmp_path / "daily-report-repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "user.email", "test@example.com")
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)
    repo_manifest = repo / "scripts" / "daily_report_paths.json"
    repo_manifest.parent.mkdir(parents=True, exist_ok=True)
    repo_manifest.write_text(MANIFEST_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    for relative_path in manifest.required:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"baseline {relative_path}\n", encoding="utf-8")
    daily = {"date": REPORT_DATE.isoformat(), "items": [
        {"title": "Baseline article", "url": "https://example.com/baseline"}]}
    (repo / "daily-news/data.json").write_text(json.dumps(daily), encoding="utf-8")
    (repo / f"public-pages/news/daily/{REPORT_DATE}.json").write_bytes(
        build_search_index.json_bytes(build_search_index.normalize_daily_payload(daily)))
    (repo / "public-pages/news/search_index.json").write_bytes(b"[]\n")
    if include_optional:
        for relative_path in manifest.optional:
            if "*" in relative_path:  # a glob names no single file to create
                continue
            path = repo / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"optional")
    baseline_paths = [
        "scripts/daily_report_paths.json",
        *manifest.required,
        *(path for path in manifest.optional if (repo / path).is_file()),
    ]
    git(repo, "add", "--", *baseline_paths)
    git(repo, "commit", "-m", "baseline")
    return repo, manifest


def run_publisher(repo: Path, *, push: bool = False) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT),
        "--repo",
        str(repo),
        "--date",
        REPORT_DATE.isoformat(),
        "--message",
        "publish daily report",
    ]
    if push:
        command.append("--push")
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_manifest_expands_all_date_formats_and_optional_ogp() -> None:
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)

    assert "input/day/0718.txt" in manifest.required
    assert "daily-news/archive/2026-07-18.html" in manifest.required
    assert "presentations/daily_reports/auto_daily_report_2026_07_18.html" in manifest.required
    assert manifest.optional == (
        "presentations/daily_reports/og/2026_07_18.png",
        "presentations/model_watch/2026-07-18.json",
        "public-pages/news/*.json",
    )


def test_historical_news_json_is_allowed_but_other_strays_are_not() -> None:
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)

    # update_news_archive.py regenerates any past date whose input txt looks newer.
    assert manifest.matches("public-pages/news/2026-06-07.json")
    assert manifest.matches("public-pages/news/2026-07-18.json")
    # The glob must not widen past one path segment, nor past that one directory.
    assert not manifest.matches("public-pages/news/nested/2026-06-07.json")
    assert not manifest.matches("public-pages/news/2026-06-07.json.bak")
    assert not manifest.matches("public-pages/api/stray.json")
    assert not manifest.matches(".env")


def test_required_manifest_entry_rejects_a_glob(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"required": ["public-pages/news/*.json"], "optional": []}),
        encoding="utf-8",
    )

    try:
        load_manifest(manifest_path, REPORT_DATE)
    except ValueError as error:
        assert "must not contain" in str(error)
    else:  # pragma: no cover - guards against a silently accepted glob
        raise AssertionError("a globbed required path must be rejected")


def test_regenerated_historical_news_json_publishes_with_the_day(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    today_path = "public-pages/news/daily/2026-07-18.json"
    historical_path = "public-pages/news/2026-06-07.json"
    assert today_path in manifest.required
    (repo / today_path).write_text("today\n", encoding="utf-8")
    (repo / historical_path).write_text("regenerated by update_news_archive\n", encoding="utf-8")

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    committed = git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines()
    assert committed == sorted((today_path, historical_path))


def test_unrelated_change_rejects_without_staging_or_losing_work(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    allowed = repo / manifest.required[0]
    unrelated = repo / "unrelated.txt"
    allowed.write_text("allowed update\n", encoding="utf-8")
    unrelated.write_text("keep this change\n", encoding="utf-8")

    result = run_publisher(repo)

    assert result.returncode != 0
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""
    assert allowed.read_text(encoding="utf-8") == "allowed update\n"
    assert unrelated.read_text(encoding="utf-8") == "keep this change\n"


def test_allowed_changes_commit_exactly_changed_manifest_paths(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    changed = (manifest.required[0], manifest.required[3])
    for relative_path in changed:
        (repo / relative_path).write_text("updated\n", encoding="utf-8")

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    committed = git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines()
    assert committed == sorted(changed)
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""


def test_missing_required_path_rejects_before_staging(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    (repo / manifest.required[0]).unlink()
    head_before = git(repo, "rev-parse", "HEAD").stdout

    result = run_publisher(repo)

    assert result.returncode != 0
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""
    assert git(repo, "rev-parse", "HEAD").stdout == head_before


def test_pre_staged_change_rejects_without_new_staged_changes(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    staged = repo / manifest.required[0]
    unstaged = repo / manifest.required[1]
    staged.write_text("already staged\n", encoding="utf-8")
    git(repo, "add", "--", manifest.required[0])
    unstaged.write_text("must remain unstaged\n", encoding="utf-8")
    before = git(repo, "diff", "--cached", "--name-only").stdout

    result = run_publisher(repo)

    assert result.returncode != 0
    assert git(repo, "diff", "--cached", "--name-only").stdout == before
    assert unstaged.read_text(encoding="utf-8") == "must remain unstaged\n"


def test_missing_optional_ogp_succeeds_and_archive_name_is_dated(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path, include_optional=False)
    archive_name = "presentations/daily_reports/auto_daily_report_2026_07_18.html"
    assert archive_name in manifest.required
    assert not (repo / manifest.optional[0]).exists()
    (repo / archive_name).write_text("updated archive\n", encoding="utf-8")

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    assert git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines() == [archive_name]


def test_ignored_required_file_is_discovered_and_force_added(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    ignored_path = manifest.required[0]
    (repo / ".gitignore").write_text("input/\n", encoding="utf-8")
    git(repo, "rm", "--cached", "--", ignored_path)
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "ignore generated input")

    assert git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout == ""
    assert (repo / ignored_path).is_file()

    result = run_publisher(repo)

    assert result.returncode == 0, result.stderr
    assert git(repo, "show", "--format=", "--name-only", "HEAD").stdout.splitlines() == [ignored_path]


def test_dirty_manifest_cannot_self_allow_an_ignored_secret(
    monkeypatch, tmp_path: Path
) -> None:
    repo, _manifest = create_repo(tmp_path)
    repo_manifest = repo / "scripts" / "daily_report_paths.json"
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "scripts/daily_report_paths.json")
    git(repo, "commit", "-m", "track publication policy")

    dirty_policy = json.loads(repo_manifest.read_text(encoding="utf-8"))
    dirty_policy["optional"].extend(["scripts/daily_report_paths.json", ".env"])
    repo_manifest.write_text(json.dumps(dirty_policy), encoding="utf-8")
    secret = repo / ".env"
    secret.write_text("TOP_SECRET=must-not-commit\n", encoding="utf-8")
    head_before = git(repo, "rev-parse", "HEAD").stdout
    monkeypatch.setattr(publish_daily_report, "MANIFEST_PATH", repo_manifest)

    result = publish_daily_report.publish(repo, REPORT_DATE, "publish daily report")

    assert result != 0
    assert git(repo, "rev-parse", "HEAD").stdout == head_before
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""
    assert secret.read_text(encoding="utf-8") == "TOP_SECRET=must-not-commit\n"


def test_rebase_retry_revalidates_a_tightened_remote_manifest(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    origin = tmp_path / "origin.git"
    writer = tmp_path / "policy-writer"
    git(tmp_path, "init", "--bare", str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-u", "origin", "HEAD:main")
    git(tmp_path, "--git-dir", str(origin), "symbolic-ref", "HEAD", "refs/heads/main")
    git(tmp_path, "clone", str(origin), str(writer))
    git(writer, "config", "user.name", "Policy Writer")
    git(writer, "config", "user.email", "policy@example.com")

    removed_path = manifest.required[0]
    writer_manifest = writer / "scripts" / "daily_report_paths.json"
    tightened = json.loads(writer_manifest.read_text(encoding="utf-8"))
    tightened["required"].remove("input/day/{MMDD}.txt")
    writer_manifest.write_text(json.dumps(tightened), encoding="utf-8")
    git(writer, "add", "scripts/daily_report_paths.json")
    git(writer, "commit", "-m", "tighten publication policy")
    git(writer, "push", "origin", "main")

    (repo / removed_path).write_text("must not cross tightened policy\n", encoding="utf-8")

    result = run_publisher(repo, push=True)

    assert result.returncode != 0
    assert "post-rebase publication rejected" in result.stderr
    remote_subject = git(
        tmp_path,
        "--git-dir",
        str(origin),
        "log",
        "-1",
        "--format=%s",
        "refs/heads/main",
    ).stdout.strip()
    assert remote_subject == "tighten publication policy"


def test_validate_changes_reports_missing_required_path(tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    (repo / manifest.required[-1]).unlink()

    errors = validate_changes(repo, manifest)

    assert any("missing required path" in error for error in errors)


def test_publish_stages_the_single_validated_status_snapshot(monkeypatch, tmp_path: Path) -> None:
    repo, manifest = create_repo(tmp_path)
    validated_path = manifest.required[0]
    (repo / validated_path).write_text("validated update\n", encoding="utf-8")
    (repo / "unrelated.txt").write_text("must never be staged\n", encoding="utf-8")
    snapshots = iter(((validated_path,), ("unrelated.txt",)))
    add_calls: list[tuple[str, ...]] = []
    original_git = publish_daily_report._git

    def changing_status(_: Path) -> tuple[str, ...]:
        return next(snapshots)

    def recording_git(repo_path: Path, args, *, check: bool = True):
        if args[0] == "add":
            add_calls.append(tuple(args))
        return original_git(repo_path, args, check=check)

    monkeypatch.setattr(publish_daily_report, "_status_paths", changing_status)
    monkeypatch.setattr(publish_daily_report, "_git", recording_git)

    result = publish_daily_report.publish(repo, REPORT_DATE, "publish daily report")

    assert result == 0
    assert add_calls == [("add", "-f", "--", validated_path)]


def test_manifest_requires_synced_search_and_homepage():
    manifest = load_manifest(MANIFEST_PATH, REPORT_DATE)
    for path in ('public-pages/news/daily/2026-07-18.json', 'public-pages/news/search_index.json',
                 'index.html', 'news/latest.json', 'presentations/news_archive.html'):
        assert path in manifest.required


def test_strict_publication_fails_before_commit_if_bundle_is_invalid(tmp_path):
    repo, manifest = create_repo(tmp_path)
    (repo / manifest.required[0]).write_text('updated\n')
    before = git(repo, 'rev-parse', 'HEAD').stdout
    result = publish_daily_report.publish(repo, REPORT_DATE, 'publish', require_quality=True)
    assert result == 1
    assert git(repo, 'rev-parse', 'HEAD').stdout == before
    assert not git(repo, 'diff', '--cached', '--name-only').stdout


def create_remote_with_unrelated_commit(tmp_path: Path, repo: Path) -> Path:
    """Publish the baseline to a bare origin, then land an unrelated slide on main.

    This is the morning race: the pipeline fast-forwards at 08:00, runs for half
    an hour, and by push time a slide or the cloud archive job has moved main.
    """
    origin = tmp_path / "origin.git"
    writer = tmp_path / "slide-writer"
    git(tmp_path, "init", "--bare", str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-u", "origin", "HEAD:main")
    git(tmp_path, "--git-dir", str(origin), "symbolic-ref", "HEAD", "refs/heads/main")
    git(tmp_path, "clone", str(origin), str(writer))
    git(writer, "config", "user.name", "Slide Writer")
    git(writer, "config", "user.email", "slides@example.com")
    slide = writer / "presentations" / "day_slides" / "day_slide_2026_07_18.html"
    slide.parent.mkdir(parents=True, exist_ok=True)
    slide.write_text("<h1>slide</h1>\n", encoding="utf-8")
    git(writer, "add", "presentations/day_slides/day_slide_2026_07_18.html")
    git(writer, "commit", "-m", "feat(slides): publish day slide")
    git(writer, "push", "origin", "main")
    return origin


def remote_log(tmp_path: Path, origin: Path) -> list[str]:
    result = git(tmp_path, "--git-dir", str(origin), "log", "--format=%s", "refs/heads/main")
    return result.stdout.strip().splitlines()


def test_strict_push_replays_onto_an_unrelated_remote_commit_and_rechecks_quality(monkeypatch, tmp_path):
    repo, manifest = create_repo(tmp_path)
    origin = create_remote_with_unrelated_commit(tmp_path, repo)
    (repo / manifest.required[0]).write_text("today's report\n", encoding="utf-8")
    checks: list[Path] = []
    monkeypatch.setattr(
        publish_daily_report, "_check_daily_publication", lambda root, _date: checks.append(root) or [],
        raising=False,
    )

    result = publish_daily_report.publish(repo, REPORT_DATE, "publish", push=True, require_quality=True)

    assert result == 0
    assert remote_log(tmp_path, origin) == ["publish", "feat(slides): publish day slide", "baseline"]
    assert checks == [repo, repo], "quality check must run before commit and again on the rebased tree"
    pushed_files = git(tmp_path, "--git-dir", str(origin), "ls-tree", "-r", "--name-only", "refs/heads/main").stdout
    assert "presentations/day_slides/day_slide_2026_07_18.html" in pushed_files


def test_strict_push_keeps_remote_untouched_when_the_rebased_bundle_fails_quality(monkeypatch, tmp_path, capsys):
    repo, manifest = create_repo(tmp_path)
    origin = create_remote_with_unrelated_commit(tmp_path, repo)
    (repo / manifest.required[0]).write_text("today's report\n", encoding="utf-8")
    verdicts = iter([[], ["daily date does not match 2026-07-18"]])
    monkeypatch.setattr(
        publish_daily_report, "_check_daily_publication", lambda _root, _date: next(verdicts), raising=False
    )

    result = publish_daily_report.publish(repo, REPORT_DATE, "publish", push=True, require_quality=True)

    assert result == 1
    assert "post-rebase publication rejected" in capsys.readouterr().err
    assert remote_log(tmp_path, origin) == ["feat(slides): publish day slide", "baseline"]


SEARCH_PATH = "public-pages/news/search_index.json"


def prepare_search_bundle(repo: Path, title: str) -> dict:
    """A real strict bundle, so retry tests exercise the actual quality checker."""
    day = REPORT_DATE.isoformat()
    item = {"title": title, "url": "https://example.com/current", "type": "news",
            "source": "Example", "category": "AI", "processing_status": "llm",
            "summary": "\u65e5\u672c\u8a9e\u3067\u30cb\u30e5\u30fc\u30b9\u306e\u8981\u70b9\u3092\u8aac\u660e\u3057\u307e\u3059\u3002"}
    daily = {"date": day, "total": 1, "news_count": 1, "items": [item],
             "quality": {"status": "passed", "provider": "test", "model": "test",
                         "article_count": 1, "japanese_count": 1, "sources": ["Example"],
                         "excluded": [{"url": "https://example.com/held", "errors": ["unverified"]}]}}
    report = {"date": day, "total": 1, "headlines": [item]}
    for path, data in (("daily-news/data.json", daily),
                       ("presentations/auto_daily_report.json", report),
                       ("public-pages/api/auto_daily_report/latest.json", report),
                       (f"public-pages/news/daily/{day}.json", build_search_index.normalize_daily_payload(daily))):
        (repo / path).write_bytes(build_search_index.json_bytes(data))
    html = (f'<meta name="report:date" content="{day}"><meta name="report:total" content="1">'
            f'<article class="card"><h2 class="card-title"><a href="{item["url"]}">{title}</a></h2>'
            f'<div class="card-body">{item["summary"]}</div></article>')
    (repo / "daily-news/index.html").write_text(html, encoding="utf-8")
    (repo / "presentations/auto_daily_report.html").write_text(
        html.replace('class="card"', 'class="row"').replace("card-title", "row-title").replace("card-body", "d-summary"),
        encoding="utf-8")
    (repo / "index.html").write_text(
        f'<time id="dailyReportDate">{day}</time><time id="dailyNewsDate">{day}</time>'
        f'<ol id="dailyHeadlines"><li>{title}<a href="{item["url"]}">source</a></li></ol>', encoding="utf-8")
    return item


def create_search_race(tmp_path: Path):
    repo, manifest = create_repo(tmp_path)
    prepare_search_bundle(repo, "\u53e4\u3044\u65e5\u672c\u8a9e\u306e\u898b\u51fa\u3057")
    (repo / SEARCH_PATH).write_bytes(b"[]\n")
    build_search_index.write_index(repo)
    git(repo, "add", "--", *manifest.required)
    git(repo, "commit", "-m", "valid search baseline")
    origin = create_remote_with_unrelated_commit(tmp_path, repo)
    writer = tmp_path / "slide-writer"
    historical = {"date": "2020-01-01", "title": "Unrecoverable legacy row",
                  "url": "https://example.com/history", "extra": {"keep": True}}
    rows = json.loads((writer / SEARCH_PATH).read_text(encoding="utf-8"))
    rows.extend([historical, historical.copy(),
                 {"date": REPORT_DATE.isoformat(), "title": "held", "url": "https://example.com/held",
                  "type": "news", "capture_schema": 1},
                 {"date": "2026-07-17", "title": "Remote-only slide", "type": "slide", "slide_schema": 1,
                  "url": "/presentations/day_slides/day_slide_2026_07_17.html"}])
    (writer / SEARCH_PATH).write_bytes(build_search_index.json_bytes(rows))
    slide = writer / "presentations/day_slides/day_slide_2026_07_18.html"
    slide.write_text('<title>Concurrent slide</title><meta name="description" content="New slide summary">', encoding="utf-8")
    git(writer, "add", SEARCH_PATH, "presentations/day_slides/day_slide_2026_07_18.html")
    git(writer, "commit", "-m", "concurrent search updates")
    git(writer, "push", "origin", "main")
    item = prepare_search_bundle(repo, "\u65b0\u3057\u3044\u65e5\u672c\u8a9e\u306e\u898b\u51fa\u3057")
    build_search_index.write_index(repo)
    return repo, writer, origin, historical, item


def test_strict_retry_preserves_remote_search_history_and_regenerates_projection(tmp_path):
    repo, writer, origin, historical, item = create_search_race(tmp_path)
    local_history = dict(historical, title="Local-only legacy row", url="https://example.com/local-history")
    local_rows = json.loads((repo / SEARCH_PATH).read_text(encoding="utf-8"))
    local_rows.extend([local_history, local_history.copy()])
    (repo / SEARCH_PATH).write_bytes(build_search_index.json_bytes(local_rows))

    result = publish_daily_report.publish(repo, REPORT_DATE, "publish", push=True, require_quality=True)

    assert result == 0
    rows = json.loads(git(tmp_path, "--git-dir", str(origin), "show", f"main:{SEARCH_PATH}").stdout)
    assert rows.count(historical) == 2, "baseline-only history, fields and duplicates must survive"
    assert rows.count(local_history) == 2
    assert any(row["title"] == "Remote-only slide" for row in rows)
    assert any(row["title"] == "Concurrent slide" and row["summary"] == "New slide summary" for row in rows)
    current = [row for row in rows if row["url"] == item["url"]]
    assert len(current) == 1
    assert current[0]["title"] == item["title"]
    assert not any(row["url"] == "https://example.com/held" for row in rows)
    assert publish_daily_report._check_daily_publication(repo, REPORT_DATE) == []
    assert git(repo, "status", "--porcelain").stdout == ""


@pytest.mark.parametrize("invalid", ["not json", "{}", '[{"date":"2020-01-01","url":"https://example.com/lost"}]'])
def test_strict_retry_rejects_invalid_remote_search_without_pushing(tmp_path, invalid):
    repo, writer, origin, _, _ = create_search_race(tmp_path)
    (writer / SEARCH_PATH).write_text(invalid, encoding="utf-8")
    git(writer, "add", SEARCH_PATH)
    git(writer, "commit", "-m", "invalid remote corpus")
    git(writer, "push", "origin", "main")
    before = git(writer, "rev-parse", "HEAD").stdout.strip()

    assert publish_daily_report.publish(repo, REPORT_DATE, "publish", push=True, require_quality=True) == 1
    assert git(tmp_path, "--git-dir", str(origin), "rev-parse", "main").stdout.strip() == before


def test_retry_search_refreshes_a_changed_daily_type_without_adding_a_duplicate(tmp_path):
    repo, _ = create_repo(tmp_path)
    prepare_search_bundle(repo, "\u65b0\u3057\u3044\u65e5\u672c\u8a9e\u306e\u898b\u51fa\u3057")
    payload = json.loads((repo / "daily-news/data.json").read_text(encoding="utf-8"))
    payload["items"][0]["type"] = "x"
    (repo / "daily-news/data.json").write_bytes(build_search_index.json_bytes(payload))
    (repo / f"public-pages/news/daily/{REPORT_DATE}.json").write_bytes(
        build_search_index.json_bytes(build_search_index.normalize_daily_payload(payload)))
    local = {"date": REPORT_DATE.isoformat(), "url": "https://example.com/current", "title": "local",
             "capture_schema": 1, "type": "x"}
    remote = dict(local, title="remote", type="news")
    rows = build_search_index.build_index(
        repo, preservation_baseline=publish_daily_report._merge_search_baselines([local], [remote]))
    assert len(rows) == 1
    assert rows[0]["type"] == "x"


def test_strict_retry_obeys_remote_manifest_before_rebuilding_search(tmp_path, capsys):
    repo, writer, origin, _, _ = create_search_race(tmp_path)
    path = writer / "scripts/daily_report_paths.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["required"].remove(SEARCH_PATH)
    manifest["optional"].remove("public-pages/news/*.json")
    path.write_text(json.dumps(manifest), encoding="utf-8")
    git(writer, "add", "scripts/daily_report_paths.json")
    git(writer, "commit", "-m", "exclude search from manifest")
    git(writer, "push", "origin", "main")
    remote_before = git(writer, "rev-parse", "HEAD").stdout.strip()
    local_before = json.loads((repo / SEARCH_PATH).read_text(encoding="utf-8"))

    assert publish_daily_report.publish(repo, REPORT_DATE, "publish", push=True, require_quality=True) == 1
    assert "manifest excludes changed path" in capsys.readouterr().err
    assert git(tmp_path, "--git-dir", str(origin), "rev-parse", "main").stdout.strip() == remote_before
    assert json.loads((repo / SEARCH_PATH).read_text(encoding="utf-8")) == local_before
    assert git(repo, "status", "--porcelain").stdout == ""


@pytest.mark.parametrize("needs_repair", [False, True])
def test_strict_retry_does_not_amend_remote_when_local_commit_is_already_applied(tmp_path, needs_repair):
    repo, manifest = create_repo(tmp_path)
    prepare_search_bundle(repo, "\u65b0\u3057\u3044\u65e5\u672c\u8a9e\u306e\u898b\u51fa\u3057")
    build_search_index.write_index(repo)
    git(repo, "add", "--", *manifest.required)
    git(repo, "commit", "-m", "valid publication")
    origin = create_remote_with_unrelated_commit(tmp_path, repo)
    writer = tmp_path / "slide-writer"
    if needs_repair:
        slide = writer / "presentations/day_slides/day_slide_2026_07_18.html"
        slide.write_text("<title>Source-only slide needs indexing</title>", encoding="utf-8")
        git(writer, "add", "presentations/day_slides/day_slide_2026_07_18.html")
        git(writer, "commit", "-m", "new slide source")
        git(writer, "push", "origin", "main")
    remote_before = git(writer, "rev-parse", "HEAD").stdout.strip()

    assert publish_daily_report._push_with_one_rebase_retry(repo, REPORT_DATE, require_quality=True) == 0
    assert git(tmp_path, "--git-dir", str(origin), "merge-base", "--is-ancestor", remote_before, "main").returncode == 0
    if needs_repair:
        assert git(tmp_path, "--git-dir", str(origin), "rev-parse", "main^").stdout.strip() == remote_before
        rows = json.loads(git(tmp_path, "--git-dir", str(origin), "show", f"main:{SEARCH_PATH}").stdout)
        assert any(row["title"] == "Source-only slide needs indexing" for row in rows)
    else:
        assert git(tmp_path, "--git-dir", str(origin), "rev-parse", "main").stdout.strip() == remote_before
