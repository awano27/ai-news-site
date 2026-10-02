"""Shared public HTML inventory for analytics injection and coverage.

Root pages, slides/comparisons, Daily News and design articles are public.
Scratch/backup pages, image tooling and meta-refresh redirects are excluded.
"""
from pathlib import Path
import re
from html.parser import HTMLParser

PUBLIC_DIRS = ("presentations", "daily-news", "articles")


class _Head(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.redirect = False
        self.analytics = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            self.redirect = True
        if tag == "script" and attrs.get("src") == "/assets/js/analytics.js":
            self.analytics = True


def exclusion_reason(path, text):
    if re.search(r"_bak|\.bak|^(test_|tmp_)|og-image-generator", path.name, re.I):
        return "scratch, backup or image tooling"
    if _Head(text).redirect:
        return "meta-refresh redirect"
    return None


def public_html_files(root):
    root = Path(root)
    files = set(root.glob("*.html"))
    for directory in PUBLIC_DIRS:
        files.update((root / directory).rglob("*.html"))
    return sorted(files)


def analytics_present(text):
    return _Head(text).analytics


def ensure_analytics(text):
    if analytics_present(text) or _Head(text).redirect:
        return text
    return re.sub(r"</head>", '<script src="/assets/js/analytics.js" defer></script>\n</head>', text, count=1, flags=re.I)
