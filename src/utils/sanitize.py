"""
Sanitization helpers for generators and repair tools.

- Decode HTML/numeric entities (including double-encoded like &amp;#NNN;)
- Repair typical mojibake (UTF-8/Shift_JIS mix) seen in this repo
- Fix broken closing tags like "E/h3>" => "</h3>"
"""
from __future__ import annotations

from html import unescape
import re


def _decode_numeric_entities(text: str) -> str:
    """Decode entities, handling double-encoded sequences by unescaping twice."""
    if not text:
        return text
    s = str(text)
    prev = None
    for _ in range(2):  # twice is enough for most &amp;#NNN; cases
        if s == prev:
            break
        prev = s
        s = unescape(s)
    return s


_RE_E_BETWEEN_NONASCII = re.compile(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])')


def _fix_date_mojibake(s: str) -> str:
    # 例: 2025/09朁E03日 → 2025/09月03日, または 09朁E03日 → 09月03日
    s = re.sub(r'(\d{4})[\./年-]?(\d{1,2})朁E(\d{1,2})日',
               lambda m: f"{m.group(1)}年{int(m.group(2)):02d}月{int(m.group(3)):02d}日", s)
    s = re.sub(r'(\d{1,2})朁E(\d{1,2})日',
               lambda m: f"{int(m.group(1)):02d}月{int(m.group(2)):02d}日", s)
    s = re.sub(r'(?<=\d)朁E(?=\d{1,2}(?:日|\b))', '月', s)
    # Shift_JIS→UTF-8 文字化けパターンの代表格（年/月/日）
    s = s.replace('蟷ｴ', '年').replace('譛・', '月').replace('譌･', '日')
    return s


def sanitize_text(text: str | None) -> str:
    """Return a safe, normalized string for titles and headings."""
    if not text:
        return ''
    s = str(text)
    s = _decode_numeric_entities(s)
    s = _fix_date_mojibake(s)
    # Remove replacement character
    s = s.replace('\uFFFD', '')
    # Remove stray ASCII 'E' sandwiched by non-ASCII (mojibake artifact)
    s = _RE_E_BETWEEN_NONASCII.sub('', s)
    # Collapse excessive whitespace
    s = re.sub(r'[\u00A0\u2000-\u200B\u3000]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def sanitize_html(html: str) -> str:
    if not html:
        return html
    out = html
    # Fix broken closing tags like E/span>, E/div>, E/p>, E/button>
    for tag in ('span', 'div', 'p', 'button', 'a', 'li', 'ul', 'ol', 'section', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        out = re.sub(fr'E\/{tag}>', f'</{tag}>', out)
    # Decode entities
    out = _decode_numeric_entities(out)
    # Fix date mojibake
    out = _fix_date_mojibake(out)
    # Remove replacement characters and stray 'E' between multibyte chars
    out = out.replace('\uFFFD', '')
    out = _RE_E_BETWEEN_NONASCII.sub('', out)
    # Ensure meta charset tag exists and is utf-8 (idempotent)
    if '<meta charset="' not in out:
        out = out.replace('<head>', '<head>\n    <meta charset="utf-8"/>', 1)
    return out
