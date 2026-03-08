"""Guest name cleaning, normalization, and match-key generation.

The canonical match key format is ``normalized_first|normalized_last``
(pipe-separated lowercase, accents stripped, punctuation removed).
"""
from __future__ import annotations

import re

from src.cleaners.nulls import is_blank
from src.cleaners.text import collapse_spaces, strip_accents

# ── Constants ────────────────────────────────────────────────────────────────

NAME_KEY_SEP = "|"

_SALUTATION = re.compile(
    r"^(?:mr|mrs|ms|miss|dr|prof|rev|sir|lord|lady)\.?\s+",
    re.IGNORECASE,
)
_SUFFIX = re.compile(
    r"\b(?:jr|sr|ii|iii|iv|v|vi|esq|phd|md|dds|dvm|rn|pe)\.?$",
    re.IGNORECASE,
)
_NON_ALPHA = re.compile(r"[^a-z\s'\-]")

# Delimiters used to separate accompanying guests in a single field
_ACCOMPANYING_SPLIT = re.compile(
    r"\s*(?:,|;|/|&|\\+|\band\b)\s*",
    re.IGNORECASE,
)


# ── Core normalization ────────────────────────────────────────────────────────

def normalize_name_part(raw: str | None) -> str | None:
    """Normalize one name token (first or last name).

    Steps:
    1. Strip leading salutations and trailing suffixes.
    2. Remove diacritics.
    3. Lowercase.
    4. Remove non-alphabetic characters (allow hyphen and apostrophe).
    5. Collapse whitespace.

    Returns ``None`` when the result is empty.
    """
    if is_blank(raw):
        return None
    text = str(raw).strip()
    text = _SALUTATION.sub("", text)
    text = _SUFFIX.sub("", text)
    text = strip_accents(text).lower()
    text = _NON_ALPHA.sub(" ", text)
    text = collapse_spaces(text)
    return text or None


def build_match_name_key(first: str | None, last: str | None) -> str | None:
    """Build the canonical ``first|last`` matching key.

    Both parts are independently normalized.  Returns ``None`` when both
    parts are blank after normalization.
    """
    fn = normalize_name_part(first) or ""
    ln = normalize_name_part(last) or ""
    if not fn and not ln:
        return None
    return f"{fn}{NAME_KEY_SEP}{ln}"


# ── Name splitting ────────────────────────────────────────────────────────────

def split_full_name(raw: str | None) -> tuple[str | None, str | None]:
    """Split a raw full-name string into ``(first, last)``.

    Handles:
    - ``"Last, First"`` (comma-separated, last name first)
    - ``"First Last"``
    - Single token (treated as last name only)
    - Three or more tokens (last token = last name, remainder = first)

    Returns ``(first, last)``; either may be ``None`` if indeterminate.
    """
    if is_blank(raw):
        return None, None
    text = collapse_spaces(str(raw).strip())
    if "," in text:
        parts = [p.strip() for p in text.split(",", 1)]
        last = parts[0] or None
        first = parts[1] if len(parts) > 1 and parts[1] else None
        return first, last
    parts = text.split()
    if len(parts) == 0:
        return None, None
    if len(parts) == 1:
        return None, parts[0]
    if len(parts) == 2:
        return parts[0], parts[1]
    # Three or more tokens: last token is last name
    return " ".join(parts[:-1]), parts[-1]


def build_full_name_clean(first: str | None, last: str | None) -> str | None:
    """Return a cleaned display name (``First Last``); None if both blank."""
    parts = [p.strip() for p in (first or "", last or "") if p.strip()]
    return " ".join(parts) or None


# ── Accompanying-guest splitting ──────────────────────────────────────────────

def split_accompanying_guest_text(raw: str | None) -> list[str]:
    """Split raw accompanying-guest text into individual name strings.

    Handles common delimiters: comma, semicolon, slash, ampersand, ``and``.
    Preserves the original messy segment text — callers decide on QA flags.
    Returns an empty list when the field is blank.
    """
    if is_blank(raw):
        return []
    text = collapse_spaces(str(raw).strip())
    parts = re.split(
        r"\s*(?:,|;|/|&|\band\b)\s*",
        text,
        flags=re.IGNORECASE,
    )
    return [p.strip() for p in parts if p.strip()]


def has_multiple_names_in_field(value: str | None) -> bool:
    """Return True if the field appears to contain more than one person's name."""
    if is_blank(value):
        return False
    segments = split_accompanying_guest_text(value)
    return len(segments) > 1


def classify_name_quality(first: str | None, last: str | None) -> str:
    """Return a simple quality label for a name pair.

    Returns one of: ``"ok"``, ``"last_only"``, ``"first_only"``, ``"both_blank"``.
    """
    has_first = bool(first and first.strip())
    has_last = bool(last and last.strip())
    if has_first and has_last:
        return "ok"
    if has_last:
        return "last_only"
    if has_first:
        return "first_only"
    return "both_blank"
