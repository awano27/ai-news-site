#!/usr/bin/env python3
"""Report analytics coverage for public HTML files."""
from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def excluded(path,text):
    return bool(re.search(r"_bak|\.bak|^test_",path.name,re.I) or re.search(r'<meta\s+[^>]*http-equiv=["\']refresh["\']',text,re.I))
def main():
    files=list(ROOT.glob("*.html"))+list((ROOT/"presentations").rglob("*.html"))
    targets=[]
    for p in files:
        if "_review_output" in p.parts:
            continue
        text=p.read_text(encoding="utf-8")
        if not excluded(p,text): targets.append((p,text))
    missing=[p for p,text in targets if '/assets/js/analytics.js' not in text]
    print(f"[analytics_coverage] total={len(targets)} injected={len(targets)-len(missing)} missing={len(missing)} coverage={(len(targets)-len(missing))*100/len(targets):.1f}%")
    for p in missing: print(p.relative_to(ROOT))
    return bool(missing)
if __name__ == '__main__': raise SystemExit(main())
