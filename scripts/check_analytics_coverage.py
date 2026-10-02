#!/usr/bin/env python3
"""Report analytics coverage for public HTML files."""
from __future__ import annotations
import re
from pathlib import Path
try:
    from .public_html import public_html_files, exclusion_reason, analytics_present
except ImportError:
    from public_html import public_html_files, exclusion_reason, analytics_present
ROOT=Path(__file__).resolve().parents[1]
def excluded(path,text):
    return exclusion_reason(path, text) is not None
def main():
    files=public_html_files(ROOT)
    targets=[]
    for p in files:
        if "_review_output" in p.parts:
            continue
        text=p.read_text(encoding="utf-8")
        if not excluded(p,text): targets.append((p,text))
    missing=[p for p,text in targets if not analytics_present(text)]
    print(f"[analytics_coverage] total={len(targets)} injected={len(targets)-len(missing)} missing={len(missing)} coverage={(len(targets)-len(missing))*100/max(len(targets),1):.1f}%")
    for p in missing: print(p.relative_to(ROOT))
    return bool(missing)
if __name__ == '__main__': raise SystemExit(main())
