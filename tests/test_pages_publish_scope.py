"""GitHub Pages artifact stays on the public allowlist."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from scripts.stage_pages_site import (
    DENIED_PREFIXES,
    REQUIRED_PUBLISHED_PATHS,
    PublishSafetyError,
    loc_to_relative,
    publication_paths,
    should_publish,
    sitemap_locs,
    stage_site,
    validate_publication,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "daily_report_paths.json"
INTERNAL_PREFIXES = (
    "tasks/",
    ".claude/",
    "ops/",
    "config/",
    "docs/",
    "src/",
    "scripts/",
    "tests/",
    "script/",
    "tools/",
    "templates/",
    "outputs/",
    ".github/",
)


def test_sitemap_locations_map_to_repo_files():
    assert loc_to_relative("https://visionhub.jp/") == "index.html"
    assert loc_to_relative("https://visionhub.jp/daily-news/") == "daily-news/index.html"
    assert loc_to_relative("https://visionhub.jp/about.html") == "about.html"
    with pytest.raises(ValueError):
        loc_to_relative("https://example.com/index.html")


@pytest.mark.parametrize(
    "rel",
    [
        "tasks/lessons.md",
        ".claude/skills/daily-ai-slide-generator-skill/SKILL.md",
        "ops/ga4-setup-guide.md",
        "config/analytics.json",
        "config/indexnow.json",
        "docs/plans/2026-09-05-content-integrity/PLAN.md",
        "src/auto_collect/main.py",
        "scripts/stage_pages_site.py",
        "tests/test_pages_publish_scope.py",
        "input/day/1011.txt",
        "input/day/other.pdf",
        "README.md",
        "CLAUDE.md",
        "assets/../../tasks/lessons.md",
        "../tasks/lessons.md",
    ],
)
def test_internal_paths_are_not_publishable(rel):
    assert should_publish(rel) is False


@pytest.mark.parametrize(
    "rel",
    [
        "index.html",
        "sitemap.xml",
        "feed.xml",
        "llms.txt",
        "robots.txt",
        "CNAME",
        ".nojekyll",
        "ads.txt",
        "daily-news/archive/2099-01-01.html",
        "daily-news/data.json",
        "presentations/day_slides/day_slide_2099_01_01.html",
        "presentations/day_slides/images/0101/cover.jpg",
        "presentations/daily_reports/auto_daily_report_2099_01_01.html",
        "presentations/daily_reports/og/2099_01_01.png",
        "presentations/auto_daily_report.json",
        "news/latest.json",
        "public-pages/news/daily/2099-01-01.json",
        "public-pages/news/2099-01-01.json",
        "public-pages/api/auto_daily_report/latest.json",
        "assets/og/day_slide_2099_01_01.png",
        "articles/claim-evidence-design.html",
        "examples/claim-evidence/fixtures.json",
        "ai-news-site/index.html",
        "daily-news-csv/index.html",
        "input/day/0514.pdf",
        "6db38145acbd08b2a324f22c368e269d511a6bd952645819d1f029423a540c21.txt",
    ],
)
def test_public_and_future_daily_files_are_publishable(rel):
    assert should_publish(rel) is True


def test_daily_manifest_outputs_are_published_and_raw_input_is_not():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    day = date(2099, 1, 1)
    replacements = {
        "{MMDD}": day.strftime("%m%d"),
        "{YYYY-MM-DD}": day.isoformat(),
        "{YYYY_MM_DD}": day.strftime("%Y_%m_%d"),
        "*": "sample",
    }
    for key in ("required", "optional"):
        for pattern in manifest[key]:
            expanded = pattern
            for token, value in replacements.items():
                expanded = expanded.replace(token, value)
            if expanded.startswith("input/"):
                assert should_publish(expanded) is False
            else:
                assert should_publish(expanded) is True


def _write(root: Path, rel: str, text: str = "ok") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _required_stubs(root: Path) -> None:
    for rel in REQUIRED_PUBLISHED_PATHS:
        if rel == "sitemap.xml":
            continue
        _write(root, rel, "stub")
    _write(
        root,
        "sitemap.xml",
        """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://visionhub.jp/</loc></url>
  <url><loc>https://visionhub.jp/daily-news/archive/2099-01-01.html</loc></url>
  <url><loc>https://visionhub.jp/presentations/day_slides/day_slide_2099_01_01.html</loc></url>
</urlset>
""",
    )


def test_staging_keeps_new_daily_files_and_drops_internal_trees(tmp_path):
    root = tmp_path / "repo"
    dest = tmp_path / "site"
    _required_stubs(root)
    _write(root, "daily-news/archive/2099-01-01.html", "news")
    _write(root, "presentations/day_slides/day_slide_2099_01_01.html", "slide")
    _write(root, "presentations/day_slides/images/0101/cover.jpg", "jpg")
    _write(root, "news/latest.json", "{}")
    _write(root, "assets/og/day_slide_2099_01_01.png", "png")
    _write(root, "6db38145acbd08b2a324f22c368e269d511a6bd952645819d1f029423a540c21.txt", "key")
    _write(root, "tasks/lessons.md", "internal")
    _write(root, ".claude/skills/SKILL.md", "internal")
    _write(root, "ops/notes.md", "internal")
    _write(root, "config/analytics.json", '{"measurement_id":"G-REPLACE-ME"}')
    _write(root, "docs/plans/secret.md", "C:/Users/awano")
    _write(root, "src/main.py", "print(1)")
    _write(root, "scripts/build.py", "print(1)")
    _write(root, "tests/test_secret.py", "assert False")
    _write(root, "input/day/1011.txt", "raw notes")
    _write(root, "input/day/other.pdf", "not the linked guide")
    _write(root, "examples/claim-evidence/fixtures.json", "{}")
    _write(root, "examples/private.txt", "do not publish")

    copied = stage_site(root, dest)

    assert "daily-news/archive/2099-01-01.html" in copied
    assert (dest / "presentations/day_slides/day_slide_2099_01_01.html").read_text(encoding="utf-8") == "slide"
    assert (dest / "presentations/day_slides/images/0101/cover.jpg").is_file()
    assert (dest / "news/latest.json").is_file()
    assert (dest / "assets/og/day_slide_2099_01_01.png").is_file()
    assert (dest / "input/day/0514.pdf").is_file()
    assert (dest / "examples/claim-evidence/fixtures.json").is_file()
    assert (dest / "6db38145acbd08b2a324f22c368e269d511a6bd952645819d1f029423a540c21.txt").is_file()
    for prefix in INTERNAL_PREFIXES:
        assert not (dest / prefix).exists()
        assert not any(path.startswith(prefix) for path in copied)
    assert not (dest / "input/day/1011.txt").exists()
    assert not (dest / "input/day/other.pdf").exists()
    assert not (dest / "examples/private.txt").exists()
    assert not (dest / "config/analytics.json").exists()


def test_staging_refuses_symlink_inside_a_public_directory(tmp_path):
    root = tmp_path / "repo"
    outside = tmp_path / "secret.md"
    outside.write_text("secret", encoding="utf-8")
    _required_stubs(root)
    public = root / "assets"
    public.mkdir(parents=True, exist_ok=True)
    (public / "leak.md").symlink_to(outside)
    with pytest.raises(PublishSafetyError, match="symlink"):
        stage_site(root, tmp_path / "site")


def test_repository_sitemap_is_complete_and_internal_trees_stay_out():
    errors = validate_publication(ROOT)
    assert errors == []
    published = set(publication_paths(ROOT))
    locs = sitemap_locs((ROOT / "sitemap.xml").read_text(encoding="utf-8"))
    assert len(locs) >= 781
    for loc in locs:
        rel = loc_to_relative(loc)
        assert rel in published
        assert (ROOT / rel).is_file()
    for prefix in DENIED_PREFIXES:
        leaked = [rel for rel in published if rel.startswith(prefix) and rel not in {"input/day/0514.pdf"}]
        assert leaked == []
    for prefix in INTERNAL_PREFIXES:
        assert not any(rel.startswith(prefix) for rel in published)


def test_pages_workflow_uploads_the_staged_site_only():
    text = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    assert "stage_pages_site.py" in text
    assert 'path: ${{ runner.temp }}/pages-site' in text
    assert "path: ./" not in text
    assert "path: ." not in text
    assert "rm -rf" not in text
    assert text.index("build_sitemap.py") < text.index("stage_pages_site.py")
    assert text.index("stage_pages_site.py") < text.index("upload-pages-artifact")
    assert "|| true" not in text
