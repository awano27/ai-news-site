#!/usr/bin/env python3
"""Ping IndexNow. Default is dry-run (print payload, do not POST).

    py -3 scripts/indexnow_ping.py
    py -3 scripts/indexnow_ping.py --urls https://visionhub.jp/presentations/day_slides/day_slide_2026_09_13.html
    py -3 scripts/indexnow_ping.py --from-sitemap-diff --dry-run
    py -3 scripts/indexnow_ping.py --urls ... --send
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "indexnow.json"
SITEMAP = ROOT / "sitemap.xml"
ENDPOINT = "https://api.indexnow.org/indexnow"
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
HOST = "visionhub.jp"


def load_config(path: Path = CONFIG) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    key = str(data.get("key") or "")
    if not (32 <= len(key) <= 64) or any(c not in "0123456789abcdefABCDEF" for c in key):
        raise SystemExit("indexnow key must be 32-64 hex characters")
    location = str(data.get("key_location") or f"https://{HOST}/{key}.txt")
    return {"key": key, "key_location": location}


def sitemap_locs(text: str) -> list[str]:
    return LOC_RE.findall(text or "")


def urls_from_sitemap_diff() -> list[str]:
    current = sitemap_locs(SITEMAP.read_text(encoding="utf-8") if SITEMAP.is_file() else "")
    try:
        proc = subprocess.run(
            ["git", "show", "HEAD:sitemap.xml"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        previous = sitemap_locs(proc.stdout) if proc.returncode == 0 else []
    except OSError:
        previous = []
    prev_set = set(previous)
    added = [u for u in current if u not in prev_set]
    return added or current[:1]


def payload_for(urls: list[str], cfg: dict) -> dict:
    return {
        "host": HOST,
        "key": cfg["key"],
        "keyLocation": cfg["key_location"],
        "urlList": urls,
    }


def post_indexnow(payload: dict) -> int:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"[indexnow] POST {ENDPOINT} status={resp.status}")
            return 0 if 200 <= resp.status < 300 else 1
    except OSError as exc:
        print(f"[indexnow] POST failed: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--urls", nargs="*", default=[])
    ap.add_argument("--from-sitemap-diff", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="Print payload only (default)")
    ap.add_argument("--send", action="store_true", help="Actually POST to IndexNow")
    args = ap.parse_args(argv)

    cfg = load_config()
    urls = list(args.urls)
    if args.from_sitemap_diff:
        urls.extend(urls_from_sitemap_diff())
    urls = list(dict.fromkeys(u.strip() for u in urls if u.strip()))
    if not urls:
        print("[indexnow] no URLs", file=sys.stderr)
        return 1

    payload = payload_for(urls, cfg)
    send = args.send and not args.dry_run
    if not send:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("[indexnow] dry-run (not sent)")
        return 0
    return post_indexnow(payload)


if __name__ == "__main__":
    raise SystemExit(main())
