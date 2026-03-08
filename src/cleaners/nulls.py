"""Null and empty-value normalization utilities."""
from __future__ import annotations

import re

_BLANK_PATTERN = re.compile(
    r"^\s*(?:n/?a|none|null|undefined|unknown|-+|\.+|x+)?\s*$",
    re.IGNORECASE,
)


def is_blank(value: object) -> bool:
    """Return True if value is None, empty, or a common null-sentinel string.

    Treats None, empty string, whitespace-only, and common placeholders
    such as 'N/A', 'None', 'null', 'unknown', '---' as blank.
    """
    if value is None:
        return True
    return bool(_BLANK_PATTERN.match(str(value)))


def normalize_null(
    value: str | None,
    *,
    replacement: str | None = None,
) -> str | None:
    """Strip value and return None (or replacement) when blank.

    Returns the stripped string when the value contains real content;
    otherwise returns *replacement* (default ``None``).
    """
    if value is None:
        return replacement
    stripped = str(value).strip()
    if _BLANK_PATTERN.match(stripped):
        return replacement
    return stripped


def coerce_str(value: object) -> str | None:
    """Convert value to a stripped string; return None if blank."""
    if value is None:
        return None
    return normalize_null(str(value))
