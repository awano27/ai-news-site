#!/usr/bin/env python3
"""Copy the public visionhub.jp tree into a GitHub Pages staging directory.

The Pages artifact used to be the repository root. Deleting a denylist in
place kept leaking new internal directories (tasks/, .claude/, ops/, config/,
docs/, and the rest). This script copies an allowlist instead. Daily output
lands in directories that are already on the allowlist, so a new slide, daily
news page, or report is published without editing this file.

Run:
    python scripts/stage_pages_site.py --dest "$RUNNER_TEMP/pages-site"
    python scripts/stage_pages_site.py --check-only
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


HOSTS = {"visionhub.jp", "www.visionhub.jp"}
SITEMAP_NAME = "sitemap.xml"

# Directories copied in full. New daily files appear inside these trees.
PUBLISH_DIRECTORIES = (
    "ai-news-site",
    "articles",
    "assets",
    "daily-news",
    "daily-news-csv",
    "examples/claim-evidence",
    "news",
    "presentations",
    "public-pages",
)

# Repo-root files the live site serves. IndexNow key files are separate.
PUBLISH_ROOT_FILES = frozenset({
    ".nojekyll",
    "404.html",
    "CNAME",
    "about.html",
    "ads.txt",
    "contact.html",
    "credits.html",
    "daily_slides_index.html",
    "feed.xml",
    "index.html",
    "llms.txt",
    "news.js",
    "privacy-policy.html",
    "robots.txt",
    "sitemap.xml",
    "style.css",
})

# One reader-facing download linked from the 2026-05-14 slide.
# Every other path under input/ stays unpublished.
PUBLISH_EXACT_FILES = frozenset({
    "input/day/0514.pdf",
})

# Top-level trees that must never appear in the artifact, even if a later
# edit adds them under a publish directory by mistake.
DENIED_PREFIXES = (
    ".claude/",
    ".git/",
    ".github/",
    "config/",
    "docs/",
    "input/",
    "ops/",
    "outputs/",
    "script/",
    "scripts/",
    "src/",
    "tasks/",
    "templates/",
    "tests/",
    "tools/",
)

# Root files that are repository metadata, not site pages. A published HTML
# file that links at one of these still must not put it on the CDN.
DENIED_ROOT_FILES = frozenset({
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".vercelignore",
    "ADSENSE_CHANGES.md",
    "CLAUDE.md",
    "PLAN.md",
    "README.md",
    "_config.yml",
    "requirements-daily.txt",
    "requirements.txt",
    "setup.py",
    "update_news_archive.py",
})

REQUIRED_PUBLISHED_PATHS = (
    ".nojekyll",
    "404.html",
    "CNAME",
    "about.html",
    "ads.txt",
    "assets/js/analytics.js",
    "assets/og/default.png",
    "contact.html",
    "credits.html",
    "daily-news/data.json",
    "daily-news/index.html",
    "feed.xml",
    "index.html",
    "input/day/0514.pdf",
    "llms.txt",
    "privacy-policy.html",
    "robots.txt",
    "sitemap.xml",
)

INDEXNOW_KEY_FILE = re.compile(r"^[0-9a-fA-F]{32,64}\.txt$")
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
ATTR_REF_RE = re.compile(
    r"""(?:href|src|poster|data-src)\s*=\s*['"]([^'"]+)['"]""",
    re.IGNORECASE,
)
URL_REF_RE = re.compile(r"""url\(\s*['"]?([^'")\s]+)['"]?\s*\)""", re.IGNORECASE)
FETCH_REF_RE = re.compile(r"""(?:fetch|import)\(\s*['"]([^'"]+)['"]""")

SKIP_DIR_NAMES = frozenset({"__pycache__", ".git", ".github", "node_modules", ".venv", "venv"})
BLOCKED_FILE_NAMES = frozenset({
    ".DS_Store",
    ".env",
    ".env.local",
    "Thumbs.db",
    "credentials.json",
    "secrets.json",
})
BLOCKED_SUFFIXES = frozenset({".pyc", ".pyo", ".pem", ".key", ".p12", ".pfx"})
SCAN_SUFFIXES = frozenset({".html", ".js", ".css"})


class PublishSafetyError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def normalize_rel(rel: str) -> str:
    """Return a posix relative path, or raise ValueError if it escapes the root."""
    text = rel.replace("\\", "/")
    if text.startswith("file:"):
        raise ValueError(rel)
    parts: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise ValueError(rel)
            parts.pop()
            continue
        parts.append(part)
    if not parts:
        raise ValueError(rel)
    return "/".join(parts)


def _blocked_file(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    if name in BLOCKED_FILE_NAMES:
        return True
    suffix = Path(name).suffix.lower()
    return suffix in BLOCKED_SUFFIXES


def _has_skipped_dir(rel: str) -> bool:
    return any(part in SKIP_DIR_NAMES for part in rel.split("/"))


def is_denied(rel: str) -> bool:
    if rel in PUBLISH_EXACT_FILES:
        return False
    if rel in DENIED_ROOT_FILES:
        return True
    return any(rel == prefix.rstrip("/") or rel.startswith(prefix) for prefix in DENIED_PREFIXES)


def should_publish(rel: str) -> bool:
    """True when a repo-relative path belongs in the Pages artifact."""
    try:
        rel = normalize_rel(rel)
    except ValueError:
        return False
    if _has_skipped_dir(rel) or _blocked_file(rel):
        return False
    if rel in PUBLISH_EXACT_FILES:
        return True
    if is_denied(rel):
        return False
    if rel in PUBLISH_ROOT_FILES:
        return True
    if "/" not in rel and INDEXNOW_KEY_FILE.fullmatch(rel):
        return True
    return any(rel.startswith(directory.rstrip("/") + "/") for directory in PUBLISH_DIRECTORIES)


def sitemap_locs(text: str) -> list[str]:
    return LOC_RE.findall(text)


def loc_to_relative(loc: str) -> str:
    parsed = urlparse(loc.strip())
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in HOSTS:
        raise ValueError(f"unexpected sitemap location: {loc}")
    path = unquote(parsed.path)
    if path in ("", "/"):
        return "index.html"
    if path.endswith("/"):
        path += "index.html"
    return normalize_rel(path)


def iter_publish_files(root: Path):
    """Yield files that should be copied. Rejects symlinks instead of following them."""
    root = root.resolve()
    seen: set[str] = set()
    for directory in PUBLISH_DIRECTORIES:
        base = root.joinpath(*directory.split("/"))
        if not base.exists():
            continue
        if base.is_symlink():
            raise PublishSafetyError([f"refusing to publish symlink: {directory}"])
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            current = Path(dirpath)
            if current.is_symlink():
                raise PublishSafetyError([f"refusing to publish symlink: {current}"])
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
            for name in list(dirnames):
                if (current / name).is_symlink():
                    raise PublishSafetyError([f"refusing to publish symlink: {directory}/{name}"])
            for name in filenames:
                path = current / name
                if path.is_symlink():
                    raise PublishSafetyError([
                        f"refusing to publish symlink: {path.relative_to(root).as_posix()}"
                    ])
                rel = path.relative_to(root).as_posix()
                if should_publish(rel) and rel not in seen:
                    seen.add(rel)
                    yield path

    for name in sorted(PUBLISH_ROOT_FILES):
        path = root / name
        if path.is_symlink():
            raise PublishSafetyError([f"refusing to publish symlink: {name}"])
        rel = name
        if path.is_file() and should_publish(rel) and rel not in seen:
            seen.add(rel)
            yield path

    for path in sorted(root.iterdir()):
        if not path.is_file() or path.is_symlink():
            if path.is_symlink() and INDEXNOW_KEY_FILE.fullmatch(path.name):
                raise PublishSafetyError([f"refusing to publish symlink: {path.name}"])
            continue
        if INDEXNOW_KEY_FILE.fullmatch(path.name) and path.name not in seen and should_publish(path.name):
            seen.add(path.name)
            yield path

    for rel in sorted(PUBLISH_EXACT_FILES):
        path = root.joinpath(*rel.split("/"))
        if path.is_symlink():
            raise PublishSafetyError([f"refusing to publish symlink: {rel}"])
        if path.is_file() and rel not in seen and should_publish(rel):
            seen.add(rel)
            yield path


def publication_paths(root: Path) -> list[str]:
    root = root.resolve()
    return [path.relative_to(root).as_posix() for path in iter_publish_files(root)]


def _resolve_ref(source_file: str, ref: str) -> str | None:
    if ref.startswith(("mailto:", "data:", "javascript:", "tel:", "#", "//")):
        return None
    if ref.startswith(("http://", "https://")):
        parsed = urlparse(ref)
        if parsed.netloc not in HOSTS:
            return None
        path = unquote(parsed.path)
    else:
        path = unquote(ref.split("#", 1)[0].split("?", 1)[0])
        if not path.startswith("/"):
            parent = source_file.rsplit("/", 1)[0] if "/" in source_file else ""
            path = f"{parent}/{path}" if parent else path
    path = path.split("#", 1)[0].split("?", 1)[0]
    if not path or path == "/":
        return None
    try:
        return normalize_rel(path)
    except ValueError:
        return None


def missing_published_references(scan_root: Path, lookup_root: Path, published: set[str]) -> list[str]:
    """Return repo files a published page links to that the allowlist dropped.

    Links into denied trees are omitted on purpose (config/analytics.json is the
    known one). lookup_root is the full repository, so a file left out of the
    staging directory is still visible.
    """
    missing: list[str] = []
    seen: set[str] = set()
    for rel in sorted(published):
        if Path(rel).suffix.lower() not in SCAN_SUFFIXES:
            continue
        path = scan_root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        refs = ATTR_REF_RE.findall(text) + URL_REF_RE.findall(text) + FETCH_REF_RE.findall(text)
        for ref in refs:
            target = _resolve_ref(rel, ref)
            if not target or target in published or is_denied(target):
                continue
            if (lookup_root / target).is_file():
                item = f"{rel} -> {target}"
                if item not in seen:
                    seen.add(item)
                    missing.append(item)
    return missing


def validate_publication(
    site: Path,
    published: set[str] | None = None,
    source: Path | None = None,
) -> list[str]:
    """Check sitemap coverage, required URLs, and the absence of internal trees."""
    site = site.resolve()
    source = (source or site).resolve()
    errors: list[str] = []
    if published is None:
        published = set(publication_paths(source if source != site else site))

    leaked = sorted(rel for rel in published if not should_publish(rel) or is_denied(rel))
    errors.extend(f"internal path would be published: {rel}" for rel in leaked)

    sitemap_path = site / SITEMAP_NAME
    if not sitemap_path.is_file():
        errors.append("sitemap.xml is missing from the publication")
        return errors
    locs = sitemap_locs(sitemap_path.read_text(encoding="utf-8"))
    if not locs:
        errors.append("sitemap.xml has no URLs")
    for loc in locs:
        try:
            rel = loc_to_relative(loc)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if rel not in published or not (site / rel).is_file():
            errors.append(f"sitemap URL missing from publication: {loc} ({rel})")

    for rel in REQUIRED_PUBLISHED_PATHS:
        if rel not in published or not (site / rel).is_file():
            errors.append(f"required public file missing: {rel}")

    errors.extend(
        f"published page links to an unpublished repo file: {item}"
        for item in missing_published_references(site, source, published)
    )
    return errors


def stage_site(root: Path, dest: Path) -> list[str]:
    """Copy the allowlist to dest, replacing any previous staging directory."""
    root = root.resolve()
    dest = dest.resolve()
    if dest == root or root in dest.parents or dest in root.parents:
        raise PublishSafetyError([f"staging directory must be outside the repository and must not contain it: {dest}"])
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    copied: list[str] = []
    for source in iter_publish_files(root):
        rel = source.relative_to(root).as_posix()
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(rel)
    published = set(copied)
    errors = validate_publication(dest, published, source=root)
    if errors:
        raise PublishSafetyError(errors)
    return copied


def _print_errors(errors: list[str]) -> None:
    print(f"pages publication check failed ({len(errors)})", file=sys.stderr)
    for error in errors[:50]:
        print(error, file=sys.stderr)
    if len(errors) > 50:
        print(f"... {len(errors) - 50} more", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dest", type=Path, help="Directory that becomes the Pages artifact root")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate the source tree without copying",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"repository root does not exist: {root}", file=sys.stderr)
        return 1
    try:
        if args.dest is None:
            errors = validate_publication(root)
            if errors:
                _print_errors(errors)
                return 1
            selected = publication_paths(root)
            print(f"pages publication check passed: {len(selected)} files, sitemap included")
            return 0
        if args.check_only:
            print("--check-only does not use --dest", file=sys.stderr)
            return 1
        copied = stage_site(root, args.dest)
    except PublishSafetyError as exc:
        _print_errors(exc.errors)
        return 1
    print(f"staged {len(copied)} public files -> {args.dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
