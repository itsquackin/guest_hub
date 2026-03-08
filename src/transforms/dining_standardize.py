"""Dining standardization transform.

Converts DiningVisitRaw records into DiningCanonicalRow instances with
cleaned, typed fields and computed match keys.
Revenue-style columns have already been stripped by the parser.
"""
from __future__ import annotations

import logging

from src.cleaners.dates import parse_date
from src.cleaners.names import (
    build_full_name_clean,
    build_match_name_key,
    split_full_name,
)
from src.cleaners.nulls import normalize_null
from src.cleaners.phones import build_match_phone_key, normalize_phone
from src.models.canonical_schema import DiningCanonicalRow
from src.parsers.dining_parser import DiningVisitRaw
from src.transforms.shared_fields import stamp_row
from src.utils.constants import SOURCE_DINING

logger = logging.getLogger(__name__)


def _parse_int(val: str | None) -> int | None:
    """Parse a string to int; return None on failure."""
    if not val or not val.strip():
        return None
    try:
        return int(float(val.strip()))
    except (ValueError, OverflowError):
        return None


def standardize_dining_record(
    record: DiningVisitRaw,
    *,
    load_timestamp: str | None = None,
) -> DiningCanonicalRow:
    """Convert one DiningVisitRaw into a DiningCanonicalRow.

    The ``retained`` dict on the raw record uses canonical field names
    (already mapped by the parser using column aliases).
    """
    r = record.retained
    row = DiningCanonicalRow()

    stamp_row(
        row,
        source_system=SOURCE_DINING,
        source_file_name=record.source_file_name,
        source_row_id=record.source_row_id,
        load_timestamp=load_timestamp,
    )

    # Date / time
    visit_date_raw = r.get("visit_date")
    visit_time_raw = r.get("visit_time")
    visit_date = parse_date(visit_date_raw)
    row.visit_date = visit_date
    row.visit_time = normalize_null(visit_time_raw)
    row.activity_date = visit_date  # canonical matching field mirrors visit_date
    row.activity_time = row.visit_time

    if not visit_date and visit_date_raw and visit_date_raw.strip():
        row.is_valid_record = False
        row.qa_issue = "unparseable_date"
        row.qa_notes = f"unparseable_date:visit_date:{visit_date_raw!r}"

    # Guest name — prefer explicit first/last columns; fall back to full-name split
    first = normalize_null(r.get("first_name"))
    last = normalize_null(r.get("last_name"))
    guest_name_raw = normalize_null(r.get("guest_name_raw"))

    if not first and not last and guest_name_raw:
        first, last = split_full_name(guest_name_raw)

    row.guest_name_raw = guest_name_raw or build_full_name_clean(first, last)
    row.first_name = first
    row.last_name = last
    row.full_name_clean = build_full_name_clean(first, last)
    row.match_name_key = build_match_name_key(first, last)

    if not row.match_name_key:
        row.is_valid_record = False
        existing_qa = row.qa_issue or ""
        row.qa_issue = "; ".join(filter(None, [existing_qa, "incomplete_name"]))
        row.qa_notes = "; ".join(filter(None, [
            row.qa_notes,
            f"no_usable_name:{row.guest_name_raw!r}",
        ]))

    # Phone
    phone_raw = normalize_null(r.get("phone_raw"))
    row.phone_raw = phone_raw
    row.phone_clean = normalize_phone(phone_raw)
    row.match_phone_key = build_match_phone_key(phone_raw)

    # Reservation details
    row.party_size = _parse_int(r.get("party_size"))
    row.dining_status = normalize_null(r.get("dining_status"))
    row.table_raw = normalize_null(r.get("table_raw"))
    row.dining_area = normalize_null(r.get("dining_area"))
    row.booking_source = normalize_null(r.get("booking_source"))
    row.server_name = normalize_null(r.get("server_name"))

    # Notes / tags
    row.guest_requests_raw = normalize_null(r.get("guest_requests_raw"))
    row.visit_notes_raw = normalize_null(r.get("visit_notes_raw"))
    row.reservation_tags_raw = normalize_null(r.get("reservation_tags_raw"))
    row.guest_tags_raw = normalize_null(r.get("guest_tags_raw"))

    # Guest history
    row.completed_visits = _parse_int(r.get("completed_visits"))

    return row


def standardize_dining_file(
    records: list[DiningVisitRaw],
    *,
    load_timestamp: str | None = None,
) -> list[DiningCanonicalRow]:
    """Standardize all records from one dining CSV."""
    return [
        standardize_dining_record(r, load_timestamp=load_timestamp)
        for r in records
    ]
