"""General text normalization utilities."""
from __future__ import annotations

import re
import unicodedata


def normalize_unicode(text: str) -> str:
    """Normalize unicode to NFC form and remove non-printable control characters."""
    nfc = unicodedata.normalize("NFC", text)
    return "".join(
        ch for ch in nfc
        if unicodedata.category(ch) != "Cc" or ch in "\t\n\r"
    )


def strip_accents(text: str) -> str:
    """Decompose text and remove diacritic marks (accents)."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def collapse_spaces(text: str) -> str:
    """Collapse runs of whitespace into a single space and strip edges."""
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str | None) -> str | None:
    """Apply unicode normalization and whitespace collapsing.

    Returns ``None`` if the input is ``None`` or empty after cleaning.
    """
    if text is None:
        return None
    result = collapse_spaces(normalize_unicode(text))
    return result if result else None


def to_upper(text: str | None) -> str | None:
    """Uppercase and strip text; return None if input is None."""
    return text.upper().strip() if text is not None else None


def to_lower(text: str | None) -> str | None:
    """Lowercase and strip text; return None if input is None."""
    return text.lower().strip() if text is not None else None


def truncate(text: str, max_length: int, suffix: str = "…") -> str:
    """Truncate *text* to *max_length* characters, appending *suffix* if cut."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
