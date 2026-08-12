#!/usr/bin/env python3
"""Harvest tool candidates from Obsidian X-Bookmarks for recommended_tools/index.html.

Scans Obsidian X-Bookmarks markdown clips, extracts tweet body + URLs +
frontmatter metadata, dedupes against existing tool cards on the
recommended_tools/index.html page, and writes a curated candidate dossier
to tmp/tool_candidates_YYYY-MM-DD.md so a human (or Claude) can review
and selectively apply.

Typical usage:
    python scripts/harvest_obsidian_tools.py                # last 30 days, default vault
    python scripts/harvest_obsidian_tools.py --days 14      # narrower window
    python scripts/harvest_obsidian_tools.py --json         # also emit JSON for programmatic use
    python scripts/harvest_obsidian_tools.py --vault PATH   # different vault
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml  # PyYAML

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VAULT = Path(r"C:\develop\obsidian\2026\00 Inbox\X-Bookmarks")
DEFAULT_TARGET_HTML = PROJECT_ROOT / "presentations" / "recommended_tools" / "index.html"
DEFAULT_OUT_DIR = PROJECT_ROOT / "tmp"

URL_RE = re.compile(r"https?://[^\s<>\"\)\]\}]+")

# Twitter often breaks long URLs across lines for display. Glue them back
# before extraction so e.g. "https://\ngithub.com/foo/bar" becomes one URL.
URL_LINEBREAK_RE = re.compile(r"(https?://)\s*\n\s*(\S+)", re.IGNORECASE)

EXCLUDE_HOSTS = {
    "x.com", "twitter.com", "t.co",
    "pbs.twimg.com", "video.twimg.com", "twimg.com",
    "lin.ee",
}

TOOL_KEYWORDS = (
    "ツール", "リリース", "ローンチ", "OSS", "オープンソース", "公式",
    "GitHub", "github.com", "stars", "★", "MIT", "Apache", "BSD",
    "プラン", "/月", "$", "無料", "プロ", "Pro", "Plus", "Enterprise",
    "Skill", "skill", "agent", "Agent", "エージェント",
    "API", "SDK", "CLI", "MCP",
    "AI",
)

# Tokens too generic to use alone as dedupe match keys. Multi-word phrases
# containing them are still allowed (e.g. "Google Finance" passes), but the
# bare token won't trigger a duplicate match against an existing card.
COMMON_NAME_TOKENS = {
    "ai", "the", "for", "of", "and", "or", "to",
    "claude", "google", "github", "open", "source",
    "tool", "tools", "plus", "pro", "enterprise",
    "code", "py", "skill", "skills", "agent", "agents",
    "deep", "research", "studio", "manager", "api", "sdk", "cli",
    "io", "dev", "app", "lab", "labs",
}


@dataclass
class Candidate:
    file: str
    date: str
    author: str
    tweet_url: str
    description: str
    body: str
    memo: str
    external_urls: list[str] = field(default_factory=list)
    matched_existing: list[str] = field(default_factory=list)
    has_tool_signals: bool = False


def parse_clip(path: Path) -> Candidate | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    fm: dict[str, Any] = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(text[3:end]) or {}
            except yaml.YAMLError:
                fm = {}
            body = text[end + 4:]

    if not isinstance(fm, dict):
        fm = {}

    sections = split_sections(body)
    body_section = sections.get("本文", "").strip()
    memo_section = sections.get("メモ", "").strip()

    description = str(fm.get("description") or "").strip()

    raw_urls: list[str] = []
    for src in (body_section, description):
        glued = URL_LINEBREAK_RE.sub(r"\1\2", src)
        for url in URL_RE.findall(glued):
            raw_urls.append(url.rstrip(".,!)】」"))

    external: list[str] = []
    seen: set[str] = set()
    for url in raw_urls:
        host = url_host(url)
        if not host or host in EXCLUDE_HOSTS:
            continue
        if url in seen:
            continue
        seen.add(url)
        external.append(url)

    text_for_signal = " ".join((body_section, memo_section, description))
    has_keyword = any(kw in text_for_signal for kw in TOOL_KEYWORDS)
    # Strict signal: a clip is considered a tool candidate only if it has
    # both a tool keyword AND at least one external URL (any non-Twitter
    # link). Pure opinion/news clips that mention "AI" but link nowhere
    # get demoted to the low-signal bucket.
    has_signals = has_keyword and bool(external)

    date_value = str(fm.get("date") or fm.get("published") or "")[:10]

    return Candidate(
        file=path.name,
        date=date_value,
        author=str(fm.get("author") or "").strip().strip('"'),
        tweet_url=str(fm.get("url") or fm.get("source") or "").strip(),
        description=description,
        body=body_section,
        memo=memo_section,
        external_urls=external,
        has_tool_signals=has_signals,
    )


def split_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"##\s+(.+)$", line.strip())
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip()
            buf = []
        else:
            if current is not None:
                buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def url_host(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else ""


def existing_tool_names(html_path: Path) -> list[str]:
    if not html_path.exists():
        return []
    text = html_path.read_text(encoding="utf-8", errors="replace")
    names = re.findall(
        r'<article class="tool-card[^"]*"[^>]*>\s*<h3>([^<]+)</h3>',
        text,
    )
    return [n.strip() for n in names if n.strip()]


def make_match_keys(name: str) -> list[str]:
    """Generate dedupe search keys from an existing tool-card name.

    Returns the full lowercased name plus shorter variants — first two
    words, and any distinctive 4+ char tokens not in COMMON_NAME_TOKENS —
    so a card "Google Finance Deep Research" can still match a tweet body
    that only says "Google Finance", and "Claude Advisor" can match a
    body that says "Advisor Tool".
    """
    n = name.strip().lower()
    if not n:
        return []
    keys: list[str] = [n]
    words = [w for w in n.split() if w]
    if len(words) >= 2:
        keys.append(" ".join(words[:2]))
    for w in words:
        if len(w) >= 4 and w not in COMMON_NAME_TOKENS:
            keys.append(w)
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def match_existing(cand: Candidate, names: list[str]) -> list[str]:
    haystack = " ".join((cand.body, cand.description, cand.memo)).lower()
    matched: list[str] = []
    for name in names:
        for key in make_match_keys(name):
            if len(key) < 3:
                continue
            if " " in key:
                if key in haystack:
                    matched.append(name)
                    break
            else:
                pattern = r"(?<![a-z0-9_\-])" + re.escape(key) + r"(?![a-z0-9_\-])"
                if re.search(pattern, haystack):
                    matched.append(name)
                    break
    return matched


def render_candidate(idx: int, c: Candidate) -> list[str]:
    lines: list[str] = [
        f"### #{idx} `{c.file}`",
        "",
        f"- **Date**: {c.date or '(unknown)'}  |  **Author**: {c.author or '(unknown)'}",
    ]
    if c.tweet_url:
        lines.append(f"- **Tweet**: {c.tweet_url}")
    if c.external_urls:
        lines.append("- **External URLs**:")
        for url in c.external_urls[:8]:
            lines.append(f"  - {url}")
    if c.memo:
        memo_short = c.memo.replace("\n", " ")
        lines.append(f"- **Memo (user)**: {memo_short[:240]}")
    body_excerpt = c.body if c.body else c.description
    if body_excerpt:
        lines.append("- **Body**:")
        for ln in body_excerpt.splitlines()[:18]:
            ln = ln.rstrip()
            if not ln:
                continue
            lines.append(f"  > {ln}")
        if len(body_excerpt.splitlines()) > 18:
            lines.append("  > …(truncated)")
    return lines


def render_markdown(candidates: list[Candidate], existing_names: list[str], cutoff: str | None) -> str:
    today = dt.date.today().isoformat()
    new_picks = [c for c in candidates if c.has_tool_signals and not c.matched_existing]
    dupes = [c for c in candidates if c.matched_existing]
    weak = [c for c in candidates if not c.has_tool_signals and not c.matched_existing]

    lines: list[str] = []
    lines.append(f"# Tool Candidates {today}")
    lines.append("")
    range_desc = f"clips dated since {cutoff}" if cutoff else "all clips"
    lines.append(f"_Source: Obsidian X-Bookmarks ({range_desc})._")
    lines.append("")
    lines.append(f"- Existing tool cards on recommended_tools/index.html: **{len(existing_names)}**")
    lines.append(f"- 🆕 New candidates with tool signals: **{len(new_picks)}**")
    lines.append(f"- ♻️ Already on the page (duplicates): {len(dupes)}")
    lines.append(f"- 🤔 Low-signal (no tool keywords): {len(weak)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🆕 New candidates")
    lines.append("")
    if not new_picks:
        lines.append("(No new tool-shaped clips in this window.)")
        lines.append("")
    for i, c in enumerate(new_picks, 1):
        lines.extend(render_candidate(i, c))
        lines.append("")

    if dupes:
        lines.append("## ♻️ Duplicates (already on the page)")
        lines.append("")
        for c in dupes[:30]:
            matches = ", ".join(c.matched_existing[:5])
            lines.append(f"- `{c.file}` — matches: {matches}")
        lines.append("")

    if weak:
        lines.append("## 🤔 Low-signal clips (review only if interested)")
        lines.append("")
        for c in weak[:40]:
            preview = (c.description or c.body or "").replace("\n", " ").strip()
            lines.append(f"- `{c.file}` — {preview[:100]}")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT, help="X-Bookmarks directory")
    ap.add_argument("--target-html", type=Path, default=DEFAULT_TARGET_HTML, help="recommended_tools/index.html for dedupe")
    ap.add_argument("--days", type=int, default=30, help="Only include clips dated within last N days (0 = all)")
    ap.add_argument("--out", type=Path, default=None, help="Output markdown path (default: tmp/tool_candidates_YYYY-MM-DD.md)")
    ap.add_argument("--json", action="store_true", help="Also dump JSON next to the markdown")
    args = ap.parse_args(argv)

    if not args.vault.exists():
        print(f"Vault not found: {args.vault}", file=sys.stderr)
        return 2

    cutoff: str | None = None
    if args.days > 0:
        cutoff = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()

    candidates: list[Candidate] = []
    for path in sorted(args.vault.glob("*.md")):
        cand = parse_clip(path)
        if cand is None:
            continue
        if cutoff and cand.date and cand.date < cutoff:
            continue
        candidates.append(cand)

    existing = existing_tool_names(args.target_html)
    for c in candidates:
        c.matched_existing = match_existing(c, existing)

    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(exist_ok=True)
    out_path = args.out or (out_dir / f"tool_candidates_{dt.date.today().isoformat()}.md")
    out_path.write_text(render_markdown(candidates, existing, cutoff), encoding="utf-8")

    new_count = sum(1 for c in candidates if c.has_tool_signals and not c.matched_existing)
    dupe_count = sum(1 for c in candidates if c.matched_existing)
    print(f"Wrote {out_path}")
    print(f"  scanned: {len(candidates)}  |  new: {new_count}  |  dupes: {dupe_count}")

    if args.json:
        json_path = out_path.with_suffix(".json")
        payload = [asdict(c) for c in candidates]
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
