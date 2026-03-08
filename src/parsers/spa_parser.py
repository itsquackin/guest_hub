"""Spa parser stubs for creating canonical spa appointment rows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SpaAppointmentRaw:
    """Raw spa appointment representation before canonical standardization."""

    source_file_name: str
    source_row_id: str
    guest_name_raw: str
    service_date_raw: str
    service_time_raw: str
    service_name_raw: str


def parse_spa_pdf_file(pdf_path: Path) -> list[SpaAppointmentRaw]:
    """Extract appointment-like rows from a spa itinerary PDF.

    TODO: wire this to a concrete PDF extraction backend.
    """
    _ = pdf_path
    return []
