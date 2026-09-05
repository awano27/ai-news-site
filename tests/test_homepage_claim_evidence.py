"""Existing homepage JSON consumer must not change claim review provenance."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from src.auto_collect.content_integrity import CRUSOE_2026_09_05_URL, apply_article_correction

ROOT = Path(__file__).resolve().parents[1]


def test_homepage_json_preserves_optional_evidence_and_links_to_dated_detail(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed by the existing homepage generator")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts/build-homepage-latest.js", scripts / "build-homepage-latest.js")
    shutil.copy2(ROOT / "index.html", tmp_path / "index.html")
    slides = tmp_path / "presentations/day_slides"
    slides.mkdir(parents=True)
    (slides / "day_slide_2026_09_05.html").write_text('<title>固定テスト</title><h1>固定テスト</h1>', encoding="utf-8")
    api = tmp_path / "public-pages/api/auto_daily_report"
    api.mkdir(parents=True)
    item = apply_article_correction({"url": CRUSOE_2026_09_05_URL, "category": "Business", "score": 85})
    data = {"date": "2026-09-05", "headlines": [item, {"title": "Legacy", "summary": "旧データ", "url": "https://example.com/legacy", "score": 70}]}
    (api / "latest.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    clock = tmp_path / "fixed-clock.cjs"
    clock.write_text("const D=Date;global.Date=class extends D {constructor(...a){super(...(a.length?a:['2026-09-05T03:00:00Z']));}static now(){return new D('2026-09-05T03:00:00Z').getTime();}};", encoding="utf-8")
    result = subprocess.run([node, "--require", str(clock), str(scripts / "build-homepage-latest.js")], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    generated = json.loads((tmp_path / "news/latest.json").read_text(encoding="utf-8"))
    records = [r for group in generated["sections"].values() for r in group]
    target = next(r for r in records if r["source"]["url"] == CRUSOE_2026_09_05_URL)
    assert target["claim_evidence"] == item["claim_evidence"]
    assert target["evidence_url"].endswith("auto_daily_report_2026_09_05.html#evidence-crusoe-valuation")
    assert "claim_evidence" not in next(r for r in records if r["title"] == "Legacy")
