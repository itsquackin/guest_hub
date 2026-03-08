"""Guest, phone, and row identifier generation utilities."""
from __future__ import annotations

import uuid


def new_guest_id() -> str:
    """Generate a new unique guest identifier (e.g. ``G-3F9A1B2C4D5E``)."""
    return f"G-{uuid.uuid4().hex[:12].upper()}"


def new_phone_id() -> str:
    """Generate a new unique phone dimension identifier (e.g. ``P-3F9A1B2C4D5E``)."""
    return f"P-{uuid.uuid4().hex[:12].upper()}"


def make_source_row_id(source_file: str, row_index: int) -> str:
    """Build a readable source row identifier.

    Format: ``<file_stem>:<zero_padded_index>``
    Example: ``rooms_export:000042``
    """
    stem = source_file.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return f"{stem}:{row_index:06d}"


def make_reservation_guest_key(confirmation_number: str, sequence: int) -> str:
    """Compound key linking a guest row to its reservation position.

    Format: ``<confirmation_number>#<sequence>``
    """
    return f"{confirmation_number}#{sequence}"


def make_stay_span_key(confirmation_number: str, arrival: str, departure: str) -> str:
    """Compound key for the stay date span of a reservation.

    Format: ``<confirmation_number>@<arrival>/<departure>``
    """
    return f"{confirmation_number}@{arrival}/{departure}"
