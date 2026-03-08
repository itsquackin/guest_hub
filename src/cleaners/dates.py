"""Date parsing and normalization utilities."""
from __future__ import annotations

from datetime import date, datetime
from typing import Sequence

_DATE_FORMATS: Sequence[str] = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y%m%d",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d-%b-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%m-%d-%Y",
]


def parse_date(raw: str | None) -> date | None:
    """Parse a raw date string using common formats; return a ``date`` or ``None``.

    Tries each known format in order.  Returns ``None`` when the value is blank
    or does not match any supported format.
    """
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def format_iso(d: date | None) -> str | None:
    """Return ISO-8601 date string (``YYYY-MM-DD``) or ``None``."""
    return d.isoformat() if d is not None else None


def parse_date_safe(
    raw: str | None,
    *,
    field_name: str = "",
) -> tuple[date | None, str | None]:
    """Parse a date and return ``(date, qa_note)``.

    *qa_note* is non-None when the value is present but could not be parsed.
    """
    if not raw or not raw.strip():
        return None, None
    d = parse_date(raw)
    if d is None:
        note = (
            f"unparseable_date:{field_name}:{raw!r}"
            if field_name
            else f"unparseable_date:{raw!r}"
        )
        return None, note
    return d, None
