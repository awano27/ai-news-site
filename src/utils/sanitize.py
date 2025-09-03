"""
Utilities to sanitize text and HTML output across generators.

Goals:
- Ensure numeric character entities like &amp;#32; or fullwidth variants decode
- Repair common broken-closing-tag artifacts like "E/span>" -> "</span>"
- Provide a safe normalize_text helper for plain strings
"""
from __future__ import annotations

from html import unescape
import re

_NUM_ENTITY_RE = re.compile(r'([&\uFF06])amp;([#\uFF03])(\d+);')

def _decode_numeric_entities(text: str) -> str:
    def repl(m: re.Match) -> str:
        try:
            return chr(int(m.group(3)))
        except Exception:
            return ' '
    return _NUM_ENTITY_RE.sub(repl, text)

def normalize_text(text: str | None) -> str:
    if not text:
        return ''
    s = str(text)
    # First, decode any numeric entities (including fullwidth ＆＃nnn; forms)
    s = _decode_numeric_entities(s)
    # Then, unescape standard HTML entities repeatedly until stable
    prev = None
    for _ in range(3):
        if s == prev:
            break
        prev = s
        s = unescape(s)
    # Collapse weird whitespace artifacts
    s = re.sub(r'[\u00A0\u2000-\u200B\u3000]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def sanitize_html(html: str) -> str:
    if not html:
        return html
    out = html
    # Fix broken closing tags like E/span>, E/div>, E/p>, E/button>
    for tag in ('span','div','p','button','h1','h2','h3','h4','h5','h6'):
        out = re.sub(fr'E\/{tag}>', f'</{tag}>', out)
    # Decode numeric entities (standard and fullwidth forms)
    out = _decode_numeric_entities(out)
    # Fix specific corrupted date pattern: YYYY年MM朁EDD日 -> YYYY年MM月DD日
    out = re.sub(r"(\d{4})年(\d{1,2})朁E(\d{1,2})日", lambda m: f"{m.group(1)}年{int(m.group(2)):02d}月{int(m.group(3)):02d}日", out)
    # Fix standalone month name like '8朁E' -> '8月' (avoid touching adjacent digits)
    out = re.sub(r"(?<!\d)([1-9]|(?<!\\d)([1-9]|1[0-2])朁E(?!\\d)", lambda m: f"{int(m.group(1))}月", out)
    # Ensure meta charset tag exists and is utf-8 (idempotent)
    if '<meta charset="' not in out:
        out = out.replace('<head>', '<head>\n    <meta charset="utf-8"/>', 1)
    return out

