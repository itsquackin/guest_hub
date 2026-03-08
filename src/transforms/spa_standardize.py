"""Spa standardization transform.

Converts SpaAppointmentRaw records into SpaCanonicalRow instances with
cleaned, typed fields and computed match keys.
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict

from src.cleaners.dates import parse_date
from src.cleaners.names import (
    build_full_name_clean,
    build_match_name_key,
    split_full_name,
)
from src.cleaners.nulls import normalize_null
from src.models.canonical_schema import SpaCanonicalRow
from src.parsers.spa_parser import SpaAppointmentRaw
from src.transforms.shared_fields import stamp_row
from src.utils.constants import SOURCE_SPA
from src.utils.hashing import hash_fields

logger = logging.getLogger(__name__)

_DURATION_DIGITS = re.compile(r"(\d+)")

_COUPLES_KEYWORDS = re.compile(
    r"\b(?:couple[s]?|duo|partner|pairs?|two-person)\b", re.IGNORECASE
)

_SERVICE_CATEGORIES = [
    ("massage", "Massage"),
    ("facial", "Facial"),
    ("body", "Body Treatment"),
    ("wrap", "Body Treatment"),
    ("scrub", "Body Treatment"),
    ("manicure", "Nail"),
    ("pedicure", "Nail"),
    ("nail", "Nail"),
    ("hair", "Hair"),
    ("wax", "Waxing"),
    ("hydro", "Hydrotherapy"),
    ("bath", "Hydrotherapy"),
    ("fitness", "Fitness"),
    ("yoga", "Fitness"),
    ("meditation", "Fitness"),
    ("consult", "Consultation"),
    ("assessment", "Consultation"),
]


def _classify_service(service_name: str | None) -> str | None:
    """Assign a broad service category based on the service name."""
    if not service_name:
        return None
    lower = service_name.lower()
    for keyword, category in _SERVICE_CATEGORIES:
        if keyword in lower:
            return category
    return "Other"


def _parse_duration(raw: str | None) -> int | None:
    """Extract duration in minutes from a raw string like '60 mins' or '90'."""
    if not raw:
        return None
    m = _DURATION_DIGITS.search(raw)
    if m:
        return int(m.group(1))
    return None


def standardize_spa_record(
    record: SpaAppointmentRaw,
    *,
    load_timestamp: str | None = None,
) -> SpaCanonicalRow:
    """Convert one SpaAppointmentRaw into a SpaCanonicalRow."""
    row = SpaCanonicalRow()

    stamp_row(
        row,
        source_system=SOURCE_SPA,
        source_file_name=record.source_file_name,
        source_row_id=record.source_row_id,
        load_timestamp=load_timestamp,
    )

    # Guest name
    name_raw = normalize_null(record.guest_name_raw)
    row.guest_name_raw = name_raw
    first, last = split_full_name(name_raw) if name_raw else (None, None)
    row.first_name = first
    row.last_name = last
    row.full_name_clean = build_full_name_clean(first, last)
    row.match_name_key = build_match_name_key(first, last)

    if not row.match_name_key:
        row.is_valid_record = False
        row.qa_issue = "incomplete_name"
        row.qa_notes = f"no_usable_name:{name_raw!r}"

    # Service date/time
    svc_date = parse_date(record.service_date_raw)
    row.service_date = svc_date
    row.service_time = normalize_null(record.service_time_raw)
    # activity_date mirrors service_date for matching consistency
    row.activity_date = svc_date
    row.activity_time = row.service_time

    # Service details
    svc_name = normalize_null(record.service_name_raw)
    row.service_name = svc_name
    row.service_type_raw = svc_name
    row.duration_mins = _parse_duration(record.duration_raw)
    row.service_category = _classify_service(svc_name)
    row.is_couples_service = bool(
        svc_name and _COUPLES_KEYWORDS.search(svc_name)
    )

    if not svc_date:
        row.is_valid_record = False
        issue = "unparseable_date:service_date"
        row.qa_issue = issue
        row.qa_notes = f"{issue}:{record.service_date_raw!r}"

    return row


def compute_spa_guest_aggregates(rows: list[SpaCanonicalRow]) -> list[SpaCanonicalRow]:
    """Compute per-guest aggregate fields across a list of spa canonical rows.

    Mutates rows in place and returns them.  Aggregates:
    - guest_total_spa_appts
    - guest_total_spa_time_mins
    - guest_has_same_day_multi (multiple appts same day)
    - guest_is_multi_day (appts on more than one day)
    - guest_has_any_couples
    """
    # Group by match_name_key
    by_guest: dict[str, list[SpaCanonicalRow]] = defaultdict(list)
    for r in rows:
        key = r.match_name_key or r.guest_name_raw or "__unknown__"
        by_guest[key].append(r)

    for guest_rows in by_guest.values():
        total_appts = len(guest_rows)
        total_mins = sum(r.duration_mins or 0 for r in guest_rows)
        dates = [r.activity_date for r in guest_rows if r.activity_date]
        unique_dates = set(dates)
        has_same_day_multi = len(dates) > len(unique_dates)
        is_multi_day = len(unique_dates) > 1
        has_any_couples = any(r.is_couples_service for r in guest_rows)

        # Build appointment group key per day
        for r in guest_rows:
            r.guest_total_spa_appts = total_appts
            r.guest_total_spa_time_mins = total_mins
            r.guest_has_same_day_multi = has_same_day_multi
            r.guest_is_multi_day = is_multi_day
            r.guest_has_any_couples = has_any_couples
            if r.activity_date:
                r.appointment_group_key = hash_fields(
                    r.match_name_key or "", str(r.activity_date)
                )

    return rows


def standardize_spa_file(
    records: list[SpaAppointmentRaw],
    *,
    load_timestamp: str | None = None,
) -> list[SpaCanonicalRow]:
    """Standardize all records from one spa PDF and compute aggregates."""
    rows = [standardize_spa_record(r, load_timestamp=load_timestamp) for r in records]
    return compute_spa_guest_aggregates(rows)
