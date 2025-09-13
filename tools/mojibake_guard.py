#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from typing import Dict, Tuple

try:
    from ftfy import fix_text  # type: ignore
except Exception:  # pragma: no cover - ftfy optional at runtime
    def fix_text(s: str) -> str:  # fallback no-op
        return s


RULES_PATH = Path('config/mojibake_rules.json')


def load_rules(path: Path = RULES_PATH) -> Dict:
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {
        'enforce_utf8_meta': True,
        'fix_e_slash_tags': True,
        'replace_pua_symbols': {},
        # Representative mojibake tokens observed in repo snapshots
        'forbid_tokens': [
            '郢', '邵', '陷', '隴', '陝', '鬯', '髫', '鬩',
            '蟷ｴ', '譛', '譌', '縺', '繝', '繧', '・ｽ', '窶ｦ',
        ],
        'fail_on_forbid': True,
        'remove_forbid': True,
        'try_cp932_roundtrip': False,
    }


_E_SLASH_TAG = re.compile(r'E\/(h[1-6]|p|div|span|a|li|ul|ol|section|strong|em|button)>')


def ensure_utf8_meta(html: str) -> str:
    if '<meta charset="' not in html:
        return html.replace('<head>', '<head>\n  <meta charset="utf-8">', 1)
    return html


def fix_e_slash_tags(html: str) -> str:
    # Replace occurrences like E/h3> with </h3>
    return _E_SLASH_TAG.sub(lambda m: f'</{m.group(1)}>', html)


def replace_pua(text: str, mapping: Dict[str, str]) -> str:
    out = text
    for k, v in mapping.items():
        out = out.replace(k, v)
    # Remove Private Use Area chars by default if not explicitly mapped
    out = re.sub(r'[\uE000-\uF8FF]', '', out)
    return out


def normalize_text(text: str) -> str:
    if not text:
        return ''
    s = fix_text(str(text))
    s = unescape(unescape(s))  # handle double-encoded entities
    s = s.replace('\uFFFD', '')
    # remove stray ASCII 'E' sandwiched by multibyte chars
    s = re.sub(r'(?<=[^\x00-\x7F])E(?=[^\x00-\x7F])', '', s)
    # collapse whitespace
    s = re.sub(r'[\u00A0\u2000-\u200B\u3000]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def remove_forbid(text: str, forbid_tokens) -> str:
    if not forbid_tokens:
        return text
    # Build a regex that matches any of the tokens (escape non-ascii safely)
    pats = [re.escape(t) for t in forbid_tokens if t]
    if not pats:
        return text
    rx = re.compile("(" + "|".join(pats) + ")")
    return rx.sub("", text)


def detect_mojibake(text: str, forbid_tokens) -> Tuple[bool, Dict[str, int]]:
    counts = {tok: text.count(tok) for tok in forbid_tokens}
    total = sum(counts.values())
    return (total > 0), counts


def try_cp932_roundtrip(text: str) -> str:
    try:
        return text.encode('cp932', errors='ignore').decode('utf-8', errors='ignore')
    except Exception:
        return text


def sanitize_and_enforce(html: str, rules: Dict | None = None) -> Tuple[str, Dict]:
    rules = rules or load_rules()
    out = html
    out = normalize_text(out)
    if rules.get('enforce_utf8_meta', True):
        out = ensure_utf8_meta(out)
    if rules.get('fix_e_slash_tags', True):
        out = fix_e_slash_tags(out)
    out = replace_pua(out, rules.get('replace_pua_symbols', {}))
    # Optionally attempt round-trip repair (off by default)
    if rules.get('try_cp932_roundtrip', False):
        out = try_cp932_roundtrip(out)
    forbid = rules.get('forbid_tokens', [])
    has_moji, counts = detect_mojibake(out, forbid)
    if rules.get('remove_forbid', False) and (has_moji or True):
        out = remove_forbid(out, forbid)
        has_moji, counts = detect_mojibake(out, forbid)
    result = {
        'has_mojibake': has_moji,
        'token_counts': counts,
    }
    return out, result


def main(paths):
    rules = load_rules()
    for p in paths:
        fp = Path(p)
        if not fp.exists():
            print(f'[skip] not found: {fp}')
            continue
        text = fp.read_text(encoding='utf-8', errors='ignore')
        fixed, info = sanitize_and_enforce(text, rules)
        fp.write_text(fixed, encoding='utf-8')
        status = 'WARN' if info['has_mojibake'] else 'OK'
        print(f'[{status}] {fp} tokens={info["token_counts"]}')


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python tools/mojibake_guard.py <file> [file ...]')
        sys.exit(1)
    main(sys.argv[1:])
