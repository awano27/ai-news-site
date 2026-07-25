"""Verify local hero readability at the acceptance-test viewports."""

from __future__ import annotations

import functools
import http.server
import json
import threading
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


REPO = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO / "outputs" / "hero_readability_2026-07-25"
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
          const rect = selector => {
            const el = document.querySelector(selector);
            const box = el ? el.getBoundingClientRect() : null;
            return box ? {
              top: Math.round(box.top * 10) / 10,
              bottom: Math.round(box.bottom * 10) / 10,
              width: Math.round(box.width * 10) / 10,
              height: Math.round(box.height * 10) / 10,
            } : null;
          };
          const visible = selector => {
            const el = document.querySelector(selector);
            if (!el) return false;
            const style = getComputedStyle(el);
            return style.display !== 'none' && style.visibility !== 'hidden' &&
              el.getBoundingClientRect().height > 0;
          };
          const resources = performance.getEntriesByType('resource')
            .filter(entry => /hero-planck/i.test(entry.name))
            .map(entry => ({
              url: entry.name,
              transferBytes: entry.transferSize,
              encodedBodyBytes: entry.encodedBodySize,
              decodedBodyBytes: entry.decodedBodySize,
              initiatorType: entry.initiatorType,
            }));
          const bg = document.querySelector('.hero-bg');
          return {
            pageHeight: document.documentElement.scrollHeight,
            hero: rect('.hero'),
            h1: rect('.hero h1'),
            heroSlideBtn: rect('#heroSlideBtn'),
            heroBackground: {
              rect: rect('.hero-bg'),
              computedWidth: bg ? getComputedStyle(bg).width : null,
              backgroundImage: bg ? getComputedStyle(bg).backgroundImage : null,
            },
            heroResources: resources,
            resExpandVisible: visible('#resources .res-expand'),
            heroDynamicContent: {
              date: document.querySelector('#heroDate')?.textContent.trim() || null,
              newsTitle: document.querySelector('#heroNewsTitle')?.textContent.trim() || null,
              newsMeta: document.querySelector('#heroNewsMeta')?.textContent.trim() || null,
              slideHref: document.querySelector('#heroSlideBtn')?.href || null,
            },
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
    results: dict[str, object] = {"localUrl": url}

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()

            mobile = browser.new_page(viewport=VIEWPORTS["mobile"])
            mobile_errors = open_page(mobile, url)
            results["mobile"] = {
                "viewport": VIEWPORTS["mobile"],
                "metrics": page_snapshot(mobile),
                "consoleErrors": mobile_errors,
                "consoleErrorCount": len(mobile_errors),
            }
            mobile.screenshot(
                path=str(OUTPUT_DIR / "mobile_first_view.png"),
                full_page=False,
            )
            mobile.locator(".hero").screenshot(
                path=str(OUTPUT_DIR / "mobile_hero_full.png"),
            )
            mobile.close()

            desktop = browser.new_page(viewport=VIEWPORTS["desktop"])
            desktop_errors = open_page(desktop, url)
            results["desktop"] = {
                "viewport": VIEWPORTS["desktop"],
                "metrics": page_snapshot(desktop),
                "consoleErrors": desktop_errors,
                "consoleErrorCount": len(desktop_errors),
            }
            desktop.locator(".hero").screenshot(
                path=str(OUTPUT_DIR / "desktop_hero.png"),
            )
            desktop.close()
            browser.close()

        html = (REPO / "index.html").read_text(encoding="utf-8")
        results["staticChecks"] = {
            "fallbackStartCount": html.count("<!-- fallback:latest-slide -->"),
            "fallbackEndCount": html.count("<!-- fallback:end -->"),
            "noscriptPresent": "<noscript>" in html and "</noscript>" in html,
        }
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
