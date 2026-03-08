"""Room XML parser stubs.

Parses coded room XML fields (e.g., C18 confirmation, C30 arrival, C33 departure)
into raw reservation records for downstream guest expansion.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RoomRawRecord:
    """Raw reservation-level room record extracted from coded XML fields."""

    source_file_name: str
    source_row_id: str
    fields: dict[str, Any]


ROOM_CODE_MAP: dict[str, str] = {
    "C9": "booked_by_raw",
    "C15": "booked_on_raw",
    "C18": "confirmation_number",
    "C21": "last_name_raw",
    "C24": "first_name_raw",
    "C27": "accompanying_guest_raw",
    "C30": "arrival_raw",
    "C33": "departure_raw",
    "C36": "nights_raw",
    "C39": "rate_code",
    "C45": "room_type_code",
    "C48": "nightly_rate_raw",
    "C51": "company_raw",
    "C54": "reservation_status_raw",
    "C66": "specials_raw",
    "C81": "last_stay_date_raw",
    "C84": "last_room_raw",
    "C93": "phone_raw",
    "C129": "vip_status_raw",
    "C135": "assigned_room_type_code",
}


def parse_room_xml_file(xml_path: Path) -> list[RoomRawRecord]:
    """Parse one room XML file into reservation-level raw records.

    TODO: implement XML traversal and coded-field extraction.
    """
    _ = xml_path
    return []
