"""
Sanitization helpers for generators and repair tools.

- Decode numeric entities
- Repair typical mojibake (Shift_JIS⇔UTF-8) patterns in Japanese text
- Fix broken closing tags like "E/h3>" => "</h3>"
"""
from __future__ import annotations

from html import unescape
import re

_NUM_ENTITY_RE = re.compile(r'(&|\uFF06)amp;([#\uFF03])(\d+);')

def _decode_numeric_entities(text: str) -> str:
    def repl(m: re.Match) -> str:
        try:
            return chr(int(m.group(3)))
        except Exception:
            return ' '
    return _NUM_ENTITY_RE.sub(repl, text)

def sanitize_text(text: str | None) -> str:
    """Return a safe, normalized string for titles and headings."""
    if not text:
        return ''
    s = str(text)
    s = _decode_numeric_entities(s)
    # Undo common date mojibake: 2025蟷ｴ09譛・03譌･
    s = re.sub(r'(\d{4})蟷ｴ(\d{1,2})譛・(\d{1,2})譌･', lambda m: f"{m.group(1)}年{int(m.group(2)):02d}月{int(m.group(3)):02d}日", s)
    # Replace residual tokens
    s = s.replace('蟷ｴ','年').replace('譛・','月').replace('譌･','日').replace('朁E','月')
    # Collapse whitespace
    s = re.sub(r'[\u00A0\u2000-\u200B\u3000]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # Unescape entities
    prev=None
    for _ in range(2):
        if s == prev: break
        prev=s; s = unescape(s)
    return s

def sanitize_html(html: str) -> str:
    if not html:
        return html
    out = html
    # Fix broken closing tags like E/span>, E/div>, E/p>, E/button>
    for tag in ('span','div','p','button','h1','h2','h3','h4','h5','h6','section'):
        out = re.sub(fr'E\/{tag}>', f'</{tag}>', out)
    # Decode numeric entities
    out = _decode_numeric_entities(out)
    # Fix date mojibake
    out = re.sub(r'(\d{4})蟷ｴ(\d{1,2})譛・(\d{1,2})譌･', lambda m: f"{m.group(1)}年{int(m.group(2)):02d}月{int(m.group(3)):02d}日", out)
    out = out.replace('蟷ｴ','年').replace('譛・','月').replace('譌･','日').replace('朁E','月')
    # Ensure meta charset tag exists and is utf-8 (idempotent)
    if '<meta charset="' not in out:
        out = out.replace('<head>', '<head>\n    <meta charset="utf-8"/>', 1)
    return out

