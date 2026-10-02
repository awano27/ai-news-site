from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

import yaml
import pytest


ROOT = Path(__file__).resolve().parents[1]

PLANNED_DISTRIBUTION_FILES = (
    "sources.yaml",
    "requirements-ingest.txt",
    "scripts/config.py",
    "scripts/ingest.py",
    "scripts/validate.py",
    "scripts/public_html.py",
    "scripts/collectors/producthunt.py",
    "scripts/collectors/github.py",
    "src/generators/detail_analysis_generator.py",
    "src/auto_collect/output_validation.py",
    "script/pages_heal.py",
    ".github/workflows/publish-generated-content.yml",
)

AUTO_PUSH_WORKFLOWS = (
    "auto-daily-report-cloud-fallback.yml",
    "ai-news.yml",
    "update-news.yml",
    "ingest.yml",
    "presentations-daily.yml",
    "build-ranking-preview.yml",
    "daily-archive.yml",
    "generate-daily-news-json.yml",
)


def load_workflow(name: str) -> dict:
    return yaml.load(
        (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )


def test_clean_checkout_dependencies_are_individually_unignored():
    for relative in PLANNED_DISTRIBUTION_FILES:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", relative],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 1, f"required clean-checkout file is still ignored: {relative}"


def test_planned_clean_tree_imports_pipeline_entrypoints(tmp_path):
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8").split("\0")
    distributed = {path for path in tracked if path}
    distributed.update(PLANNED_DISTRIBUTION_FILES)

    needed_prefixes = ("script/", "scripts/", "src/", ".github/workflows/")
    needed_files = {"setup.py", "sources.yaml", "requirements-ingest.txt"}
    for relative in sorted(distributed):
        if relative not in needed_files and not relative.startswith(needed_prefixes):
            continue
        source = ROOT / relative
        if not source.is_file():
            continue
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    command = textwrap.dedent(
        """
        import json
        from pathlib import Path
        import subprocess
        import sys
        from unittest.mock import patch
        import yaml

        import script.build_news as build_news
        import scripts.config
        import scripts.ingest as ingest
        import scripts.validate as validate
        import scripts.collectors.producthunt
        import scripts.collectors.github
        import scripts.publish_daily_report
        import src.auto_collect.main
        from src.generators.detail_analysis_generator import DetailAnalysisGenerator

        for workflow_path in Path(".github/workflows").glob("*.yml"):
            yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

        build_news.load_sources()
        news_dir = Path("fixture-news")
        build_news.NEWS_DIR = str(news_dir)
        with patch.object(build_news, "load_sources", return_value=([], [], None, [], [])), \
             patch.object(build_news, "load_manual_sns", return_value=[]):
            build_news.main()
        assert json.loads((news_dir / "latest.json").read_text(encoding="utf-8"))["sections"] == {
            "business": [], "tools": [], "company": [], "sns": []
        }

        data_dir = Path("fixture-data")
        daily_dir = data_dir / "daily"
        daily_dir.mkdir(parents=True)
        tools_file = data_dir / "tools.json"
        index_file = data_dir / "index.json"
        fixture_tool = {
            "id": "fixture-tool", "name": "Fixture Tool", "tagline": "Offline fixture",
            "categories": ["dev"], "links": {"official": "https://example.com/tool"},
            "first_seen_at": "2026-10-03", "source": "manual", "published": False,
        }
        for module in (ingest, validate):
            module.TOOLS_FILE = tools_file
            module.INDEX_FILE = index_file
            module.DAILY_DIR = daily_dir
        with patch.object(ingest, "collect_all", return_value=[fixture_tool]), \
             patch.object(sys, "argv", ["ingest.py", "--date", "2026-10-03"]):
            ingest.main()
        with patch.object(sys, "argv", ["validate.py"]):
            try:
                validate.main()
            except SystemExit as exc:
                assert exc.code == 0

        detail_root = Path("fixture-detail")
        (detail_root / "news").mkdir(parents=True)
        (detail_root / "news" / "latest.json").write_text(
            json.dumps({"generated_at": "2026-10-03T00:00:00+09:00", "sections": {}}),
            encoding="utf-8",
        )
        dated, latest = DetailAnalysisGenerator(
            root=detail_root, output_dir=detail_root / "presentations"
        ).generate()
        assert dated.is_file() and latest.is_file()

        Path("fixture.html").write_text(
            "<!doctype html><html><head></head><body>fixture</body></html>",
            encoding="utf-8",
        )
        subprocess.run([sys.executable, "scripts/inject_analytics.py"], check=True)
        assert '/assets/js/analytics.js' in Path("fixture.html").read_text(encoding="utf-8")
        subprocess.run([sys.executable, "scripts/check_analytics_coverage.py"], check=True)
        """
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr


def test_generated_commit_is_validated_then_deployed_at_the_same_sha():
    publish = load_workflow("publish-generated-content.yml")
    assert publish["jobs"]["validate"]["uses"] == "./.github/workflows/freshness-guard.yml"
    assert publish["jobs"]["deploy"]["needs"] == "validate"
    assert publish["jobs"]["deploy"]["uses"] == "./.github/workflows/pages.yml"
    assert publish["jobs"]["validate"]["with"]["ref"] == "${{ inputs.ref }}"
    assert publish["jobs"]["deploy"]["with"]["ref"] == "${{ inputs.ref }}"

    pages = load_workflow("pages.yml")
    assert pages["on"]["workflow_call"]["inputs"]["ref"]["required"] == "true"
    checkout = pages["jobs"]["build"]["steps"][0]
    assert checkout["with"]["ref"] == "${{ inputs.ref || github.sha }}"
    build_steps = pages["jobs"]["build"]["steps"]
    build_public = next(step for step in build_steps if step.get("id") == "revision")
    validate_public = next(step for step in build_steps if step.get("name") == "Validate generated public artifact")
    assert "scripts/inject_analytics.py" in build_public["run"]
    assert "deployment-revision.json" in build_public["run"]
    assert build_steps.index(build_public) < build_steps.index(validate_public)
    assert "scripts/check_site_freshness.py" in validate_public["run"]
    assert "scripts/check_analytics_coverage.py" in validate_public["run"]
    verify_run = pages["jobs"]["verify"]["steps"][0]["run"]
    assert "deployment-revision.json" in verify_run
    assert "EXPECTED_SHA" in verify_run

    freshness = load_workflow("freshness-guard.yml")
    assert freshness["on"]["workflow_call"]["inputs"]["ref"]["required"] == "true"
    assert freshness["jobs"]["check"]["steps"][0]["with"]["ref"] == "${{ inputs.ref || github.sha }}"
    raw_coverage = next(
        step for step in freshness["jobs"]["check"]["steps"]
        if step.get("name") == "Verify analytics coverage"
    )
    assert "inputs.ref == ''" in raw_coverage["if"]

    for name in AUTO_PUSH_WORKFLOWS:
        workflow = load_workflow(name)
        publish_job = workflow["jobs"]["publish"]
        assert publish_job["uses"] == "./.github/workflows/publish-generated-content.yml", name
        assert "generated_ref" in publish_job["with"]["ref"], name


def test_pages_heal_distinguishes_probe_dispatch_and_recovery():
    from script.pages_heal import HealStatus, classify_heal

    assert classify_heal(0) is HealStatus.HEALTHY
    assert classify_heal(2, dispatch_succeeded=False) is HealStatus.DISPATCH_REJECTED
    assert classify_heal(2, dispatch_succeeded=True) is HealStatus.DISPATCH_ACCEPTED
    assert classify_heal(2, dispatch_succeeded=True, recovery_failures=0) is HealStatus.RECOVERED
    assert classify_heal(2, dispatch_succeeded=True, recovery_failures=1) is HealStatus.RECOVERY_FAILED

    workflow_text = (ROOT / ".github" / "workflows" / "pages-heal.yml").read_text(encoding="utf-8")
    workflow = load_workflow("pages-heal.yml")
    assert workflow["permissions"]["actions"] == "write"
    assert "/pages/builds" not in workflow_text
    dispatch_step = next(step for step in workflow["jobs"]["probe"]["steps"] if step.get("id") == "dispatch")
    assert "gh workflow run pages.yml" in dispatch_step["run"]
    assert "|| true" not in dispatch_step["run"]


@pytest.mark.parametrize('args,status,exit_code', [
    (['--initial-failures', '0'], 'healthy', 0),
    (['--initial-failures', '1', '--dispatch-succeeded', 'false'], 'dispatch_rejected', 1),
    (['--initial-failures', '1', '--dispatch-succeeded', 'true'], 'dispatch_accepted', 1),
    (['--initial-failures', '1', '--dispatch-succeeded', 'true', '--recovery-failures', '1'], 'recovery_failed', 1),
    (['--initial-failures', '1', '--dispatch-succeeded', 'true', '--recovery-failures', '0'], 'recovered', 0),
])
def test_mock_heal_observations_reach_process_exit(args, status, exit_code):
    result = subprocess.run([sys.executable, str(ROOT / 'script/pages_heal.py'), *args],
                            text=True, capture_output=True, encoding='utf-8')
    assert result.returncode == exit_code
    assert result.stdout.strip() == status


def test_detail_analysis_chart_data_cannot_close_script_element(tmp_path):
    detail = importlib.import_module("src.generators.detail_analysis_generator")
    generator = detail.DetailAnalysisGenerator(root=tmp_path, output_dir=tmp_path / "presentations")
    payload = "</script><img src=x onerror=alert(1)>&"
    html = generator.render_html(
        {"generated_at": "2026-10-03T00:00:00+09:00"},
        {
            "item_count": 0,
            "categories": [(payload, 1)],
            "sources": [(payload, 1)],
            "timeline": [],
            "top_items": [],
            "day_entries": [],
        },
    )
    assert payload not in html
    assert r"\u003c/script\u003e\u003cimg" in html
