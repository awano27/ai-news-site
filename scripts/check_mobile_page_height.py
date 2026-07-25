"""Measure the local top page at the acceptance-test viewports."""

from __future__ import annotations

import functools
import http.server
import json
import threading
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


REPO = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO / "outputs" / "mobile_height_2026-07-25"
VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1440, "height": 900},
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


def page_snapshot(page: Page) -> dict[str, object]:
    return page.evaluate(
        """() => {
          const visible = el => {
            const style = getComputedStyle(el);
            return style.display !== 'none' && style.visibility !== 'hidden' &&
              el.getBoundingClientRect().height > 0;
          };
          const button = document.querySelector('#resources .res-expand');
          const grid = document.querySelector('#resources .res-grid');
          return {
            scrollHeight: document.documentElement.scrollHeight,
            sections: Array.from(document.querySelectorAll('main section')).map(section => ({
              id: section.id || '(no id)',
              height: Math.round(section.getBoundingClientRect().height),
            })),
            visibleResourceCards: Array.from(
              document.querySelectorAll('#resources .res-card')
            ).filter(visible).length,
            resourceLinksInDom: document.querySelectorAll(
              '#resources a.res-card[href]'
            ).length,
            resourceColumns: grid ? getComputedStyle(grid).gridTemplateColumns.split(' ').length : 0,
            buttonVisible: button ? visible(button) : false,
            buttonHeight: button ? Math.round(button.getBoundingClientRect().height) : 0,
            buttonExpanded: button ? button.getAttribute('aria-expanded') : null,
            staticGridClass: grid ? grid.getAttribute('class') : null,
          };
        }"""
    )


def open_page(page: Page, url: str) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url, wait_until="networkidle")
    return errors


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(QuietHandler, directory=str(REPO))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/index.html"
    results: dict[str, object] = {}

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for name, viewport in VIEWPORTS.items():
                page = browser.new_page(viewport=viewport)
                errors = open_page(page, url)
                before = page_snapshot(page)
                page.screenshot(
                    path=str(
                        OUTPUT_DIR /
                        ("mobile_collapsed.png" if name == "mobile" else "desktop.png")
                    ),
                    full_page=True,
                )
                result: dict[str, object] = {
                    "viewport": viewport,
                    "beforeExpand": before,
                    "consoleErrors": errors,
                }
                if name == "mobile":
                    page.locator("#resources .res-expand").click()
                    after = page_snapshot(page)
                    page.screenshot(
                        path=str(OUTPUT_DIR / "mobile_expanded.png"),
                        full_page=True,
                    )
                    result["afterExpand"] = after
                results[name] = result
                page.close()
            no_js_context = browser.new_context(
                viewport=VIEWPORTS["mobile"],
                java_script_enabled=False,
            )
            no_js_page = no_js_context.new_page()
            no_js_page.goto(url, wait_until="load")
            results["mobileNoJavaScript"] = page_snapshot(no_js_page)
            no_js_context.close()
            browser.close()
        results["staticHtmlHasCollapsedGridClass"] = (
            'class="res-grid is-collapsed"' in
            (REPO / "index.html").read_text(encoding="utf-8")
        )
    finally:
        server.shutdown()
        server.server_close()

    log_path = OUTPUT_DIR / "measurement.txt"
    log_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(log_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
