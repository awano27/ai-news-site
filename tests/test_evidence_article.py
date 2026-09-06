"""The permanent article must stay bound and reachable after a daily rebuild."""
import json
from pathlib import Path
import re
import shutil
import subprocess

from scripts.render_claim_evidence import DEFAULT_PAGES, check_static_page, render_static_page

ROOT = Path(__file__).resolve().parents[1]
ARTICLE = "articles/claim-evidence-design.html"


def test_article_is_in_preflight_and_changed_body_is_rejected():
    assert ARTICLE in DEFAULT_PAGES
    assert check_static_page(ROOT / ARTICLE) == []
    text = (ROOT / ARTICLE).read_text(encoding="utf-8")
    changed = text.replace('data-claim-id="ART-FINGERPRINT">', 'data-claim-id="ART-FINGERPRINT">変更した説明。', 1)
    assert any("body text differs" in error for error in render_static_page(changed)[1])


def test_resource_entry_survives_existing_homepage_generation(tmp_path):
    node = shutil.which("node")
    assert node, "Node is required to verify the existing homepage generator"
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    about = (ROOT / "about.html").read_text(encoding="utf-8")
    assert index.count(f'href="{ARTICLE}"') == 1
    assert about.count(f'href="/{ARTICLE}"') == 1
    resources = re.search(r'<section id="resources".*?</section>', index, re.S).group()
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts/build-homepage-latest.js", scripts / "build-homepage-latest.js")
    # Preserve the LF checkout required by .gitattributes and the existing
    # generator; text-mode writes on Windows would create a different fixture.
    shutil.copy2(ROOT / "index.html", tmp_path / "index.html")
    slides = tmp_path / "presentations/day_slides"
    slides.mkdir(parents=True)
    (slides / "day_slide_2026_09_05.html").write_text("<title>固定した生成テスト</title><h1>固定した生成テスト</h1>", encoding="utf-8")
    api = tmp_path / "public-pages/api/auto_daily_report"
    api.mkdir(parents=True)
    (api / "latest.json").write_text(json.dumps({"date": "2026-09-05", "headlines": []}), encoding="utf-8")
    clock = tmp_path / "fixed-clock.cjs"
    clock.write_text("const D=Date;global.Date=class extends D{constructor(...a){super(...(a.length?a:['2026-09-05T03:00:00Z']));}static now(){return new D('2026-09-05T03:00:00Z').getTime();}};", encoding="utf-8")
    result = subprocess.run([node, "--require", str(clock), str(scripts / "build-homepage-latest.js")], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    after = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert re.search(r'<section id="resources".*?</section>', after, re.S).group() == resources
