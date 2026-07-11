from pathlib import Path

from scripts import inject_slide_nav


def test_inject_distinguishes_changed_unchanged_and_skipped_no_body(tmp_path: Path) -> None:
    block = "<!-- slide-nav:start -->\n<nav>links</nav>\n<!-- slide-nav:end -->"
    injectable = tmp_path / "injectable.html"
    injectable.write_text("<html><body>slide</body></html>", encoding="utf-8")
    no_body = tmp_path / "no-body.html"
    no_body.write_text("<html><main>slide</main></html>", encoding="utf-8")

    assert inject_slide_nav.inject(injectable, block) == "changed"
    assert inject_slide_nav.inject(injectable, block) == "unchanged"
    assert inject_slide_nav.inject(no_body, block) == "skipped-no-body"
    assert no_body.read_text(encoding="utf-8") == "<html><main>slide</main></html>"


def test_main_reports_each_no_body_skip_and_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    slides = tmp_path / "day_slides"
    slides.mkdir()
    (slides / "day_slide_2026_07_09.html").write_text(
        "<html><body>first</body></html>", encoding="utf-8"
    )
    no_body = slides / "day_slide_2026_07_10.html"
    no_body_contents = (
        "<html><main>missing body close</main>"
        "<!-- slide-nav:start --><nav>existing</nav><!-- slide-nav:end --></html>"
    )
    no_body.write_text(no_body_contents, encoding="utf-8")
    monkeypatch.setattr(inject_slide_nav, "SLIDES", slides)

    assert inject_slide_nav.main() == 0

    output = capsys.readouterr().out
    assert no_body.read_text(encoding="utf-8") == no_body_contents
    assert "day_slide_2026_07_10.html: skipped (no </body>)" in output
    assert "[inject_slide_nav] 2 files, 1 changed, 1 skipped" in output
