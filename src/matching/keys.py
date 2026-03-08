"""Match key builders for cross-source guest linking.

All match keys produced here are stable, normalized strings that can be
compared with == (exact) or a similarity function (fuzzy).
"""
from __future__ import annotations

from datetime import date

from src.cleaners.names import build_match_name_key
from src.cleaners.phones import build_match_phone_key
from src.utils.constants import NAME_KEY_SEP


def make_name_key(first: str | None, last: str | None) -> str | None:
    """Return the canonical ``first|last`` match key."""
    return build_match_name_key(first, last)


def make_phone_key(raw: str | None) -> str | None:
    """Return the last-10-digits match key for a phone number."""
    return build_match_phone_key(raw)


def make_stay_window_key(
    confirmation_number: str,
    arrival: date | None,
    departure: date | None,
) -> str | None:
    """Return a compound stay-window key for fast lookups."""
    if not arrival or not departure:
        return None
    return f"{confirmation_number}@{arrival.isoformat()}/{departure.isoformat()}"


def make_activity_source_key(source_system: str, source_row_id: str) -> str:
    """Return a globally unique activity key across source systems."""
    return f"{source_system}:{source_row_id}"


def name_key_last_part(key: str | None) -> str | None:
    """Extract the last-name token from a ``first|last`` key."""
    if not key or NAME_KEY_SEP not in key:
        return key
    return key.split(NAME_KEY_SEP, 1)[1] or None


def name_key_first_part(key: str | None) -> str | None:
    """Extract the first-name token from a ``first|last`` key."""
    if not key or NAME_KEY_SEP not in key:
        return None
    return key.split(NAME_KEY_SEP, 1)[0] or None
