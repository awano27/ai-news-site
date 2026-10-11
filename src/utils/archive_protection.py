"""Fail closed before legacy tools can replace source-reviewed archive copy.

Review metadata belongs to its exact text. Legacy generators and normalizers
cannot validate that relationship, so they must leave these snapshots intact.
This guard never copies review flags onto replacement content.
"""
from __future__ import annotations

import json
from pathlib import Path


class ArchiveProtectionError(ValueError):
    """An existing snapshot cannot safely be changed by a legacy writer."""


class ProtectedArchiveError(ArchiveProtectionError):
    """A readable snapshot has provenance that a legacy writer must preserve."""


def _unique_keys(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError(f'duplicate JSON key: {key}')
        data[key] = value
    return data


def _invalid_constant(value):
    raise ValueError(f'non-JSON numeric constant: {value}')


def load_strict_json(raw):
    """Parse JSON without duplicate-key ambiguity or non-JSON numeric values."""
    return json.loads(raw, object_pairs_hook=_unique_keys,
                      parse_constant=_invalid_constant)


def has_review_provenance(value):
    """Recognize review markers consistently in writers and bundle validators."""
    if isinstance(value, dict):
        for key, child in value.items():
            # Empty evidence objects are still evidence-bearing, not permission
            # to erase provenance. Null is used by ordinary unreviewed articles.
            if key in {'editorial_review', 'reviewed_summary', 'claim_evidence',
                       'provenance', 'reviewed_at', 'review_method'} and child is not None:
                return True
            if key in {'publication_mode', 'mode'} and child == 'editorial_review':
                return True
            if key in {'processing_status', 'status'} and child == 'editorial_reviewed':
                return True
            if has_review_provenance(child):
                return True
    elif isinstance(value, list):
        return any(has_review_provenance(child) for child in value)
    return False


def guard_legacy_archive_write(path: Path) -> dict | None:
    """Return an unreviewed payload, or refuse an unreadable/protected target.

    Call for every target before the first write in a batch, irrespective of
    timestamps. An absent target is safe for legacy generation.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding='utf-8')
    except FileNotFoundError as error:
        if not path.is_symlink():
            return None
        raise ArchiveProtectionError(f'unreadable archive snapshot: {path}') from error
    except (OSError, UnicodeError) as error:
        raise ArchiveProtectionError(f'unreadable archive snapshot: {path}: {error}') from error
    try:
        data = load_strict_json(raw)
        if not isinstance(data, dict):
            raise ValueError('expected an object')
        for key in ('items', 'articles'):
            if key in data and (not isinstance(data[key], list)
                               or not all(isinstance(item, dict) for item in data[key])):
                raise ValueError(f'{key} must be a list of objects')
        protected = has_review_provenance(data)
    except (ValueError, RecursionError) as error:
        raise ArchiveProtectionError(f'invalid archive snapshot: {path}: {error}') from error
    if protected:
        raise ProtectedArchiveError(f'protected reviewed archive snapshot: {path}')
    return data
