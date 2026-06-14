"""
src/utils/encoding.py — Shared UTF-8 file I/O helpers.

Consolidates the ~55 scattered ``open(..., encoding='utf-8')`` call-sites across
src/, scripts/, script/, and root *.py into a single, consistent API.

Usage
-----
    from src.utils.encoding import read_text, write_text, read_json, write_json

All functions default to UTF-8 without BOM.  Pass ``errors='ignore'`` or
``errors='replace'`` for lenient decoding of third-party content (matches the
pattern seen in src/auto_collect/html_report.py:476).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Text I/O
# ---------------------------------------------------------------------------

def read_text(path: str | Path, errors: str = "strict") -> str:
    """Read *path* as UTF-8 text.

    Args:
        path:   File to read.
        errors: Python codec error handler ('strict', 'ignore', 'replace').
                Use 'ignore' for untrusted / scraped HTML (mirrors
                html_report.py read_text(encoding='utf-8', errors='ignore')).

    Returns:
        File contents as str.

    Raises:
        FileNotFoundError: if *path* does not exist.
        UnicodeDecodeError: if *errors* == 'strict' and the file is not valid UTF-8.
    """
    return Path(path).read_text(encoding="utf-8", errors=errors)


def write_text(path: str | Path, content: str, *, mkdir: bool = True) -> Path:
    """Write *content* to *path* as UTF-8 (no BOM).

    Args:
        path:    Destination file.
        content: Text to write.
        mkdir:   If True (default), create parent directories automatically.

    Returns:
        Resolved Path of the written file.
    """
    p = Path(path)
    if mkdir:
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------

def read_json(path: str | Path) -> Any:
    """Load JSON from *path* (UTF-8).

    Returns:
        Parsed Python object (dict, list, …).

    Raises:
        FileNotFoundError, json.JSONDecodeError.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(
    path: str | Path,
    data: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    mkdir: bool = True,
) -> Path:
    """Serialise *data* to JSON and write to *path* (UTF-8, no BOM).

    Args:
        path:         Destination file.
        data:         JSON-serialisable object.
        indent:       Pretty-print indent (default 2, mirrors existing call-sites).
        ensure_ascii: False preserves Japanese characters without escaping.
        mkdir:        If True, create parent directories automatically.

    Returns:
        Resolved Path of the written file.
    """
    p = Path(path)
    if mkdir:
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(data, ensure_ascii=ensure_ascii, indent=indent),
        encoding="utf-8",
    )
    return p


# ---------------------------------------------------------------------------
# Convenience: open() wrapper for streaming / large files
# ---------------------------------------------------------------------------

def open_utf8(path: str | Path, mode: str = "r", errors: str = "strict"):
    """Return an open file handle for *path* with UTF-8 encoding.

    Thin wrapper so callers can do::

        with open_utf8(p) as f:
            for line in f:
                ...

    This replaces the pattern ``open(path, 'r', encoding='utf-8')`` seen in
    all generator files.
    """
    return open(Path(path), mode, encoding="utf-8", errors=errors)
