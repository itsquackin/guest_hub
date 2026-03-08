"""Deterministic hashing utilities for row identification."""
from __future__ import annotations

import hashlib
import json


def hash_dict(data: dict) -> str:
    """Generate a stable 16-char SHA-256 hex digest from a dictionary.

    Keys are sorted for stability.  Values are coerced to strings so that
    ``None`` and non-serialisable types don't break the hash.

    Used to produce deterministic ``source_row_id`` values.
    """
    serialized = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def hash_string(text: str) -> str:
    """Return a 16-char SHA-256 hex digest of *text*."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def hash_fields(*values: object) -> str:
    """Hash an ordered sequence of field values to a 16-char hex string.

    Useful for compound keys (e.g. confirmation_number + guest_sequence).
    """
    joined = "|".join("" if v is None else str(v) for v in values)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]
