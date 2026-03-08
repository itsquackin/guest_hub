"""Room XML parser.

Parses coded room XML fields (C9, C15, C18 … C135) into reservation-level
raw records for downstream guest expansion and standardization.

Supported XML structures
------------------------
1. Child elements named after the code::

       <room>
           <C18>RES-001</C18>
           <C21>Smith</C21>
       </room>

2. Generic field elements with an ``id`` attribute::

       <room>
           <Field id="C18">RES-001</Field>
           <Field id="C21">Smith</Field>
       </room>

Both structures are auto-detected per file.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.utils.id_utils import make_source_row_id

logger = logging.getLogger(__name__)

# ── Field code map (locked business rules) ────────────────────────────────────

ROOM_CODE_MAP: dict[str, str] = {
    "C9":   "booked_by_raw",
    "C15":  "booked_on_raw",
    "C18":  "confirmation_number",
    "C21":  "last_name_raw",
    "C24":  "first_name_raw",
    "C27":  "accompanying_guest_raw",
    "C30":  "arrival_raw",
    "C33":  "departure_raw",
    "C36":  "nights_raw",
    "C39":  "rate_code",
    "C45":  "room_type_code",
    "C48":  "nightly_rate_raw",
    "C51":  "company_raw",
    "C54":  "reservation_status_raw",
    "C66":  "specials_raw",
    "C81":  "last_stay_date_raw",
    "C84":  "last_room_raw",
    "C93":  "phone_raw",
    "C129": "vip_status_raw",
    "C135": "assigned_room_type_code",
}


@dataclass(slots=True)
class RoomRawRecord:
    """Raw reservation-level room record extracted from coded XML fields."""
    source_file_name: str
    source_row_id: str
    fields: dict[str, Any]


def _extract_fields_element_strategy(room_el: ET.Element) -> dict[str, str]:
    """Extract fields where child element tags are the C-codes (e.g. <C18>)."""
    fields: dict[str, str] = {}
    for code, canonical in ROOM_CODE_MAP.items():
        child = room_el.find(code)
        if child is not None:
            fields[canonical] = (child.text or "").strip()
    return fields


def _extract_fields_attribute_strategy(room_el: ET.Element) -> dict[str, str]:
    """Extract fields where elements have id="C18" style attributes."""
    # Build lookup: id_value -> element
    id_map: dict[str, ET.Element] = {}
    for child in room_el:
        fid = child.get("id", "").strip()
        if fid:
            id_map[fid] = child
    fields: dict[str, str] = {}
    for code, canonical in ROOM_CODE_MAP.items():
        el = id_map.get(code)
        if el is not None:
            fields[canonical] = (el.text or "").strip()
    return fields


def _detect_strategy(room_el: ET.Element) -> str:
    """Return 'element' or 'attribute' based on the first child element."""
    for child in room_el:
        if child.tag in ROOM_CODE_MAP:
            return "element"
        if child.get("id", "").strip() in ROOM_CODE_MAP:
            return "attribute"
    return "element"  # default


def _parse_room_element(
    room_el: ET.Element,
    strategy: str,
    file_name: str,
    row_index: int,
) -> RoomRawRecord | None:
    """Parse one <room> element into a RoomRawRecord."""
    if strategy == "attribute":
        fields = _extract_fields_attribute_strategy(room_el)
    else:
        fields = _extract_fields_element_strategy(room_el)

    if not fields.get("confirmation_number"):
        logger.warning(
            "Row %d in %s: missing confirmation_number — skipping",
            row_index, file_name,
        )
        return None

    return RoomRawRecord(
        source_file_name=file_name,
        source_row_id=make_source_row_id(file_name, row_index),
        fields=fields,
    )


def parse_room_xml_file(xml_path: Path) -> list[RoomRawRecord]:
    """Parse one room XML file into a list of reservation-level raw records.

    Returns an empty list on parse errors so callers can continue processing
    other files.
    """
    file_name = xml_path.name
    try:
        tree = ET.parse(xml_path)
    except FileNotFoundError as exc:
        logger.error("XML file not found: %s", exc)
        return []
    except ET.ParseError as exc:
        logger.error("XML parse error in %s: %s", file_name, exc)
        return []

    root = tree.getroot()

    # Find all reservation elements — support both <room> and <reservation>
    reservation_tag = None
    for tag in ("room", "reservation", "Reservation", "Room"):
        if root.find(tag) is not None:
            reservation_tag = tag
            break

    if reservation_tag is None:
        # Maybe root IS the reservation
        children = list(root)
        if children and (children[0].tag in ROOM_CODE_MAP or children[0].get("id", "") in ROOM_CODE_MAP):
            reservation_elements = [root]
        else:
            logger.warning("No reservation elements found in %s", file_name)
            return []
    else:
        reservation_elements = root.findall(reservation_tag)

    if not reservation_elements:
        logger.warning("No <%s> elements found in %s", reservation_tag, file_name)
        return []

    # Detect field strategy from the first element
    strategy = _detect_strategy(reservation_elements[0])
    logger.debug("Using '%s' field strategy for %s", strategy, file_name)

    records: list[RoomRawRecord] = []
    for idx, el in enumerate(reservation_elements, start=1):
        record = _parse_room_element(el, strategy, file_name, idx)
        if record is not None:
            records.append(record)

    logger.info(
        "Parsed %d/%d room records from %s",
        len(records), len(reservation_elements), file_name,
    )
    return records
