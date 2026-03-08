"""Rooms standardization transform.

Converts a RoomRawRecord (reservation-level dict of string fields) into
a partially-filled RoomsCanonicalRow with cleaned, typed values.
Guest expansion happens in rooms_expand_guests.py after this step.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from src.cleaners.codes import normalize_code, split_specials_string, parse_nightly_rate, parse_nights
from src.cleaners.dates import parse_date, parse_date_safe
from src.cleaners.names import (
    build_full_name_clean,
    build_match_name_key,
    normalize_name_part,
)
from src.cleaners.nulls import normalize_null
from src.cleaners.phones import normalize_phone, build_match_phone_key
from src.models.canonical_schema import RoomsCanonicalRow
from src.parsers.room_parser import RoomRawRecord
from src.transforms.shared_fields import stamp_row
from src.utils.constants import SOURCE_ROOMS
from src.utils.id_utils import make_stay_span_key

logger = logging.getLogger(__name__)


def _build_stay_window(
    arrival: date | None,
    departure: date | None,
    tolerance_days: int = 1,
) -> tuple[date | None, date | None]:
    """Return (window_start, window_end) applying ±tolerance around stay dates."""
    if arrival is None or departure is None:
        return None, None
    return arrival - timedelta(days=tolerance_days), departure + timedelta(days=tolerance_days)


def standardize_room_record(
    record: RoomRawRecord,
    *,
    load_timestamp: str | None = None,
    date_tolerance_days: int = 1,
) -> RoomsCanonicalRow:
    """Convert one RoomRawRecord into a RoomsCanonicalRow.

    Applies cleaners to all raw string fields and computes derived fields
    (match keys, stay window, specials list).  Guest expansion is NOT
    performed here — call rooms_expand_guests.expand_room_guests() next.
    """
    f = record.fields
    row = RoomsCanonicalRow()

    # Provenance
    stamp_row(
        row,
        source_system=SOURCE_ROOMS,
        source_file_name=record.source_file_name,
        source_row_id=record.source_row_id,
        load_timestamp=load_timestamp,
    )

    # Booking metadata
    row.booked_by_raw = normalize_null(f.get("booked_by_raw"))
    row.confirmation_number = normalize_null(f.get("confirmation_number")) or ""

    arrival_raw = f.get("arrival_raw")
    departure_raw = f.get("departure_raw")
    booked_on_raw = f.get("booked_on_raw")
    last_stay_raw = f.get("last_stay_date_raw")

    arrival_d, a_note = parse_date_safe(arrival_raw, field_name="arrival")
    departure_d, d_note = parse_date_safe(departure_raw, field_name="departure")
    booked_on_d, _ = parse_date_safe(booked_on_raw, field_name="booked_on")
    last_stay_d, _ = parse_date_safe(last_stay_raw, field_name="last_stay_date")

    row.arrival_date = arrival_d
    row.departure_date = departure_d
    row.booked_on_date = booked_on_d
    row.last_stay_date = last_stay_d

    nights_raw = f.get("nights_raw")
    row.nights = parse_nights(nights_raw)

    # Stay window (arrival ± tolerance through departure ± tolerance)
    row.stay_window_start, row.stay_window_end = _build_stay_window(
        arrival_d, departure_d, date_tolerance_days
    )

    # Rate / room
    row.rate_code = normalize_code(f.get("rate_code"))
    row.nightly_rate = parse_nightly_rate(f.get("nightly_rate_raw"))
    row.room_type_code = normalize_code(f.get("room_type_code"))
    row.assigned_room_type_code = normalize_code(f.get("assigned_room_type_code"))

    # Reservation details
    row.company_raw = normalize_null(f.get("company_raw"))
    row.reservation_status_raw = normalize_null(f.get("reservation_status_raw"))
    row.vip_status_raw = normalize_null(f.get("vip_status_raw"))
    row.last_room_raw = normalize_null(f.get("last_room_raw"))
    row.specials_raw = normalize_null(f.get("specials_raw"))
    row.specials_list = split_specials_string(row.specials_raw)

    # Primary guest name (raw values from C21/C24)
    first_raw = normalize_null(f.get("first_name_raw"))
    last_raw = normalize_null(f.get("last_name_raw"))
    row.primary_guest_name_raw = build_full_name_clean(first_raw, last_raw)

    # Phone
    phone_raw = normalize_null(f.get("phone_raw"))
    row.phone_raw = phone_raw
    row.phone_clean = normalize_phone(phone_raw)
    row.match_phone_key = build_match_phone_key(phone_raw)

    # Accompanying guest raw text (for expansion downstream)
    row.accompanying_guest_raw = normalize_null(f.get("accompanying_guest_raw"))

    # QA notes from date parsing
    qa_notes: list[str] = []
    if a_note:
        qa_notes.append(a_note)
    if d_note:
        qa_notes.append(d_note)
    if qa_notes:
        row.qa_notes = "; ".join(qa_notes)
        row.is_valid_record = False

    # Stay span key
    if arrival_d and departure_d:
        row.stay_span_key = make_stay_span_key(
            row.confirmation_number,
            arrival_d.isoformat(),
            departure_d.isoformat(),
        )

    return row
