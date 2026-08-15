from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_build_homepage_accepts_marked_latest_slide_fallbacks(tmp_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the homepage build integration test")

    script = tmp_path / "scripts" / "build-homepage-latest.js"
    script.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "build-homepage-latest.js", script)
    shutil.copy2(ROOT / "index.html", tmp_path / "index.html")

    newest_slide = max((ROOT / "presentations" / "day_slides").glob("day_slide_????_??_??.html"))
    slide_dir = tmp_path / "presentations" / "day_slides"
    slide_dir.mkdir(parents=True)
    shutil.copy2(newest_slide, slide_dir / newest_slide.name)

    result = subprocess.run(
        [node, str(script)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    updated = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'id="heroTwist"' in updated
    assert 'id="heroWhy"' in updated
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    src_twist = source.split('id="heroTwist"', 1)[1].split("</p>", 1)[0]
    out_twist = updated.split('id="heroTwist"', 1)[1].split("</p>", 1)[0]
    assert 'id="heroIdentity"' in updated
    assert "今日のAIを" in updated
    assert out_twist == src_twist
