"""Rate code, room-type code, and specials-string normalization utilities."""
from __future__ import annotations

import re

_SPECIALS_SPLIT = re.compile(r"[,;/|+]")


def normalize_code(code: str | None) -> str | None:
    """Uppercase and strip a code string; return None if blank."""
    if not code or not code.strip():
        return None
    return code.strip().upper()


def split_specials_string(raw: str | None) -> list[str]:
    """Split a specials/codes field on common delimiters.

    Returns a list of non-empty, uppercased, stripped code tokens.
    Handles comma, semicolon, slash, pipe, and plus as delimiters.
    """
    if not raw or not raw.strip():
        return []
    parts = _SPECIALS_SPLIT.split(raw)
    return [p.strip().upper() for p in parts if p.strip()]


def parse_nightly_rate(raw: str | None) -> float | None:
    """Parse a nightly rate string to a float; strip currency symbols and commas."""
    if not raw or not raw.strip():
        return None
    cleaned = re.sub(r"[^\d.]", "", raw.strip())
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_nights(raw: str | None) -> int | None:
    """Parse a nights-count string to an int."""
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip()
    try:
        return int(float(cleaned))
    except (ValueError, OverflowError):
        return None
