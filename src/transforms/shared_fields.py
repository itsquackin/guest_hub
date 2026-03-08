"""Shared field population utilities.

Adds common provenance and timestamp fields (source_system, source_file_name,
source_row_id, load_timestamp) to any canonical row dataclass.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp_row(
    row: Any,
    *,
    source_system: str,
    source_file_name: str,
    source_row_id: str,
    load_timestamp: str | None = None,
) -> None:
    """Mutate *row* in-place, populating provenance fields.

    Works with any object that has the four provenance attributes.
    The load_timestamp defaults to the current UTC time when not supplied.
    """
    row.source_system = source_system
    row.source_file_name = source_file_name
    row.source_row_id = source_row_id
    row.load_timestamp = load_timestamp or _utc_now_iso()


def make_load_timestamp() -> str:
    """Return a fresh ISO-8601 UTC timestamp string for a pipeline run."""
    return _utc_now_iso()
