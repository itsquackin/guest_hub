"""Phone number normalization and classification utilities."""
from __future__ import annotations

import re

_DIGITS_ONLY = re.compile(r"\D")

# Minimum digit count to be considered a plausible phone number
_MIN_DIGITS = 7
_MAX_DIGITS_DOMESTIC = 11


def normalize_phone(raw: str | None) -> str | None:
    """Strip all non-digit characters from a phone string.

    Returns ``None`` when the input is blank or produces no digits.
    """
    if not raw:
        return None
    digits = _DIGITS_ONLY.sub("", str(raw))
    return digits if digits else None


def build_match_phone_key(raw: str | None) -> str | None:
    """Return the last 10 digits of the normalized phone as the matching key.

    Uses the last 10 digits so that country codes and leading 1s are ignored
    during matching.  Returns ``None`` when fewer than 7 digits are present.
    """
    digits = normalize_phone(raw)
    if not digits or len(digits) < _MIN_DIGITS:
        return None
    return digits[-10:] if len(digits) >= 10 else digits


def is_blank_phone(raw: str | None) -> bool:
    """Return True when the phone field is None, empty, or produces no digits."""
    return not normalize_phone(raw)


def is_incomplete_like(phone_clean: str | None) -> bool:
    """Return True if the cleaned phone has fewer than 7 digits (likely truncated)."""
    if not phone_clean:
        return True
    return len(phone_clean) < _MIN_DIGITS


def is_international_like(phone_clean: str | None, raw: str | None = None) -> bool:
    """Return True if the phone appears international.

    Triggers on:
    - Raw value starting with ``+``
    - More than 11 digits (exceeds North American maximum)
    """
    if raw and str(raw).strip().startswith("+"):
        return True
    if phone_clean and len(phone_clean) > _MAX_DIGITS_DOMESTIC:
        return True
    return False


def is_valid_like(phone_clean: str | None) -> bool:
    """Return True if the phone looks like a plausible domestic number (7–11 digits)."""
    if not phone_clean:
        return False
    return _MIN_DIGITS <= len(phone_clean) <= _MAX_DIGITS_DOMESTIC


def classify_phone(
    phone_clean: str | None,
    raw: str | None = None,
    *,
    is_inherited: bool = False,
    is_shared: bool = False,
) -> list[str]:
    """Return a list of flag strings describing the phone's status.

    Possible flags: ``"blank"``, ``"inherited"``, ``"shared"``,
    ``"incomplete"``, ``"international_like"``, ``"valid"``.
    """
    flags: list[str] = []
    if is_blank_phone(raw):
        flags.append("blank")
        return flags
    if is_inherited:
        flags.append("inherited")
    if is_shared:
        flags.append("shared")
    if is_incomplete_like(phone_clean):
        flags.append("incomplete")
    elif is_international_like(phone_clean, raw):
        flags.append("international_like")
    else:
        flags.append("valid")
    return flags
