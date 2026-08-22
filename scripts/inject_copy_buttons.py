#!/usr/bin/env python3
"""Inject idempotent one-tap copy buttons into day slides that show commands."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "presentations" / "day_slides"
START, END = "<!-- copy-btn:start -->", "<!-- copy-btn:end -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
TARGET_RE = re.compile(r"<code\b|class=['\"]cmd['\"]", re.I)
InjectionStatus = Literal["injected", "unchanged", "no-target"]

PREFIX_RE = re.compile(r"^(npx|npm|pip|uv|git|curl|docker|python|node|claude|brew)(\s|$)", re.I)
DOMAIN_RE = re.compile(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/|$)")


def is_cmd(text: str) -> bool:
    """Prefix match, or 8+ char one-liner. URLs, domains, and non-ASCII labels are out."""
    t = " ".join((text or "").split()).strip()
    if not t:
        return False
    if PREFIX_RE.match(t):
        return True
    if len(t) < 8:
        return False
    if t.lower().startswith("http://") or t.lower().startswith("https://"):
        return False
    if any(ord(ch) > 127 for ch in t):
        return False
    if DOMAIN_RE.match(t):
        return False
    return True


COPY_SCRIPT = r"""(function(){
  if (!navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') return;
  var PREFIX = /^(npx|npm|pip|uv|git|curl|docker|python|node|claude|brew)(\s|$)/i;
  function isCmd(text){
    var t = String(text || '').replace(/\s+/g, ' ').trim();
    if (!t) return false;
    if (PREFIX.test(t)) return true;
    if (t.length < 8) return false;
    if (/^https?:\/\//i.test(t)) return false;
    if (/[^\x00-\x7F]/.test(t)) return false;
    if (/^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(\/|$)/.test(t)) return false;
    return true;
  }
  var style = document.createElement('style');
  style.textContent = '.copy-btn-wrap{display:inline-flex;align-items:center;gap:6px;max-width:100%;flex-wrap:wrap;vertical-align:middle;}'
    + '.copy-btn{flex:0 0 auto;margin:0;padding:2px 8px;font:600 11px/1.2 sans-serif;letter-spacing:.02em;color:#111;background:rgba(255,255,255,.74);border:1px solid rgba(0,0,0,.16);border-radius:999px;cursor:pointer;opacity:.7;}'
    + '.copy-btn:hover,.copy-btn[data-ok="1"]{opacity:1;}';
  document.head.appendChild(style);
  var nodes = document.querySelectorAll('code, .cmd');
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    if (el.closest('.copy-btn-wrap')) continue;
    var text = String(el.textContent || '').replace(/\s+/g, ' ').trim();
    if (!isCmd(text) || !el.parentNode) continue;
    var wrap = document.createElement('span');
    wrap.className = 'copy-btn-wrap';
    el.parentNode.insertBefore(wrap, el);
    wrap.appendChild(el);
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'copy-btn';
    btn.textContent = 'コピー';
    btn.setAttribute('aria-label', 'コマンドをコピー');
    btn.addEventListener('click', function (ev) {
      ev.preventDefault();
      var b = ev.currentTarget;
      var src = b.previousElementSibling;
      var val = src ? String(src.textContent || '').replace(/\s+/g, ' ').trim() : '';
      navigator.clipboard.writeText(val).then(function () {
        var prev = b.textContent;
        b.textContent = '\u2713';
        b.setAttribute('data-ok', '1');
        setTimeout(function () { b.textContent = prev; b.removeAttribute('data-ok'); }, 1500);
      }).catch(function () {});
    });
    wrap.appendChild(btn);
  }
})();"""


def build_block() -> str:
    return f"{START}\n<script>\n{COPY_SCRIPT}\n</script>\n{END}"


def has_target(html: str) -> bool:
    return bool(TARGET_RE.search(html))


def inject(path: Path) -> InjectionStatus:
    text = path.read_text(encoding="utf-8")
    if not has_target(text) or not re.search(r"</body>", text, flags=re.I):
        return "no-target"
    block = build_block()
    if START in text:
        updated = BLOCK_RE.sub(lambda _m: block, text, count=1)
    else:
        updated = re.sub(r"</body>", lambda _m: block + "\n</body>", text, count=1, flags=re.I)
    if updated == text:
        return "unchanged"
    path.write_text(updated, encoding="utf-8", newline="\n")
    return "injected"


def main() -> int:
    slides = sorted(SLIDES.glob("day_slide_????_??_??.html"))
    counts = {"injected": 0, "unchanged": 0, "no-target": 0}
    for path in slides:
        status = inject(path)
        counts[status] += 1
    print(
        f"[inject_copy_buttons] {len(slides)} files, "
        f"{counts['injected']} injected, {counts['unchanged']} unchanged, "
        f"{counts['no-target']} no-target"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
