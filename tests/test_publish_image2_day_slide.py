from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import publish_image2_day_slide as publisher


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "user.email", "test@example.invalid")
    (repo / "presentations").mkdir()
    (repo / "presentations" / "day_slides_index.html").write_text(
        "original index\n", encoding="utf-8"
    )
    (repo / "presentations" / "day_slides_list.html").write_text(
        "original list\n", encoding="utf-8"
    )
    (repo / "sitemap.xml").write_text("original sitemap\n", encoding="utf-8")
    (repo / "index.html").write_text("original home\n", encoding="utf-8")
    (repo / "feed.xml").write_text("original feed\n", encoding="utf-8")
    slides = repo / "presentations" / "day_slides"
    slides.mkdir()
    (slides / "day_slide_2026_10_02.html").write_text(
        "original older slide\n", encoding="utf-8"
    )
    (repo / "user.txt").write_text("original user work\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "initial")
    return repo


def make_plan(repo: Path) -> publisher.PublishPlan:
    page = repo / "presentations" / "day_slides" / "day_slide_2026_10_03.html"
    pptx = (
        repo
        / "presentations"
        / "day_slides"
        / "downloads"
        / "day_slide_2026_10_03_example.pptx"
    )
    image_dir = repo / "presentations" / "day_slides" / "images" / "1003"
    return publisher.PublishPlan(
        mmdd="1003",
        day=date(2026, 10, 3),
        title="Test slide",
        summary="Test summary",
        section="AI",
        slug="example",
        workspace=repo / "workspace",
        image_sources=[repo / "source.png"],
        pptx_source=repo / "source.pptx",
        page_path=page,
        pptx_path=pptx,
        image_dir=image_dir,
        image_paths=[image_dir / "cover.jpg"],
        index_path=repo / "presentations" / "day_slides_index.html",
        list_path=repo / "presentations" / "day_slides_list.html",
        sitemap_path=repo / "sitemap.xml",
    )


def install_main_fakes(monkeypatch, repo: Path, plan: publisher.PublishPlan, **overrides):
    values = {
        "repo_root": repo,
        "stage": False,
        "commit": False,
        "push": False,
        "message": None,
        "dry_run": False,
    }
    values.update(overrides)
    monkeypatch.setattr(publisher, "parse_args", lambda: SimpleNamespace(**values))
    monkeypatch.setattr(publisher, "make_plan", lambda _args: plan)
    monkeypatch.setattr(publisher, "run_finalize", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(publisher, "validate", lambda _plan: [])


def write_all_outputs(plan: publisher.PublishPlan) -> None:
    for path in publisher.git_files(plan):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"generated\n")


def test_preexisting_staged_change_rejects_before_any_output_write(
    monkeypatch, tmp_path: Path
) -> None:
    repo = make_repo(tmp_path)
    plan = make_plan(repo)
    install_main_fakes(monkeypatch, repo, plan)
    (repo / "user.txt").write_text("staged user work\n", encoding="utf-8")
    git(repo, "add", "user.txt")
    staged_before = git(repo, "diff", "--cached", "--name-only").stdout
    monkeypatch.setattr(publisher, "write_outputs", write_all_outputs)

    with pytest.raises(SystemExit):
        publisher.main()

    assert not plan.page_path.exists()
    assert git(repo, "diff", "--cached", "--name-only").stdout == staged_before
    assert (repo / "user.txt").read_text(encoding="utf-8") == "staged user work\n"


def test_failed_multi_output_generation_restores_existing_files_and_removes_new_ones(
    monkeypatch, tmp_path: Path
) -> None:
    repo = make_repo(tmp_path)
    plan = make_plan(repo)
    install_main_fakes(monkeypatch, repo, plan)

    def fail_after_partial_write(current_plan: publisher.PublishPlan) -> None:
        current_plan.index_path.write_text("partial index\n", encoding="utf-8")
        current_plan.page_path.parent.mkdir(parents=True, exist_ok=True)
        current_plan.page_path.write_text("partial page\n", encoding="utf-8")
        raise RuntimeError("injected write failure")

    monkeypatch.setattr(publisher, "write_outputs", fail_after_partial_write)

    try:
        result = publisher.main()
    except RuntimeError:
        result = 1

    assert result != 0
    assert plan.index_path.read_text(encoding="utf-8") == "original index\n"
    assert not plan.page_path.exists()


def test_finalize_failure_restores_home_feed_nav_and_preserves_untracked_work(
    monkeypatch, tmp_path: Path
) -> None:
    repo = make_repo(tmp_path)
    plan = make_plan(repo)
    install_main_fakes(monkeypatch, repo, plan)
    home = repo / "index.html"
    feed = repo / "feed.xml"
    older_slide = (
        repo / "presentations" / "day_slides" / "day_slide_2026_10_02.html"
    )
    home.write_text("user dirty home\n", encoding="utf-8")
    unrelated = repo / "untracked-user.txt"
    unrelated.write_text("preserve me\n", encoding="utf-8")
    monkeypatch.setattr(publisher, "write_outputs", write_all_outputs)

    def fail_after_wider_finalize_writes(*_args, **_kwargs) -> int:
        home.write_text("partial finalized home\n", encoding="utf-8")
        feed.write_text("partial finalized feed\n", encoding="utf-8")
        older_slide.write_text("partial nav rewrite\n", encoding="utf-8")
        return 9

    monkeypatch.setattr(publisher, "run_finalize", fail_after_wider_finalize_writes)

    result = publisher.main()

    assert result == 9
    assert home.read_text(encoding="utf-8") == "user dirty home\n"
    assert feed.read_text(encoding="utf-8") == "original feed\n"
    assert older_slide.read_text(encoding="utf-8") == "original older slide\n"
    assert unrelated.read_text(encoding="utf-8") == "preserve me\n"


def test_git_publish_rejects_dirty_secondary_output_before_writes(
    monkeypatch, tmp_path: Path
) -> None:
    repo = make_repo(tmp_path)
    plan = make_plan(repo)
    install_main_fakes(monkeypatch, repo, plan, stage=True)
    home = repo / "index.html"
    older_slide = repo / "presentations/day_slides/day_slide_2026_10_02.html"
    home.write_text("user dirty home\n", encoding="utf-8")
    older_slide.write_text("user dirty older slide\n", encoding="utf-8")

    def fail_if_called(_plan: publisher.PublishPlan) -> None:
        pytest.fail("outputs must not be written while a generated target is dirty")

    monkeypatch.setattr(publisher, "write_outputs", fail_if_called)
    head_before = git(repo, "rev-parse", "HEAD").stdout

    with pytest.raises(SystemExit, match="generated output already has local changes"):
        publisher.main()

    assert git(repo, "rev-parse", "HEAD").stdout == head_before
    assert git(repo, "diff", "--cached", "--name-only").stdout == ""
    assert home.read_text(encoding="utf-8") == "user dirty home\n"
    assert older_slide.read_text(encoding="utf-8") == "user dirty older slide\n"


def test_finalize_runs_helper_from_target_repository(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    plan = make_plan(repo)
    helper = repo / "scripts" / "finalize_day_slide.py"
    helper.parent.mkdir(parents=True)
    helper.write_text(
        "from pathlib import Path\n"
        "def finalize(mmdd, year, **kwargs):\n"
        "    Path(__file__).resolve().parents[1].joinpath('target-helper.txt').write_text(mmdd + str(year), encoding='utf-8')\n"
        "    return 0\n",
        encoding="utf-8",
    )

    assert publisher.run_finalize(plan, dry_run=False) == 0
    assert (repo / "target-helper.txt").read_text(encoding="utf-8") == "10032026"


def test_stage_includes_generated_secondary_changes_but_not_unrelated_work(
    monkeypatch, tmp_path: Path
) -> None:
    repo = make_repo(tmp_path)
    plan = make_plan(repo)
    install_main_fakes(monkeypatch, repo, plan, stage=True)
    monkeypatch.setattr(publisher, "write_outputs", write_all_outputs)
    home = repo / "index.html"
    older_slide = repo / "presentations/day_slides/day_slide_2026_10_02.html"
    unrelated = repo / "user.txt"

    def finalize_generated_outputs(*_args, **_kwargs) -> int:
        home.write_text("generated home\n", encoding="utf-8")
        older_slide.write_text("generated nav\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(publisher, "run_finalize", finalize_generated_outputs)
    unrelated.write_text("unrelated user edit\n", encoding="utf-8")

    assert publisher.main() == 0

    staged = set(git(repo, "diff", "--cached", "--name-only").stdout.splitlines())
    assert "index.html" in staged
    assert "presentations/day_slides/day_slide_2026_10_02.html" in staged
    assert "user.txt" not in staged
    assert unrelated.read_text(encoding="utf-8") == "unrelated user edit\n"
